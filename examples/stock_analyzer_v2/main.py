import asyncio
import os
import sys
import json
import argparse
import structlog
from typing import Any, List, Dict, Optional
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Custom Ops ---

@register_operator("BuildPolygonUrlsOp")
class BuildPolygonUrlsOp(Operator, BaseModel):
    ticker: Input = ""
    key: Input = ""
    details_url: Output = ""
    snapshot_url: Output = ""
    financials_url: Output = ""

    async def run(self, ctx: Any) -> None:
        self.details_url = f"https://api.polygon.io/v3/reference/tickers/{self.ticker}?apiKey={self.key}"
        self.snapshot_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{self.ticker}?apiKey={self.key}"
        self.financials_url = f"https://api.polygon.io/vX/reference/financials?ticker={self.ticker}&limit=1&apiKey={self.key}"

@register_operator("BuildNewsUrlOp")
class BuildNewsUrlOp(Operator, BaseModel):
    ticker: Input = ""
    key: Input = ""
    url: Output = ""

    async def run(self, ctx: Any) -> None:
        self.url = f"https://newsapi.org/v2/everything?pageSize=5&q={self.ticker}&apiKey={self.key}"

@register_operator("BuildFredUrlsOp")
class BuildFredUrlsOp(Operator, BaseModel):
    key: Input = ""
    gdp_url: Output = ""
    cpi_url: Output = ""
    rates_url: Output = ""

    async def run(self, ctx: Any) -> None:
        self.gdp_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={self.key}&file_type=json&limit=1&sort_order=desc"
        self.cpi_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={self.key}&file_type=json&limit=1&sort_order=desc"
        self.rates_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={self.key}&file_type=json&limit=1&sort_order=desc"

@register_operator("PolygonFinancialPrunerOp")
class PolygonFinancialPrunerOp(Operator, BaseModel):
    details: Input = None # str (JSON)
    snapshot: Input = None # str (JSON)
    financials: Input = None # str (JSON)
    summary: Output = ""

    async def run(self, ctx: Any) -> None:
        res = ["Financial Metrics Summary (via Polygon.io):"]
        
        if self.details:
            try:
                data = json.loads(self.details)
                r = data.get("results", {})
                res.append(f"- Name: {r.get('name')}, Sector: {r.get('sic_sector_description')}, Industry: {r.get('sic_description')}")
            except Exception: pass

        if self.snapshot:
            try:
                data = json.loads(self.snapshot)
                t = data.get("ticker", {})
                lt = t.get("lastTrade", {})
                d = t.get("day", {})
                res.append(f"- Current Price: {lt.get('p')}, Volume: {d.get('v')}, Today's Change: {t.get('todaysChange')} ({t.get('todaysChangePerc')}%)")
            except Exception: pass

        if self.financials:
            try:
                data = json.loads(self.financials)
                results = data.get("results", [])
                if results:
                    f = results[0].get("financials", {}).get("income_statement", {})
                    rev = f.get("revenues", {}).get("value")
                    ni = f.get("net_income_loss", {}).get("value")
                    res.append(f"- Latest Revenue: {rev}, Latest Net Income: {ni}")
            except Exception: pass
            
        self.summary = "\n".join(res)

@register_operator("NewsPrunerOp")
class NewsPrunerOp(Operator, BaseModel):
    json_str: Input = ""
    summary: Output = ""

    async def run(self, ctx: Any) -> None:
        try:
            data = json.loads(self.json_str)
            articles = data.get("articles", [])
            res = ["Latest News Headlines:"]
            for art in articles[:5]:
                res.append(f"- {art.get('title')}: {art.get('description')}")
            self.summary = "\n".join(res)
        except Exception:
            self.summary = "News: N/A"

@register_operator("FREDMacroPrunerOp")
class FREDMacroPrunerOp(Operator, BaseModel):
    gdp: Input = None
    cpi: Input = None
    rates: Input = None
    summary: Output = ""

    async def run(self, ctx: Any) -> None:
        def prune(name, raw):
            try:
                data = json.loads(raw)
                obs = data.get("observations", [])
                if obs:
                    return f"{name}: {obs[0].get('value')} (as of {obs[0].get('date')})"
            except Exception: pass
            return f"{name}: N/A"
            
        res = ["Macroeconomic Context:"]
        res.append(f"- {prune('GDP', self.gdp)}")
        res.append(f"- {prune('Inflation (CPI)', self.cpi)}")
        res.append(f"- {prune('Interest Rate (Fed Funds)', self.rates)}")
        self.summary = "\n".join(res)

@register_operator("StockPromptBuilderOp")
class StockPromptBuilderOp(Operator, BaseModel):
    ticker: Input = ""
    financials: Input = ""
    news: Input = ""
    macro: Input = ""
    prompt: Output = ""

    async def run(self, ctx: Any) -> None:
        self.prompt = (
            f"Analyze the following data for stock ticker {self.ticker} and provide a Buy/Hold/Sell recommendation.\n\n"
            f"{self.financials}\n\n"
            f"{self.news}\n\n"
            f"{self.macro}\n\n"
            f"The response must include a concise Buy/Hold/Sell verdict followed by a multi-factor rationale covering growth, valuation, debt, technicals, and macro factors."
        )

# --- Graph ---

def build_graph():
    b = Builder("stock_analyzer_v2")

    b.vertex("ticker_src").op("ContextValOp").params({"key": "ticker"}).output("result", "ticker")

    # Polygon Pipeline
    b.vertex("poly_key").op("EnvOp").params({"name": "POLYGON_API_KEY"}).output("value", "p_key")
    b.vertex("build_poly_urls").op("BuildPolygonUrlsOp") \
        .input("ticker", "ticker").input("key", "p_key") \
        .output("details_url", "p_details_url") \
        .output("snapshot_url", "p_snapshot_url") \
        .output("financials_url", "p_financials_url")
    b.vertex("fetch_poly_details").op("HTTPGetOp").input("url", "p_details_url").output("body", "p_details_json")
    b.vertex("fetch_poly_snapshot").op("HTTPGetOp").input("url", "p_snapshot_url").output("body", "p_snapshot_json")
    b.vertex("fetch_poly_financials").op("HTTPGetOp").input("url", "p_financials_url").output("body", "p_financials_json")

    # NewsAPI Pipeline
    b.vertex("news_key").op("EnvOp").params({"name": "NEWSAPI_API_KEY"}).output("value", "n_key")
    b.vertex("build_news_url").op("BuildNewsUrlOp").input("ticker", "ticker").input("key", "n_key").output("url", "news_url")
    b.vertex("fetch_news").op("HTTPGetOp").input("url", "news_url").output("body", "news_json")

    # FRED Pipeline
    b.vertex("fred_key").op("EnvOp").params({"name": "FRED_API_KEY"}).output("value", "f_key")
    b.vertex("build_fred_urls").op("BuildFredUrlsOp").input("key", "f_key") \
        .output("gdp_url", "gdp_url").output("cpi_url", "cpi_url").output("rates_url", "rates_url")
    b.vertex("fetch_gdp").op("HTTPGetOp").input("url", "gdp_url").output("body", "gdp_json")
    b.vertex("fetch_cpi").op("HTTPGetOp").input("url", "cpi_url").output("body", "cpi_json")
    b.vertex("fetch_rates").op("HTTPGetOp").input("url", "rates_url").output("body", "rates_json")

    # Pruning
    b.vertex("poly_pruner").op("PolygonFinancialPrunerOp") \
        .input("details", "p_details_json").input("snapshot", "p_snapshot_json").input("financials", "p_financials_json") \
        .output("summary", "fin_summary")
    b.vertex("news_pruner").op("NewsPrunerOp").input("json_str", "news_json").output("summary", "news_summary")
    b.vertex("fred_pruner").op("FREDMacroPrunerOp").input("gdp", "gdp_json").input("cpi", "cpi_json").input("rates", "rates_json") \
        .output("summary", "macro_summary")

    # Prompt & Recommendation
    b.vertex("final_prompt").op("StockPromptBuilderOp") \
        .input("ticker", "ticker").input("financials", "fin_summary").input("news", "news_summary").input("macro", "macro_summary") \
        .output("prompt", "stock_prompt")

    b.vertex("recommend").op("AIComputeStringToStringOp").params({
        "model": "gemini-3.5-flash",
        "operation": "Analyze the stock and provide a Buy/Hold/Sell recommendation with rationale.",
    }).input("prompt", "stock_prompt").output("result", "recommendation")

    return b.build()

# --- Execution ---

async def run_workflow(ticker: str, verbose: bool):
    graph = build_graph()
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"ticker": ticker.upper()})
    
    rec, _ = engine.get_output("recommendation")
    return {
        "ticker": ticker.upper(),
        "recommendation": rec
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Comprehensive Stock Analyzer v2.")
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker symbol")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: Neither GEMINI_API_KEY nor GOOGLE_API_KEY found. This example requires Gemini.")
        sys.exit(1)

    print(f"Analyzing stock v2: {args.ticker}...")
    try:
        result = await run_workflow(args.ticker, args.verbose)
        print("\n--- Recommendation ---")
        print(result["recommendation"])
    except Exception as e:
        if args.verbose:
            logger.exception("workflow_failed")
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
