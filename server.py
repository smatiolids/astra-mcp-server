from fastmcp import FastMCP
from load_tools import ToolLoader
from database import AstraDBManager
from dotenv import load_dotenv
from fastmcp.server.dependencies import get_context
from logger import get_logger
from run_tool import RunToolMiddleware
import os,json
load_dotenv(override=True)

# Initialize logger
logger = get_logger("astra_mcp_server",level=os.getenv("LOG_LEVEL"))

def main():
    mcp = FastMCP("Astra MCP Server")
    astra_db_manager = AstraDBManager()
    tools_config = json.load(open("tools_config.json"))
    mcp.add_middleware(RunToolMiddleware(astra_db_manager,tools_config))
    logger.info("Initializing Astra MCP Server")
    logger.info("Starting Astra MCP Server on port 5150")
    tool_loader = ToolLoader(mcp, astra_db_manager,tools_config)
    tool_loader.load_all_tools()
    logger.info("All tools loaded successfully")
    

    return mcp.http_app()

app = main()