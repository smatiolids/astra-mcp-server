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

### Starting the Server

```bash
source .venv/bin/activate
uvicorn server:main --reload --port 5150 --log-level debug --factory
```



## Using MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```