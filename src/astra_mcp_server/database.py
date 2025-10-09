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
    
    
    def find_documents(
        self,
        search_query: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        sort: Optional[Dict[str, int]] = None,
        projection: Optional[Dict[str, int]] = None,
        collection_name: Optional[str] = None,
        tool_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Find documents in Astra DB collection.
        """        
        self.logger.info(f"Finding documents in collection '{collection_name}' with filter: {filter_dict}, limit: {limit}, search_query: {search_query}")
        
        try:
            db = self.get_db_by_name(tool_config["db_name"] if "db_name" in tool_config else self.astra_db_db_name)
            target_collection = db.get_collection(collection_name)
            if not target_collection:
                self.logger.error(f"Collection '{collection_name}' not available.")
                return json.dumps({"error": "Collection not available."})
            
            find_params = {}
            if filter_dict:
                find_params["filter"] = filter_dict
            if limit:
                find_params["limit"] = limit
            
            if search_query:
                search_query_config = next((p for p in tool_config["parameters"] if p["param"] == "search_query"), None)
                if "embedding_model" in search_query_config:
                    try:    
                        embedding = generate_embedding(search_query, search_query_config["embedding_model"])
                        find_params["sort"] = {"$vector": embedding}
                    except Exception as e:
                        self.logger.error(f"Failed to generate embedding: {str(e)}")
                        return json.dumps({"error": f"Failed to generate embedding: {str(e)}"})
                elif search_query_config["attribute"] == "$vectorize":
                    find_params["sort"] = {"$vectorize": search_query}
                else:
                    self.logger.error("Search query attribute must be $vectorize or $vector")
                    return json.dumps({"error": "Search query attribute must be $vectorize or $vector"})
            elif sort:
                find_params["sort"] = sort
            
            if projection:
                find_params["projection"] = projection
            
            self.logger.debug("find_params %s", find_params)

            result = target_collection.find(**find_params)
            documents = list(result)
            self.logger.info(f"Found {len(documents)} documents in collection '{collection_name}'")
            return json.dumps({
                "success": True,
                "count": len(documents),
                "documents": documents
            }, default=str)
        except Exception as e:
            self.logger.error(f"Failed to find documents in collection '{collection_name}': {str(e)}")
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


    # def insert_document(
    #     self,
    #     tools_parameters: Optional[Dict[str, Any]] = None,
    #     document: Optional[Dict[str, Any]] = None,
    #     collection_name: Optional[str] = None
    # ) -> str:
    #     """
    #     Insert a document into Astra DB collection.
    #     """
    #     # Extract parameters from tools_parameters if provided
    #     if tools_parameters:
    #         document = tools_parameters.get('document', document)
    #         collection_name = tools_parameters.get('collection_name', collection_name)
        
    #     self.logger.debug(f"Inserting document into collection '{collection_name}': {document}")
        
    #     if not self.db:
    #         self.logger.error("Astra DB not available. Check your credentials.")
    #         return json.dumps({"error": "Astra DB not available. Check your credentials."})
    #     try:
    #         target_collection = self.db.get_collection(collection_name)
    #         if not target_collection:
    #             self.logger.error(f"Collection '{collection_name}' not available.")
    #             return json.dumps({"error": "Collection not available."})
    #         result = target_collection.insert_one(document)
    #         self.logger.info(f"Successfully inserted document with ID {result.inserted_id} into collection '{collection_name}'")
    #         return json.dumps({
    #             "success": True,
    #             "inserted_id": str(result.inserted_id),
    #             "document": document
    #         })
    #     except Exception as e:
    #         self.logger.error(f"Failed to insert document into collection '{collection_name}': {str(e)}")
    #         return json.dumps({"error": f"Failed to insert document: {str(e)}"})
    
    # def update_document(
    #     self,
    #     tools_parameters: Optional[Dict[str, Any]] = None,
    #     filter_dict: Optional[Dict[str, Any]] = None,
    #     update_dict: Optional[Dict[str, Any]] = None,
    #     upsert: bool = False,
    #     collection_name: Optional[str] = None
    # ) -> str:
    #     """
    #     Update documents in Astra DB collection.
    #     """
    #     # Extract parameters from tools_parameters if provided
    #     if tools_parameters:
    #         filter_dict = tools_parameters.get('filter_dict', filter_dict)
    #         update_dict = tools_parameters.get('update_dict', update_dict)
    #         upsert = tools_parameters.get('upsert', upsert)
    #         collection_name = tools_parameters.get('collection_name', collection_name)
        
    #     self.logger.debug(f"Updating document in collection '{collection_name}' with filter: {filter_dict}, update: {update_dict}, upsert: {upsert}")
        
    #     if not self.db:
    #         self.logger.error("Astra DB not available. Check your credentials.")
    #         return json.dumps({"error": "Astra DB not available. Check your credentials."})
    #     try:
    #         target_collection = self.db.get_collection(collection_name)
    #         if not target_collection:
    #             self.logger.error(f"Collection '{collection_name}' not available.")
    #             return json.dumps({"error": "Collection not available."})
    #         result = target_collection.update_one(
    #             filter_dict,
    #             update_dict,
    #             upsert=upsert
    #         )
    #         self.logger.info(f"Updated document in collection '{collection_name}': matched={result.matched_count}, modified={result.modified_count}")
    #         return json.dumps({
    #             "success": True,
    #             "matched_count": result.matched_count,
    #             "modified_count": result.modified_count,
    #             "upserted_id": str(result.upserted_id) if hasattr(result, 'upserted_id') and result.upserted_id else None
    #         })
    #     except Exception as e:
    #         self.logger.error(f"Failed to update document in collection '{collection_name}': {str(e)}")
    #         return json.dumps({"error": f"Failed to update document: {str(e)}"})
    
    # def delete_document(
    #     self,
    #     tools_parameters: Optional[Dict[str, Any]] = None,
    #     filter_dict: Optional[Dict[str, Any]] = None,
    #     collection_name: Optional[str] = None
    # ) -> str:
    #     """
    #     Delete documents from Astra DB collection.
    #     """
    #     # Extract parameters from tools_parameters if provided
    #     if tools_parameters:
    #         filter_dict = tools_parameters.get('filter_dict', filter_dict)
    #         collection_name = tools_parameters.get('collection_name', collection_name)
        
    #     self.logger.debug(f"Deleting document from collection '{collection_name}' with filter: {filter_dict}")
        
    #     if not self.db:
    #         self.logger.error("Astra DB not available. Check your credentials.")
    #         return json.dumps({"error": "Astra DB not available. Check your credentials."})
    #     try:
    #         target_collection = self.db.get_collection(collection_name)
    #         if not target_collection:
    #             self.logger.error(f"Collection '{collection_name}' not available.")
    #             return json.dumps({"error": "Collection not available."})
    #         result = target_collection.delete_one(filter_dict)
    #         self.logger.info(f"Deleted {result.deleted_count} document(s) from collection '{collection_name}'")
    #         return json.dumps({
    #             "success": True,
    #             "deleted_count": result.deleted_count
    #         })
    #     except Exception as e:
    #         self.logger.error(f"Failed to delete document from collection '{collection_name}': {str(e)}")
    #         return json.dumps({"error": f"Failed to delete document: {str(e)}"})
    
    
