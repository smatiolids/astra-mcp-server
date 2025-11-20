# Agentic Astra

Agentic Astra provides a semantic layer to connect AI Agents to Astra DB through MCP. 

It is a powerful solution to translate structured and unstructured data with configurable business logic about how to use it.

Is also includes a UI for tool editing and Agentic Tool Generation

![Astra MCP Server Overview](docs/astra-mcp-server-overview.png)

The agentic-astra that provides tools to interact with Astra DB. It is built with FastMCP and Astrapy (then Astra DB or DataStax HCD can be used as database).

The server will load the tool definitions from a collection in Astra DB or a file. The tool definitions are then transformed to a function definition that can be passed to an LLM, making it possible to use the tools provided by the MCP Server in an Agentic workflow.

When a tool is called, the server will call the appropriate method in Astra DB or DataStax HCD, converting the parameters to the appropriate filters and return the result to the MCP Client/Agent. If some embedding generations is required, the models from OpenAI or IBM Watsonx can be used for similarity search.

## How to run the Astra MCP Server

### Running it as MCP Server with STDIO

To run the agentic-astra as MCP Server with STDIO, you can use the following command:

```bash
uvx agentic-astra --env-file .env --tr http|sse|stdio
# or
uvx agentic-astra --astra_token <astra_token> --astra_db_name <astra_db_name>
```
# Getting Started

You will need a Astra DB database and a Astra DB application token. You can get the token from the Astra DB console.

Also, you will need a collection in Astra DB to store the tool definitions. You can create a collection in Astra DB console.

## Creating Tools

Run agentic-astra-ui to create tools and save them to the Astra DB collection.

```bash
npx agentic-astra-ui --env-file .env
```

Agentic-Astra-UI includes an agent for tool generation. You can use it to generate tools and save them to the Astra DB collection.

Once you have your tool, you are ready to run the MCP Server.

### Running it as MCP Server with HTTP locally

To run the agentic-astra as MCP Server with STDIO, you can use the following command:

```bash
uv run agentic-astra --env-file .env -tr http
```

Copy the .env.example file to .env and fill the variables.

# Local Development

```bash
# Install dependencies
uv sync

# Run the server
uv run agentic-astra --env-file .env --reload --log-level debug
```

# Run from the build version

```bash
# Run the server
uv build
uvx --from ./dist/agentic_astra-0.0.5-py3-none-any.whl agentic-astra --env-file .env -tr http
```

## Using MCP Inspector (STDIO)

```bash
npx @modelcontextprotocol/inspector uv run agentic-astra --log-level debug -tr stdio --env-file .env 
```

