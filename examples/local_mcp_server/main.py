import asyncio
import os
import sys
import json
import argparse
import structlog
import hashlib
from typing import Any, List, Dict, Optional
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
from sparsi.library.mcp_pool import global_mcp_pool
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Custom Ops ---

GOOGLE_SEARCH_BOX_TARGET = 'textarea[name="q"]'
DISMISS_CONSENT_JS = """() => {
    const buttons = document.querySelectorAll('button');
    for (const b of buttons) {
        if (b.innerText.includes('Accept all') || b.innerText.includes('I agree')) {
            b.click();
            return b.innerText;
        }
    }
    return '';
}"""
WAIT_FOR_SEARCH_BOX_JS = """async () => {
    let start = Date.now();
    while (Date.now() - start < 10000) {
        if (document.querySelector('textarea[name="q"]')) return true;
        await new Promise(r => setTimeout(r, 500));
    }
    return false;
}"""
WAIT_FOR_RESULTS_JS = """async () => {
    let start = Date.now();
    while (Date.now() - start < 10000) {
        if (document.querySelector('#search')) return true;
        await new Promise(r => setTimeout(r, 500));
    }
    return false;
}"""
EXTRACT_URLS_JS = """() => {
    const links = Array.from(document.querySelectorAll('a'));
    const urls = [];
    for (const l of links) {
        const href = l.href;
        if (href && href.startsWith('http') && !href.includes('google.com')) {
            if (!urls.includes(href)) {
                urls.push(href);
                if (urls.length >= 3) break;
            }
        }
    }
    return urls;
}"""

@register_operator("MCPGoogleSearchURLsOp")
class MCPGoogleSearchURLsOp(Operator, BaseModel):
    query: Input = ""
    result: Output = []
    
    command: str = "npx"
    args: List[str] = ["-y", "@playwright/mcp@latest"]
    pool_size: int = 1

    async def run(self, ctx: Any) -> None:
        if not self.query:
            return
            
        client = await global_mcp_pool.acquire(
            command=self.command,
            args=self.args,
            pool_size=self.pool_size
        )
        try:
            await client.call_tool("browser_navigate", {"url": "https://www.google.com/?hl=en"})
            await client.call_tool("browser_evaluate", {"function": DISMISS_CONSENT_JS})
            await client.call_tool("browser_evaluate", {"function": WAIT_FOR_SEARCH_BOX_JS})
            await client.call_tool("browser_type", {
                "target": GOOGLE_SEARCH_BOX_TARGET,
                "text": self.query,
                "submit": True
            })
            await client.call_tool("browser_evaluate", {"function": WAIT_FOR_RESULTS_JS})
            res = await client.call_tool("browser_evaluate", {"function": EXTRACT_URLS_JS})
            
            # Extract URLs from the result (res is List[TextContent] or similar)
            text = ""
            if isinstance(res, list):
                for item in res:
                    if hasattr(item, "text"):
                        text += item.text
                    elif isinstance(item, dict):
                        text += item.get("text", "")
            elif isinstance(res, str):
                text = res
                
            if "### Result" in text:
                text = text.split("### Result")[1]
            
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    self.result = json.loads(match.group(0))
                except: pass
            
            if not self.result and "### Ran Playwright code" in text:
                # Fallback: maybe it's just a raw JSON array string
                try:
                    self.result = json.loads(text.split("### Ran Playwright code")[0].strip())
                except: pass
        finally:
            if self.pool_size <= 0:
                await client.disconnect()

@register_operator("MCPScreenshotURLOp")
class MCPScreenshotURLOp(Operator, BaseModel):
    url: Input = ""
    out_dir: str = ""
    result: Output = None # Dict
    
    command: str = "npx"
    args: List[str] = ["-y", "@playwright/mcp@latest"]
    pool_size: int = 8

    async def run(self, ctx: Any) -> None:
        if not self.url:
            return
            
        client = await global_mcp_pool.acquire(
            command=self.command,
            args=self.args,
            pool_size=self.pool_size
        )
        try:
            filename = f"shot-{hashlib.sha1(self.url.encode()).hexdigest()[:16]}.png"
            path = os.path.join(self.out_dir, filename)
            
            error = None
            try:
                await client.call_tool("browser_navigate", {"url": self.url})
                await client.call_tool("browser_take_screenshot", {"filename": path})
            except Exception as e:
                error = str(e)
                
            self.result = {
                "url": self.url,
                "path": path if not error else None,
                "error": error
            }
        finally:
            if self.pool_size <= 0:
                await client.disconnect()

# --- Graph ---

def build_graph(out_dir: str):
    b = Builder("mcp_google_search_screenshot")
    
    b.vertex("search_input").op("ContextValOp").params({"key": "query"}).output("result", "query_wire")
    
    b.vertex("find_urls").op("MCPGoogleSearchURLsOp") \
        .input("query", "query_wire").output("result", "urls_wire")
        
    b.vertex("shoot_each").map_over("urls_wire", "url") \
        .vertex("shoot").op("MCPScreenshotURLOp").params({"out_dir": out_dir}) \
        .input("url", "url").output("result", "shot_result") \
        .collect_into("shot_result", "screenshot_results")
        
    return b.build()

# --- Execution ---

async def run_workflow(query: str, out_dir: str, verbose: bool):
    graph = build_graph(out_dir)
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"query": query})
    
    results, _ = engine.get_output("screenshot_results")
    return results

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Local MCP Server (Playwright) example.")
    parser.add_argument("--query", default="Shizuoka", help="Search query")
    parser.add_argument("--out-dir", help="Absolute path to save screenshots")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    out_dir = args.out_dir
    if not out_dir:
        out_dir = os.path.join(os.getcwd(), ".playwright-mcp")
    
    if not os.path.isabs(out_dir):
        print("Error: --out-dir must be absolute")
        sys.exit(1)
        
    os.makedirs(out_dir, exist_ok=True)

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

    print(f"Running local-mcp-server workflow for: {args.query}...")
    try:
        results = await run_workflow(args.query, out_dir, args.verbose)
        print("\n--- Screenshot Results ---")
        if not results:
            print("No results.")
        else:
            for r in results:
                if not r: continue
                if r.get("error"):
                    print(f"  err {r['url']} : {r['error']}")
                else:
                    print(f"  ok  {r['url']} -> {r['path']}")
    except Exception as e:
        if args.verbose:
            logger.exception("workflow_failed")
        else:
            print(f"Error: {e}")
        sys.exit(1)
    finally:
        from sparsi.library.mcp_pool import global_mcp_pool
        await global_mcp_pool.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
