"""
Astra DB Operations

Database operations and utilities for interacting with Astra DB.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
from astrapy import DataAPIClient
from astrapy.data_types import DataAPIVector
from .logger import get_logger
from .utils import remove_underscore_from_dict_keys, extract_db_id_from_astra_url
from .embedding import generate_embedding

# Load environment variables
load_dotenv()

# Initialize logger

@dataclass
class AppContext:
    """Application context containing Astra DB connection."""
    db: Optional[Any] = None  # Database

class AstraDBManager:
    """Manager class for Astra DB operations."""
    logger = get_logger("Astra DB Manager")
    
    def __init__(self, token: str, endpoint: str, db_name: str):
        self.astra_db_token = token
        self.astra_db_api_endpoint = endpoint
        self.astra_db_db_name = db_name
        self.client = None
        self.db = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize Astra DB connection."""
        
        if not self.astra_db_token or (not self.astra_db_db_name and not self.astra_db_api_endpoint):
            self.logger.error("Astra DB credentials not found. Set ASTRA_DB_APPLICATION_TOKEN and ASTRA_DB_API_ENDPOINT or ASTRA_DB_DB_NAME environment variables.")
            return
        
        try:
            self.client = DataAPIClient()
            # to keep compatibility with the old version
            if not self.astra_db_db_name:
                db_list = self.get_dbs()
                if self.astra_db_api_endpoint:
                    catalog_db_id = extract_db_id_from_astra_url(self.astra_db_api_endpoint)
                    catalog_db = next((db for db in db_list if db.id == catalog_db_id), None)    
                    self.astra_db_db_name = catalog_db.name
                else:
                    # If no db name or api endpoint, use the first db
                    self.astra_db_db_name = db_list[0].name
                
            self.logger.debug("available collections: %s", self.get_db_by_name(self.astra_db_db_name).list_collection_names())
            
            self.logger.info("Connected to Astra DB successfully")
        except Exception as e:
            self.logger.error(f"Could not connect to Astra DB: {e}")
    
    def get_db_by_name(self, db_name: str):
        if db_name not in self.db:
            db_list = self.get_dbs()
            self.logger.debug("db_list: %s", db_list)
            new_db = next((db for db in db_list if db.name == db_name), None)
            if not new_db:
                self.logger.error(f"Database {db_name} not found.")
                return
            
            self.logger.debug("new_db: %s", new_db)
            
            self.db[db_name] = self.client.get_database(
                new_db.regions[0].api_endpoint,
                token=self.astra_db_token
            )
            
        return self.db[db_name]
    
    def get_dbs(self) -> [Any]:
        admin_client = self.client.get_admin(token=self.astra_db_token)
        return admin_client.list_databases()

    def get_catalog_content(self, collection_name: str, tags: Optional[str] = None) -> str:
        """Get catalog content from Astra DB collection."""
        db = self.get_db_by_name(self.astra_db_db_name)
        collection =  db.get_collection(collection_name)
        self.logger.info(f"Getting catalog content from {collection_name} with tags: {tags}")
        result = None
        if tags:
            result = collection.find({"type": "tool", "tags": {"$in": tags.split(",")}})
        else:
            result = collection.find({"type": "tool",})
        result = remove_underscore_from_dict_keys(list(result))
        return result
    
    
    def find(
        self,
        arguments: Optional[Dict[str, Any]] = None,
        tool_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Find documents in Astra DB collection.
        """
        try:
            if not tool_config:
                self.logger.error("Tool config not found")
                return json.dumps({"error": "Tool config not found"})
            
            # Where to run the query
            object_type = "collection" if "collection_name" in tool_config else "table"
            object_name = tool_config["collection_name"] if "collection_name" in tool_config else tool_config["table_name"]
            db_name = tool_config["db_name"] if "db_name" in tool_config else self.astra_db_db_name
            
            self.logger.debug(f"Finding documents in '{object_type}' '{object_name}' in database '{db_name}'")
            
            db = self.get_db_by_name(db_name)
            target_object = None

            if object_type == "collection":
                target_object = db.get_collection(object_name)
            else:
                target_object = db.get_table(object_name)
                
            if not target_object:
                self.logger.error(f"{object_type} '{object_name}' not available.")
                return json.dumps({"error": f"{object_type} '{object_name}' not available."})
            
            filter_dict = {}
            search_query = None
            for param in tool_config["parameters"]:
                
                attribute = param["attribute"] if "attribute" in param else param["param"]

                if attribute == "$vector" or attribute == "$vectorize":
                    search_query = arguments[param["param"]]
                    continue

                operator = "$eq"
                if "operator" in param:
                    operator = param["operator"]

                if "value" in param:
                    filter_dict[attribute] = {operator: param["value"]}
                elif param["param"] in arguments:
                    filter_dict[attribute] = {
                        operator: arguments[param["param"]]}
                    
            # Find parameters
            find_params = {}
            
            if filter_dict:
                find_params["filter"] = filter_dict
                
            if tool_config["limit"]:
                find_params["limit"] = tool_config["limit"]
            
            if search_query:
                search_query_config = next((p for p in tool_config["parameters"] if p["param"] == "search_query"), None)
                if "embedding_model" in search_query_config:
                    try:    
                        embedding = generate_embedding(search_query, search_query_config["embedding_model"])
                        find_params["sort"] = {"$vector": DataAPIVector(embedding)}
                    except Exception as e:
                        self.logger.error(f"Failed to generate embedding: {str(e)}")
                        return json.dumps({"error": f"Failed to generate embedding: {str(e)}"})
                elif search_query_config["attribute"] == "$vectorize":
                    find_params["sort"] = {"$vectorize": search_query}
                else:
                    self.logger.error("Search query attribute must be $vectorize or $vector")
                    return json.dumps({"error": "Search query attribute must be $vectorize or $vector"})
            
            elif "sort" in tool_config:
                find_params["sort"] = tool_config["sort"]
            
            if "projection" in tool_config:
                find_params["projection"] = tool_config["projection"]
            
            self.logger.debug("find_params %s", find_params)

            result = target_object.find(**find_params)
            documents = list(result)
            self.logger.info(f"Found {len(documents)} documents in {object_type} '{object_name}'")
            return {
                "success": True,
                "count": len(documents),
                "documents": documents
            }
        except Exception as e:
            self.logger.error(f"Failed to find documents in {object_type} '{object_name}': {str(e)}")
            return json.dumps({"error": f"Failed to find documents: {str(e)}"})

    def list_collections(self = None) -> str:
        """
        List all collections in the Astra DB database.
        """
        self.logger.debug("Listing all collections in Astra DB")
        
        try:
            db = self.get_db_by_name(self.astra_db_db_name)
            collections = db.list_collection_names()
            self.logger.info(f"Found {len(collections)} collections: {collections}")
            return json.dumps({
                "success": True,
                "collections": collections
            })
        except Exception as e:
            self.logger.error(f"Failed to list collections: {str(e)}")
            return json.dumps({"error": f"Failed to list collections: {str(e)}"})
