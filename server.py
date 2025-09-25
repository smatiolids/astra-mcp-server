from fastmcp import FastMCP, Context
from mcp.server.lowlevel import NotificationOptions, Server
import mcp.types as types
from load_tools import ToolLoader
from database import AstraDBManager
from dotenv import load_dotenv
from fastmcp.server.dependencies import get_context
from logger import get_logger
load_dotenv(override=True)

# Initialize logger
logger = get_logger("astra_mcp_server")

mcp = FastMCP("Astra MCP Server")
logger.info("Initializing Astra MCP Server")
astra_db_manager = AstraDBManager()


@mcp.server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools with structured output schemas."""
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "temperature": {"type": "number", "description": "Temperature in Celsius"},
                    "condition": {"type": "string", "description": "Weather condition"},
                    "humidity": {"type": "number", "description": "Humidity percentage"},
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["temperature", "condition", "humidity", "city"],
            },
        )
    ]

if __name__ == "__main__":    
    logger.info("Starting Astra MCP Server on port 5150")
    tool_loader = ToolLoader(mcp, astra_db_manager)
    tool_loader.load_all_tools()
    logger.info("All tools loaded successfully")
    mcp.run(transport="sse", port=5150)
