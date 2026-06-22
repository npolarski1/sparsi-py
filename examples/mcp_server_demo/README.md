# MCP Server Demo

A minimal example showing how to run a Sparsi workflow as a Model Context Protocol (MCP) server.

## Overview

This example uses `run_dual_mode` to expose a simple greeting workflow as both a CLI tool and an MCP tool.

## Usage

### CLI Mode

```bash
python main.py --name Sparsi
```

### MCP Mode

```bash
python main.py --mcp
```

Once running in MCP mode (via stdio), it can be connected to MCP clients like Claude Desktop.
