"""
Astra DB Operations

Database operations and utilities for interacting with Astra DB.
"""

import os
import asyncio
import json
from fastmcp import Context
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
from astrapy import DataAPIClient
from logger import get_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger("astra_db")

@dataclass
class AppContext:
    """Application context containing Astra DB connection."""
    db: Optional[Any] = None  # Database

class AstraDBManager:
    """Manager class for Astra DB operations."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize Astra DB connection."""
        astra_db_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        astra_db_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        
        if not astra_db_token or not astra_db_api_endpoint:
            logger.error("Astra DB credentials not found. Set ASTRA_DB_APPLICATION_TOKEN and ASTRA_DB_API_ENDPOINT environment variables.")
            return
        
        try:
            self.client = DataAPIClient()
            self.db = self.client.get_database(
                astra_db_api_endpoint,
                token=astra_db_token
            )
            logger.debug("available collections: %s", self.db.list_collection_names())
            
            logger.info("Connected to Astra DB successfully")
        except Exception as e:
            logger.error(f"Could not connect to Astra DB: {e}")
    
    def get_dbs(self) -> str:
        admin_client = self.client.get_admin(token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
        db_list = admin_client.list_databases()
        return json.dumps({
            "success": True,
            "dbs": db_list
        })
    
    async def find_documents(
        self,
        search_query: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        sort: Optional[Dict[str, int]] = None,
        projection: Optional[Dict[str, int]] = None,
        collection_name: Optional[str] = None,
    ) -> str:
        """
        Find documents in Astra DB collection.
        """
        
        # collection_name = tools_parameters["collection_name"]
        # filter_dict = tools_parameters["filter_dict"]
        # limit = tools_parameters["limit"]
        # sort = tools_parameters["sort"]
        # projection = tools_parameters["projection"]
        
        logger.info(f"Finding documents in collection '{collection_name}' with filter: {filter_dict}, limit: {limit}")
        
        if not self.db:
            logger.error("Astra DB not available. Check your credentials.")
            return json.dumps({"error": "Astra DB not available. Check your credentials."})
        try:
            target_collection = self.db.get_collection(collection_name)
            if not target_collection:
                logger.error(f"Collection '{collection_name}' not available.")
                return json.dumps({"error": "Collection not available."})
            
            find_params = {}
            if filter_dict:
                find_params["filter"] = filter_dict
            if limit:
                find_params["limit"] = limit
            
            if search_query:
                find_params["sort"] = {"$vectorize": search_query}
            elif sort:
                find_params["sort"] = sort
            
            if projection:
                find_params["projection"] = projection
            
            logger.info("find_params %s", find_params)

            result = target_collection.find(**find_params)
            documents = list(result)
            logger.info(f"Found {len(documents)} documents in collection '{collection_name}'")
            return json.dumps({
                "success": True,
                "count": len(documents),
                "documents": documents
            }, default=str)
        except Exception as e:
            logger.error(f"Failed to find documents in collection '{collection_name}': {str(e)}")
            return json.dumps({"error": f"Failed to find documents: {str(e)}"})
    
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
        
    #     logger.debug(f"Inserting document into collection '{collection_name}': {document}")
        
    #     if not self.db:
    #         logger.error("Astra DB not available. Check your credentials.")
    #         return json.dumps({"error": "Astra DB not available. Check your credentials."})
    #     try:
    #         target_collection = self.db.get_collection(collection_name)
    #         if not target_collection:
    #             logger.error(f"Collection '{collection_name}' not available.")
    #             return json.dumps({"error": "Collection not available."})
    #         result = target_collection.insert_one(document)
    #         logger.info(f"Successfully inserted document with ID {result.inserted_id} into collection '{collection_name}'")
    #         return json.dumps({
    #             "success": True,
    #             "inserted_id": str(result.inserted_id),
    #             "document": document
    #         })
    #     except Exception as e:
    #         logger.error(f"Failed to insert document into collection '{collection_name}': {str(e)}")
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
        
    #     logger.debug(f"Updating document in collection '{collection_name}' with filter: {filter_dict}, update: {update_dict}, upsert: {upsert}")
        
    #     if not self.db:
    #         logger.error("Astra DB not available. Check your credentials.")
    #         return json.dumps({"error": "Astra DB not available. Check your credentials."})
    #     try:
    #         target_collection = self.db.get_collection(collection_name)
    #         if not target_collection:
    #             logger.error(f"Collection '{collection_name}' not available.")
    #             return json.dumps({"error": "Collection not available."})
    #         result = target_collection.update_one(
    #             filter_dict,
    #             update_dict,
    #             upsert=upsert
    #         )
    #         logger.info(f"Updated document in collection '{collection_name}': matched={result.matched_count}, modified={result.modified_count}")
    #         return json.dumps({
    #             "success": True,
    #             "matched_count": result.matched_count,
    #             "modified_count": result.modified_count,
    #             "upserted_id": str(result.upserted_id) if hasattr(result, 'upserted_id') and result.upserted_id else None
    #         })
    #     except Exception as e:
    #         logger.error(f"Failed to update document in collection '{collection_name}': {str(e)}")
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
        
    #     logger.debug(f"Deleting document from collection '{collection_name}' with filter: {filter_dict}")
        
    #     if not self.db:
    #         logger.error("Astra DB not available. Check your credentials.")
    #         return json.dumps({"error": "Astra DB not available. Check your credentials."})
    #     try:
    #         target_collection = self.db.get_collection(collection_name)
    #         if not target_collection:
    #             logger.error(f"Collection '{collection_name}' not available.")
    #             return json.dumps({"error": "Collection not available."})
    #         result = target_collection.delete_one(filter_dict)
    #         logger.info(f"Deleted {result.deleted_count} document(s) from collection '{collection_name}'")
    #         return json.dumps({
    #             "success": True,
    #             "deleted_count": result.deleted_count
    #         })
    #     except Exception as e:
    #         logger.error(f"Failed to delete document from collection '{collection_name}': {str(e)}")
    #         return json.dumps({"error": f"Failed to delete document: {str(e)}"})
    
    def list_collections(self = None) -> str:
        """
        List all collections in the Astra DB database.
        """
        logger.debug("Listing all collections in Astra DB")
        
        if not self.db:
            logger.error("Astra DB not available. Check your credentials.")
            return json.dumps({"error": "Astra DB not available. Check your credentials."})
        try:
            collections = self.db.list_collection_names()
            logger.info(f"Found {len(collections)} collections: {collections}")
            return json.dumps({
                "success": True,
                "collections": collections
            })
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            return json.dumps({"error": f"Failed to list collections: {str(e)}"})
    
    def get_collection_info(
        self,
        tools_parameters: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> str:
        """
        Get information about a specific collection.
        """
        # Extract parameters from tools_parameters if provided
        if tools_parameters:
            collection_name = tools_parameters.get('collection_name', collection_name)
        
        logger.debug(f"Getting collection info for '{collection_name}'")
        
        if not self.db:
            logger.error("Astra DB not available. Check your credentials.")
            return json.dumps({"error": "Astra DB not available. Check your credentials."})
        try:
            target_collection = self.db.get_collection(collection_name)
            if not target_collection:
                logger.error(f"Collection '{collection_name}' not available.")
                return json.dumps({"error": "Collection not available."})
            info = target_collection.find_one()
            has_documents = info is not None
            logger.info(f"Collection '{collection_name}' info: has_documents={has_documents}")
            return json.dumps({
                "success": True,
                "collection_name": target_collection.name,
                "has_documents": has_documents
            })
        except Exception as e:
            logger.error(f"Failed to get collection info for '{collection_name}': {str(e)}")
            return json.dumps({"error": f"Failed to get collection info: {str(e)}"})

# Create a global instance
# db_manager = AstraDBManager(ctx) 