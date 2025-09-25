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

### Logging Configuration

The project includes a comprehensive logging system with the following features:

#### Log Levels
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical error messages that may prevent the program from running

## Usage

### Starting the Server

```bash
source .venv/bin/activate
uv run server.py
```
