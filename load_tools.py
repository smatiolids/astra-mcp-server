from fastmcp.tools import Tool
from fastmcp import FastMCP, Context
from fastmcp.tools import FunctionTool
from fastmcp.tools.tool_transform import ArgTransform, forward_raw
from database import AstraDBManager
from fastmcp.server.dependencies import get_context
from logger import get_logger

# Factory function for creating tool configurations


def create_tool_config(name, description, method, collection_name=None, limit=None, parameters=None, **extra_attrs):
    """
    Factory function to create tool configurations with predefined attributes

    Args:
        name: Tool name
        description: Tool description
        method: Database method to call
        collection_name: Collection name (optional)
        limit: Result limit (optional)
        parameters: List of parameters (optional)
        **extra_attrs: Additional attributes to add to the config

    Returns:
        dict: Tool configuration dictionary
    """
    config = {
        "name": name,
        "description": description,
        "method": method,
    }

    # Add optional attributes if provided
    if collection_name:
        config["collection_name"] = collection_name
    if limit:
        config["limit"] = limit
    if parameters:
        config["parameters"] = parameters

    # Add any extra attributes
    config.update(extra_attrs)

    return config


def create_tool_instance(mcp: FastMCP, astra_db_manager: AstraDBManager, config):
    """
    Factory function to create and configure tool instances

    Args:
        mcp: FastMCP instance
        astra_db_manager: AstraDBManager instance
        config: Tool configuration dictionary

    Returns:
        Tool: Configured tool instance
    """
    method_name = config["method"]

    if not hasattr(astra_db_manager, method_name):
        raise AttributeError(
            f"Method '{method_name}' not found in AstraDBManager")

    method = getattr(astra_db_manager, method_name)
    print(config)
    transform_args = {}
    # transform_args["tools_parameters"] = ArgTransform(hide=True, default=None)
    # transform_args["search_query"] = ArgTransform(
    #     name="search_query", description="Search query", hide=False)

    # Process parameters from configuration
    if "parameters" in config:
        for param in config["parameters"]:
            # Only add tool parameters (not static filters) to transform_args
            if "value" not in param:  # This is a tool parameter, not a static filter
                transform_args[param["param"]] = ArgTransform(
                    description=param.get("description", ""),
                    hide=False
                )

    if method_name == "find_documents":
        # Add the tool name to transform_args so the transform function can identify the config
        transform_args["filter_dict"] = ArgTransform(hide=True)
        transform_args["limit"] = ArgTransform(
            hide=True, default=config.get("limit", None))
        transform_args["sort"] = ArgTransform(hide=True)
        transform_args["projection"] = ArgTransform(
            hide=True, default=config.get("projection", None))
        transform_args["collection_name"] = ArgTransform(
            hide=True, default=config.get("collection_name", None))
        # transform_args["tool_name"] = ArgTransform(hide=True)

    print(transform_args)
    # Create the tool instance
    mcp.add_tool(Tool.from_tool(
        mcp.tool(method),
        name=config["name"],
        description=config["description"],
        transform_args=transform_args,
        transform_fn=transform_fn(config)
    ))

    # return tool

def transform_fn(cfg):
    async def transform_fn_inner(**kwargs):
        print("Transform function called with kwargs:", kwargs)
        return await forward_raw(filter_dict= kwargs.get("filter_dict", None),
                            search_query= kwargs.get("search_query"),
                            limit= cfg.get("limit", None),
                            sort= kwargs.get("sort", None),
                            projection= cfg.get("projection", None),
                            collection_name= cfg["collection_name"])
    return transform_fn_inner

# Tool configurations using factory function
TOOL_CONFIGS = [
    {
        "name": "collections",
        "description": "List all collections in the Astra DB database",
        "parameters": {},
        "method": "list_collections"
    },
    {
        "name": "search_products",
        "description": "Search for products",
        "parameters": [
            {  # Tool parameter
                "param": "search_query",
                "description": "Query to search for products",
                "attribute": "$vectorize",
                "datatype": "string"
            },
            {  # Static Filter
                "param": "in_stock",
                "value": "true",
                "attribute": "in_stock"
            }
        ],
        "method": "find_documents",
        "collection_name": "products",
        "limit": 10,

    },
    {
        "name": "rag",
        "collection": "latam_faq",
        "limit": 10
    }
]


class ToolLoader:
    def __init__(self, mcp: FastMCP, astra_db_manager: AstraDBManager):
        self.mcp = mcp
        self.astra_db_manager = astra_db_manager
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

        # self.tools["rag_search"] = self.mcp.tool(
        create_tool_instance(self.mcp, self.astra_db_manager, TOOL_CONFIGS[1])

        # self.logger.debug("Loading database tools")
        # for cfg in TOOL_CONFIGS:
        #     self.load_dynamic_database_tools(cfg)
        self.logger.debug("Database tools loaded successfully")

    # async def transform_args(self,  **kwargs):
    #     print(kwargs)
    #     return await forward(tools_parameters={"filter_dict": kwargs.get("filter_dict"),
    #                          "limit": kwargs.get("limit"),
    #                                            "sort": kwargs.get("sort"),
    #                                            "projection": kwargs.get("projection"),
    #                                            "collection_name": kwargs.get("collection_name"),
    #                                            "tool_name": kwargs.get("tool_name")})

    # def load_dynamic_database_tools(self, cfg):
    #     """Load a single database tool dynamically using factory function"""
    #     method_name = cfg["method"]
    #     self.logger.debug(f"Loading database tool: {method_name}")

    #     try:
    #         # Use the factory function to create the tool instance
    #         tool = create_tool_instance(self.mcp, self.astra_db_manager, cfg)
    #         self.mcp.add_tool(tool)
    #         self.logger.debug(
    #             f"Database tool '{method_name}' loaded successfully")
    #     except AttributeError as e:
    #         self.logger.error(
    #             f"Method '{method_name}' not found in AstraDBManager")
    #         raise e
