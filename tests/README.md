# MCP Server Test Suite

This directory contains test scripts for the Astra MCP Server.

## Test Script: `test.py`

### Prerequisites

1. Ensure the Astra MCP Server is properly configured with:
   - Valid Astra DB credentials in `.env` file
   - Required collections exist in your Astra DB instance

### Running the Tests

```bash
# From the project root directory
python -m pytest tests/test_table.py -v
```
