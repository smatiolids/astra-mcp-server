# Astra MCP Server

A Model Context Protocol (MCP) server for interacting with Astra DB (DataStax Astra).

## 1. Set up environment variables (see Configuration section)


Create a `.env` file in the project root with the following variables:

```env
# Astra DB Configuration
ASTRA_DB_APPLICATION_TOKEN=your_astra_db_token
ASTRA_DB_API_ENDPOINT=your_astra_db_endpoint

# Logging Configuration (optional)
LOG_LEVEL=INFO
LOG_FILE=logs/astra_mcp_server.log
```
## Usage

### Quick Start (from GitHub)

```bash
# Run directly from GitHub repository
uvx git+https://github.com/smatiolids/astra-mcp-server.git

# Run with custom settings
uvx git+https://github.com/smatiolids/astra-mcp-server.git --host 127.0.0.1 --port 5150 --reload --log-level debug
```

### Local Development

```bash
# Install dependencies
uv sync

# Run the server
uv run astra-mcp-server --host 127.0.0.1 --port 5150 --reload --log-level debug
```

### Alternative: Direct uvicorn (for development)

```bash
# Run directly with uvicorn
uv run uvicorn server:main --factory --reload --port 5150 --log-level debug
```


## Using MCP Inspector (STDIO)

```bash
npx @modelcontextprotocol/inspector uv run astra-mcp-server --log-level debug -tr stdio
```

# Distribution

```bash
uv pip install --upgrade build
uv pip install --upgrade twine
uv build
uv twine upload dist/*
```