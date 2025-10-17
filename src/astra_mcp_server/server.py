import argparse
import os
import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from .load_tools import ToolLoader
from .database import AstraDBManager
from fastmcp.server.dependencies import get_context
from .logger import get_logger
from .run_tool import RunToolMiddleware
import uvicorn
import asyncio
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier, TokenVerifier
from fastmcp.server.dependencies import get_http_headers
from .utils import load_env_variables

load_dotenv(override=True)

# Initialize logger
logger = get_logger("astra_mcp_server", level=os.getenv("LOG_LEVEL"), log_file=os.getenv("LOG_FILE"))

async def main():
    
    logger.info(f"Starting Astra MCP Server")
    
    # Parse arguments
    parser = argparse.ArgumentParser(conflict_handler="resolve")

    # ---- Uvicorn standard params ----
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Bind socket to this host")
    parser.add_argument("--port", type=int, default=8000,
                        help="Bind socket to this port")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of worker processes")
    parser.add_argument("--log-level", type=str,
                        default="info", help="Logging level")
    parser.add_argument("--log-file", type=str,
                        default="logs.log", help="Logging file")
    parser.add_argument("--transport", "-tr", default="stdio")

    # ---- Astra MCP Server params ----
    parser.add_argument("--astra_token", "-t",
                        default=os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
    parser.add_argument("--astra_endpoint", "-e",
                        default=os.getenv("ASTRA_DB_API_ENDPOINT"))
    parser.add_argument("--astra_db_name", "-db",
                        default=os.getenv("ASTRA_DB_DB_NAME"))
    parser.add_argument("--catalog_file", "-f")
    parser.add_argument("--catalog_collection", "-c",
                        default=os.getenv("ASTRA_DB_CATALOG_COLLECTION") or "tool_catalog")
    parser.add_argument("--tags", "-tags")  # For filtering tools
    parser.add_argument("--auth", "-auth", default=True,
                        action="store_true", help="Disable authentication")
    
    parser.add_argument("--env", "-env", action="append", 
                        help="Environment variables in KEY=VALUE format (can be used multiple times)")

    args = parser.parse_args()
    
    # Load environment variables from command line arguments
    load_env_variables(args.env, logger)    
    logger.error(f"ASTRA_DB_APPLICATION_TOKEN: {os.getenv('ASTRA_DB_APPLICATION_TOKEN')}")
    logger.error(f"ASTRA_DB_APPLICATION_TOKEN arg: {args.astra_token}")
    logger.error(f"Used: {args.astra_token or os.getenv("ASTRA_DB_APPLICATION_TOKEN")}")
    
    astra_db_manager = AstraDBManager(
        token=args.astra_token or os.getenv("ASTRA_DB_APPLICATION_TOKEN"), 
        endpoint=args.astra_endpoint or os.getenv("ASTRA_DB_API_ENDPOINT"), 
        db_name=args.astra_db_name or os.getenv("ASTRA_DB_DB_NAME"))

    # Initialize MCP
    # Configure JWT verifier
    verifier = StaticTokenVerifier(
        tokens={
            os.getenv("ASTRA_MCP_SERVER_TOKEN"): {
                "client_id": "astra-mcp-server",
                "scopes": ["read:data"]
            },
        },
        required_scopes=["read:data"]
    )
    mcp = FastMCP("Astra MCP Server", auth=verifier)


    # Load tools config content
    tools_config_content = None
    if args.catalog_file:
        logger.info(f"Loading tools config from {args.catalog_file}")
        tools_config_content = json.load(open(args.catalog_file))
    else:
        logger.info(
            f"Loading tools Astra collection {args.catalog_collection}")
        tools_config_content = astra_db_manager.get_catalog_content(
            collection_name=args.catalog_collection, tags=args.tags)

    logger.info(f"Tools config content: {tools_config_content}")
    if not tools_config_content or len(tools_config_content) == 0:
        logger.error("No tools found. Load tools to Astra DB collection or reference the catalog file")
        return

    # Add middleware to process tool calling
    mcp.add_middleware(RunToolMiddleware(
        astra_db_manager, tools_config_content))

    logger.info("Initializing Astra MCP Server")
    logger.info(f"Starting Astra MCP Server on port {args.port}")

    # Generate tools based on tools config content
    tool_loader = ToolLoader(mcp, astra_db_manager, tools_config_content)
    tool_loader.load_all_tools()

    logger.info("All tools loaded successfully")

    app = None
    # Return the appropriate transport app
    if args.transport == "http" or args.transport == "sse":
        await mcp.run_async(transport=args.transport, host=args.host, port=args.port, log_level=args.log_level)
    elif args.transport == "stdio":
        await mcp.run_async(transport=args.transport, log_level=args.log_level)
    else:
        raise ValueError(f"Invalid transport: {args.transport}")
    logger.info("Astra MCP Server started successfully")


def run_server():
    """Synchronous entry point for the astra-mcp-server command."""
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
