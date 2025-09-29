from fastmcp.tools import Tool
from fastmcp import FastMCP, Context
from fastmcp.tools import FunctionTool
from fastmcp.tools.tool_transform import ArgTransform, forward_raw
from database import AstraDBManager
from fastmcp.server.dependencies import get_context
from logger import get_logger

class ToolLoader:
    def __init__(self, mcp: FastMCP, astra_db_manager: AstraDBManager,tools_config: dict):
        self.mcp = mcp
        self.astra_db_manager = astra_db_manager
        self.tools_config = tools_config
        self.logger = get_logger("tool_loader")
        self.tools = {}

    def load_all_tools(self):
        """Load all tools into the MCP server"""
        self.logger.info("Loading all tools into MCP server")
        self.load_database_tools()
        self.logger.info("All tools loaded successfully")

    def load_database_tools(self):
        """Load all database tools dynamically"""
        self.tools["find_documents"] = self.mcp.tool(
            self.astra_db_manager.find_documents)
        self.tools["list_collections"] = self.mcp.tool(
            self.astra_db_manager.list_collections)
        for tool_config in self.tools_config:
            tool = self.generate_tool(config=tool_config)
            self.mcp.add_tool(tool)

    @staticmethod   
    def generate_tool( config):
        """Generate a tool from a config"""
        
        parameters = {
            "type": "object",
            "required": []
        }
        
        if "parameters" in config:
            parameters["properties"] = {}
            
        for param in config["parameters"]:
            if "value" in param:
                continue
            parameters["properties"][param["param"]] = {
                "type": param["type"],
                "description": param["description"],
            }
            if "required" in param:
                parameters["required"].append(param["param"])


        tool = Tool(
            name=config["name"],
            description=config["description"],
            parameters=parameters,
        )
        return tool

