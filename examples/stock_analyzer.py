import asyncio
import os
import sys
import json
import argparse
import structlog
import urllib.parse
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Graph ---

def build_graph():
    b = Builder("stock_analyzer")

    # 1. Ticker input
    b.vertex("ticker_src").op("ContextValOp").params({"key": "ticker"}).output("result", "ticker")

    # 2. Build Quote URL
    b.vertex("quote_prefix").op("ConstOp").params({"value": "https://query2.finance.yahoo.com/v8/finance/chart/"}).output("result", "q_pre")
    b.vertex("quote_suffix").op("ConstOp").params({"value": "?interval=1d&range=1d"}).output("result", "q_suf")
    b.vertex("q_join_1").op("StringConcatOp").input("a", "q_pre").input("b", "ticker").output("result", "q_mid")
    b.vertex("quote_url").op("StringConcatOp").input("a", "q_mid").input("b", "q_suf").output("result", "quote_url")

    # 3. Build News URL
    b.vertex("news_prefix").op("ConstOp").params({"value": "https://query2.finance.yahoo.com/v1/finance/search?q="}).output("result", "n_pre")
    b.vertex("news_suffix").op("ConstOp").params({"value": "&quotesCount=0&newsCount=1"}).output("result", "n_suf")
    b.vertex("n_join_1").op("StringConcatOp").input("a", "n_pre").input("b", "ticker").output("result", "n_mid")
    b.vertex("news_url").op("StringConcatOp").input("a", "n_mid").input("b", "n_suf").output("result", "news_url")

    # 4. Fetch data in parallel
    b.vertex("fetch_quote").op("HTTPGetOp").input("url", "quote_url").output("body", "quote_json")
    b.vertex("fetch_news").op("HTTPGetOp").input("url", "news_url").output("body", "news_json")

    # 5. Extract fields
    b.vertex("path_price").op("ConstOp").params({"value": "chart.result.0.meta.regularMarketPrice"}).output("result", "p_path")
    b.vertex("extract_price").op("JSONExtractOp").input("json_str", "quote_json").input("path", "p_path").output("result", "price_raw")

    b.vertex("path_prev").op("ConstOp").params({"value": "chart.result.0.meta.chartPreviousClose"}).output("result", "pc_path")
    b.vertex("extract_prev").op("JSONExtractOp").input("json_str", "quote_json").input("path", "pc_path").output("result", "prev_raw")

    b.vertex("path_news").op("ConstOp").params({"value": "news.0.title"}).output("result", "n_path")
    b.vertex("extract_news").op("JSONExtractOp").input("json_str", "news_json").input("path", "n_path").output("result", "headline")

    # 6. Parse numbers
    b.vertex("parse_price").op("AIParseNumberOp").input("input", "price_raw").output("result", "price")
    b.vertex("parse_prev").op("AIParseNumberOp").input("input", "prev_raw").output("result", "prev_close")

    # 7. Math
    b.vertex("calc_change").op("SubFloatOp").input("a", "price").input("b", "prev_close").output("result", "change")

    # 8. AI Sentiment
    b.vertex("sentiment").op("AIScoreOp").params({
        "criterion": "The headline indicates a positive/bullish outlook for the company",
    }).input("input", "headline").output("result", "sentiment_score")

    # 9. Convert to String for prompt
    b.vertex("sentiment_str").op("FloatToStringOp").input("val", "sentiment_score").output("result", "sentiment_txt")
    b.vertex("change_str").op("FloatToStringOp").input("val", "change").output("result", "change_txt")

    # 10. Build final prompt
    b.vertex("p_header").op("ConstOp").params({"value": "Analysis for stock ticker: "}).output("result", "ph")
    b.vertex("p_price").op("ConstOp").params({"value": "\nCurrent Price: "}).output("result", "pp")
    b.vertex("p_change").op("ConstOp").params({"value": "\nPrice Change: "}).output("result", "pc")
    b.vertex("p_headline").op("ConstOp").params({"value": "\nLatest Headline: "}).output("result", "phl")
    b.vertex("p_sentiment").op("ConstOp").params({"value": "\nSentiment (0-1): "}).output("result", "ps")
    b.vertex("p_footer").op("ConstOp").params({"value": "\n\nProvide Buy/Hold/Sell rec."}).output("result", "pf")

    b.vertex("c1").op("StringConcatOp").input("a", "ph").input("b", "ticker").output("result", "s1")
    b.vertex("c2").op("StringConcatOp").input("a", "s1").input("b", "pp").output("result", "s2")
    b.vertex("c3").op("StringConcatOp").input("a", "s2").input("b", "price_raw").output("result", "s3")
    b.vertex("c4").op("StringConcatOp").input("a", "s3").input("b", "pc").output("result", "s4")
    b.vertex("c5").op("StringConcatOp").input("a", "s4").input("b", "change_txt").output("result", "s5")
    b.vertex("c6").op("StringConcatOp").input("a", "s5").input("b", "phl").output("result", "s6")
    b.vertex("c7").op("StringConcatOp").input("a", "s6").input("b", "headline").output("result", "s7")
    b.vertex("c8").op("StringConcatOp").input("a", "s7").input("b", "ps").output("result", "s8")
    b.vertex("c9").op("StringConcatOp").input("a", "s8").input("b", "sentiment_txt").output("result", "s9")
    b.vertex("c10").op("StringConcatOp").input("a", "s9").input("b", "pf").output("result", "final_prompt")

    # 11. Final Rec
    b.vertex("recommend").op("AIComputeStringToStringOp").params({
        "operation": "Analyze the given stock data and sentiment to provide a Buy/Hold/Sell recommendation.",
    }).input("prompt", "final_prompt").output("result", "recommendation")

    return b.build()

# --- Execution ---

async def run_workflow(ticker: str):
    graph = build_graph()
    engine = Engine(graph, reporter=Reporter())
    
    await engine.run({"ticker": ticker.upper()})
    
    rec, _ = engine.get_output("recommendation")
    return {
        "ticker": ticker.upper(),
        "recommendation": rec
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Stock analyzer.")
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker symbol")
    
    args = parser.parse_args()
    
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]
    )

    print(f"Analyzing stock: {args.ticker}...")
    try:
        result = await run_workflow(args.ticker)
        print("\n--- Recommendation ---")
        print(result["recommendation"])
    except Exception as e:
        logger.error("workflow_failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
