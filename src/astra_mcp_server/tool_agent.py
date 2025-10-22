#!/usr/bin/env python3
"""
Tool Specification Generator for Astra DB Tables

This program connects to Astra DB, retrieves table schema and sample data,
and generates a tool specification in the format compatible with tool_config.json.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pydantic_core.core_schema import none_schema
from astrapy.info import TableIndexType
# Add the parent directory to the path to import astra_mcp_server modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from astra_mcp_server.database import AstraDBManager
from astra_mcp_server.logger import get_logger
from astra_mcp_server.llm import run_prompt
from astra_mcp_server.tool_agent_prompt import prompt as tool_agent_prompt

# Load environment variables
load_dotenv()

logger = get_logger("Tool Spec Generator", stdout=True)

def export_prompt(file_path: str) -> str:
    prompt = tool_agent_prompt
    with open(file_path, "w") as f:
        f.write(prompt)
    logger.info(f"Prompt exported to {file_path}")
class AstraToolAgent:
    
    db_manager = None
    db = None
    table = None
    collection = None
    table_name = None
    collection_name = None
    keyspace_name = None
    metadata = {}
    def __init__(self, astra_db_token: str, astra_db_name: str, table_name: str = None, collection_name: str = None, keyspace_name: str = "default_keyspace") -> Optional[Dict[str, Any]]:
        """Initialize the tool agent."""
        self.db_manager =  AstraDBManager(token=astra_db_token, db_name=astra_db_name)
        self.db = self.db_manager.get_db_by_name(astra_db_name)
        self.keyspace_name = keyspace_name
        if table_name:
            self.table_name = table_name
            self.table = self.db.get_table(self.table_name)
            

            
    def get_indexed_columns(self, table_indexes: List[Dict[str, Any]], index_type: TableIndexType = TableIndexType.REGULAR) -> List[str]:
        indexed_columns = []
        for index in table_indexes:
            if index.index_type == index_type:
                indexed_columns.append(index.definition.column)
        return indexed_columns

    def get_table_schema(self) -> Optional[Dict[str, Any]]:
        """Get table schema information from Astra DB."""
        tables = self.db.list_tables()        
        table_metadata = next((table for table in tables if table.name == self.table_name), None)
        table_indexes = self.table.list_indexes()
        
        
        metadata = {
            "table_name": self.table_name,
            "keyspace_name": self.keyspace_name,
            "columns": table_metadata.raw_descriptor["definition"]["columns"],
            "primary_key": table_metadata.raw_descriptor["definition"]["primaryKey"],
            "partition_key": table_metadata.raw_descriptor["definition"]["primaryKey"]["partitionBy"],
            "partition_sort": table_metadata.raw_descriptor["definition"]["primaryKey"]["partitionSort"],
            "indexed_columns": self.get_indexed_columns(table_indexes, TableIndexType.REGULAR),
            "vector_columns": self.get_indexed_columns(table_indexes, TableIndexType.VECTOR),
            "text_columns": self.get_indexed_columns(table_indexes, TableIndexType.TEXT)
        }
        logger.info(f"Table metadata: {metadata}")
        
        logger.info(f"Retrieved schema for table '{self.table_name}': {metadata}")
        return metadata
        
    def get_sample_records(self, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Get sample records from the table."""
        try:
            # Get first few records
            result = self.table.find(limit=limit)
            records = list(result)
            logger.info(f"Retrieved {len(records)} sample records from table '{self.table.name}'")
            return records
            
        except Exception as e:
            logger.error(f"Failed to get sample records from table '{self.table.name}': {str(e)}")
            return None

    def load_prompt_template(self, prompt_file: str = None) -> str:
        """Load the prompt template from the markdown file."""
        if prompt_file:
            prompt_file_path = prompt_file
        else:
            prompt_file_path = os.path.join(os.path.dirname(__file__), "tool_specification_prompt.md")
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template file not found: {prompt_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading prompt template file: {e}")
            raise

    def generate_tool_specification(self, sample_size: int = 5, additional_instructions: str = "", prompt_file: str = None) -> Dict[str, Any]:
        """Generate tool specification based on table schema and sample data."""
        self.metadata = self.get_table_schema()
        sample_records = self.get_sample_records(limit=sample_size)
        
        # Load prompt template from markdown file and format with variables
        prompt_template = ""
        if prompt_file:
            prompt_template = self.load_prompt_template(prompt_file)
        else:
            prompt_template = tool_agent_prompt
        
        if prompt_template == "":
            logger.error("No prompt template found")
            raise ValueError("No prompt template found")
            
        prompt = prompt_template.format(
            metadata=self.metadata,
            sample_records=sample_records,
            additional_instructions=additional_instructions
        )
        response = run_prompt(prompt)
        content = response["choices"][0]["message"]["content"]
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {content}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def save_tool_to_file(self, tool_spec: Dict[str, Any], file_path: str) -> None:
        """Save tool specification to a file."""
        with open(file_path, 'w') as f:
            json.dump(tool_spec, f, indent=2)
        logger.info(f"Tool specification written to '{file_path}'")

def main():
    """Main function to parse arguments and generate tool specification."""
    parser = argparse.ArgumentParser(
        description="Generate tool specification for Astra DB table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
python generate_tool_spec.py --table-name users --db-name mydb --out-file user_tool.json
python generate_tool_spec.py -t products -d ecommerce -o product_tool.json
        """
    )

    parser.add_argument(
        "--export-prompt", "-ep",
        required=False,
        help="Export the prompt used to generate the tool specification"
    )
    
    parser.add_argument(
        "--table-name", "-t",
        required=False,
        help="Name of the table to analyze"
    )
    
    parser.add_argument(
        "--collection-name", "-c",
        required=False,
        help="Name of the collection to analyze"
    )
    
    parser.add_argument(
        "--keyspace-name", "-k",
        required=False,
        default="default_keyspace",
        help="Name of the keyspace to analyze"
    )
    
    parser.add_argument(
        "--db-name", "-d", 
        required=False,
        help="Name of the database containing the table"
    )
    
    parser.add_argument(
        "--out-file", "-o",
        required=False,
        help="Output file path for the generated tool specification JSON"
    )
    
    parser.add_argument(
        "--sample-size", "-s",
        type=int,
        default=5,
        help="Number of sample records to analyze (default: 5)"
    )
    
    parser.add_argument(
        "--prompt-file", "-pf",
        required=False,
        help="Prompt file to use for the tool specification generation"
    )
    
    parser.add_argument(
        "--additional-instructions", "-ai",
        required=False,
        help="Additional instructions for the tool specification generation"
    )
    
    args = parser.parse_args()
    
    if args.export_prompt:
        export_prompt(args.export_prompt)
        sys.exit(0)
        
    if (args.table_name and args.collection_name):
        logger.error("Either --table-name or --collection-name must be provided")
        sys.exit(1)
    
    if (not args.out_file):
        logger.error("--out-file is required")
        sys.exit(1)
 
    token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    db_name = os.getenv("ASTRA_DB_DB_NAME")
    tool_agent = AstraToolAgent(token, db_name, args.table_name, args.keyspace_name)
    tool_spec = tool_agent.generate_tool_specification(args.sample_size, args.additional_instructions, args.prompt_file)
    if args.out_file:
        tool_agent.save_tool_to_file(tool_spec, args.out_file)
        logger.info(f"Tool specification written to '{args.out_file}'")
    else:
        logger.info("Tool specification:")
        logger.info(json.dumps(tool_spec, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
