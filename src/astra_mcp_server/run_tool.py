from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from .logger import get_logger
import mcp.types as types
import json
from .database import AstraDBManager
import os
from datetime import datetime # for datetime eval expressions that can be used in the tool config
import uuid

class AuditStatus:
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"

class RunToolMiddleware(Middleware):
    
    logger = get_logger("RunToolMiddleware")

    def __init__(self, astra_db_manager: AstraDBManager, tools_config: dict):
        self.astra_db_manager = astra_db_manager
        self.tools_config = tools_config

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Access the tool object to check its metadata
        if not context.fastmcp_context:
            ToolError("No context found")

        tool_name = context.message.name
        run_id = uuid.uuid1() # Use UUID1 for timestamp based UUID
        start_timestamp = datetime.now().isoformat()
        
        self.logger.info(f"Run ID: {run_id}")
        self.logger.info(f"Start timestamp: {start_timestamp}")
        self.logger.info(f"Context: {context}")
        self.astra_db_manager.log_audit(tool_id=tool_name, 
                                       client_id=context.fastmcp_context.client_id, 
                                       run_id=run_id, 
                                       start_timestamp=start_timestamp,
                                       status=AuditStatus.STARTED)
        
        try:
            arguments = context.message.arguments
            self.logger.debug(f"Arguments: {arguments}")
            self.astra_db_manager.log_audit(tool_id=tool_name, 
                                       run_id=run_id, 
                                       parameters= json.dumps(arguments),
                                       status=AuditStatus.STARTED)
        except Exception as e:
            self.logger.error(f"Error getting arguments: {e}")
            self.astra_db_manager.log_audit(tool_id=tool_name, 
                                       run_id=run_id, 
                                       end_timestamp=datetime.now().isoformat(),
                                       status=AuditStatus.FAILED,
                                       status_code=500,
                                       status_message=f"Error getting arguments: {e}",
                                       status_details=str(e),
                                       error=str(e))
            return ToolResult({"error": f"Error getting arguments: {e}"})

        tool_config = next(
            (t for t in self.tools_config if t['name'] == tool_name), None)

        if not tool_config:
            ToolError(f"Tool {tool_name} not found")
        else:
            self.logger.debug(f"Tool config: {tool_config}")

        # Check arguments            
        for param in tool_config["parameters"]:
            if param["param"] not in arguments and param.get("required", False) == True:
                self.logger.error(f"Parameter {param['param']} is required")
                return ToolResult({"error": f"Parameter {param['param']} is required"})

        # Run methods
        if tool_config["method"] == "find" or tool_config["method"] == "find_documents":
            result = self.astra_db_manager.find(
                arguments=arguments,
                tool_config=tool_config)

            self.logger.debug(f"Result: {result}")
            self.astra_db_manager.log_audit(tool_id=tool_name, 
                                       run_id=run_id, 
                                       end_timestamp=datetime.now().isoformat(),
                                       status=AuditStatus.COMPLETED,
                                       status_code=200)
            return ToolResult(structured_content=result)

        if tool_config["method"] == "list_collections":
            result = self.astra_db_manager.list_collections()
            self.logger.debug(f"Result: {result}")
            return ToolResult(structured_content=result)
        
        # Method not implemented
        ToolError(f"Method {tool_config['method']} not allowed")
