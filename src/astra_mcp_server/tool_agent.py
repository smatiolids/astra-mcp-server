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

# Load environment variables
load_dotenv()

logger = get_logger("Tool Spec Generator")

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
        print(metadata)
        
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

    def generate_tool_specification(self, sample_size: int = 5, additional_instructions: str = "") -> Dict[str, Any]:
        """Generate tool specification based on table schema and sample data."""
        self.metadata = self.get_table_schema()
        sample_records = self.get_sample_records(limit=sample_size)
        
        
        prompt = f'''
        You are a tool specification generator. You are given a table schema and sample data.
        You need to generate a tool specification for the table.
        The tool specification should be in the format of a JSON object.
        While generate descriptions, define it in a way to make it easier for LLM to understand it.
        Use the sample data to identify data types, patterns and enums.

        
        IMPORTANT: Consider ONLY the partition keys, sorting keys and indexed columns as parameteres.
        IMPORTANT: Partition keys are mandatory parameters.
        IMPORTANT: For indexed date time or timestamps parameters, generate start_<column_name> and end_<column_name> parameters. use $gt and $lte operators.
        IMPORTANT: For indexed numeric parameters, generate min_<column_name> and max_<column_name> parameters. use $gte and $lte operators.
        IMPORTANT: Return ONLY valid JSON without any markdown formatting, code blocks, or additional text.
        IMPORTANT: If the column is a vector column, generate the embedding_model as text-embedding-3-small.
        
        The table schema is: {self.metadata}
        
        The sample data is: {sample_records}

        Additional instructions: {additional_instructions}

        
        Generate the tool specification in the following format:
        {{
            "tags": [<main topics of the data>],
            "type": "tool",
            "name": <name of the tool - String>,
            "description": <description of the tool - String>,
            "projection": < relevant fields to return. avoid codes, and technical fields like _id, _createdAt, _updatedAt, _deletedAt, etc. E.g: {{"column_name": 1, "column_name2": 1, "column_name3": 1}} | type: Object | default: {{}}>,
            "parameters": [
                {{
                    "param": <name of the parameter - String | type: String >
                    "description": <instruction to the LLM about how to use the parameter - String>,
                    "attribute": <name of the column in the table | type: String | default: $vectorize | If it is equal to the param, do not fill this field>
                    "type": <type of the parameter according to the attribute>,
                    "required": <required parameter. If the attribute is partition key, it is mandatory | type: Boolean | default: False>,
                    "operator": < The operator to use to filter the parameter - if not filled, the operator is $eq | type: String | default: $eq | If the attribute is not a vector column, do not fill this field>,
                    "enum": <enum of the parameter - Array of Strings | If no enum detected, do not fill this field>,
                    "embedding_model": <embedding model of the parameter - String | If no embedding model detected, do not fill this field>,
                    "expr": <if theres a expression for the parameters, like filter conditions, add it here. Use python basic operations or datetime operations | type: String | default: None | If unknown, do not fill this field>,
                    "value": <if theres a static value for the parameters, like filter conditions, add it here | type: Any | default: None | If unknown, do not fill this field>,
                    "info": <inform if the attribute is part of partitionk key, sorting key, indexed column or vector column | type: String | default: "">
                }},
            ],
            "method": "find",
            "table_name": <table name of the tool>,
            "db_name": <db name of the tool>,
            "limit": <limit of the tool | Default: 10>
        }}
        '''
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
        required=True,
        help="Name of the database containing the table"
    )
    
    parser.add_argument(
        "--out-file", "-o",
        required=True,
        help="Output file path for the generated tool specification JSON"
    )
    
    parser.add_argument(
        "--sample-size", "-s",
        type=int,
        default=5,
        help="Number of sample records to analyze (default: 5)"
    )
    
    parser.add_argument(
        "--additional-instructions", "-ai",
        required=False,
        help="Additional instructions for the tool specification generation"
    )
    
    args = parser.parse_args()
    
    if (args.table_name and args.collection_name):
        logger.error("Either --table-name or --collection-name must be provided")
        sys.exit(1)
    
    token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    db_name = os.getenv("ASTRA_DB_DB_NAME")
    tool_agent = AstraToolAgent(token, db_name, args.table_name, args.keyspace_name)
    tool_spec = tool_agent.generate_tool_specification(args.sample_size, args.additional_instructions)
    if args.out_file:
        tool_agent.save_tool_to_file(tool_spec, args.out_file)
        logger.info(f"Tool specification written to '{args.out_file}'")
    else:
        print("Tool specification:")
        print(json.dumps(tool_spec, indent=2))
        logger.info("Tool specification:")
        logger.info(json.dumps(tool_spec, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
