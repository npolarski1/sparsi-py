from dagor import Builder
from sparsi import run_dual_mode
import dagor.builtin
import sparsi.library

def build_graph():
    b = Builder("hello_mcp")
    b.vertex("in").op("ContextValOp").params({"key": "name"}).output("result", "name_wire")
    b.vertex("greet").op("StringConcatOp").params({"a": "Hello, "}).input("b", "name_wire").output("result", "final_result")
    return b

if __name__ == "__main__":
    # This workflow can be run as:
    # CLI: python examples/mcp_server_demo.py --name Sparsi
    # MCP: python examples/mcp_server_demo.py --mcp
    run_dual_mode("hello_tool", build_graph, {"name": "name"})
