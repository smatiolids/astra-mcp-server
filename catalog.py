from math import e
from database import AstraDBManager
from logger import get_logger
import os
import json
import argparse
from dotenv import load_dotenv
from utils import add_underscore_to_dict_keys
load_dotenv(override=True)

class AstraCatalog:
    logger = get_logger("catalog")
    
    def __init__(self):
        self.astra_db_name = os.getenv("ASTRA_DB_DB_NAME")
        self.astra_db_manager = AstraDBManager(os.getenv("ASTRA_DB_APPLICATION_TOKEN"), os.getenv("ASTRA_DB_API_ENDPOINT"), self.astra_db_name)
        self.db = self.astra_db_manager.db[self.astra_db_name]
    
    def upload_catalog(self, catalog: dict, table_name: str):
        collection_name = table_name
        
        list_collections = self.db.list_collection_names()
        self.logger.info(f"List of collections: {list_collections}")
        
        if collection_name not in list_collections:
            self.logger.info(f"Collection {collection_name} not found, creating it")
            self.db.create_collection(collection_name)
            self.logger.info(f"Collection {collection_name} created")
        
        collection = self.db.get_collection(collection_name)
            
        self.logger.info(f"Deleting all catalog items from {collection_name}")
        collection.delete_many({})
        self.logger.info(f"Uploading {len(catalog)} catalog items to {collection_name}")
        result = collection.insert_many(catalog)
        self.logger.info(f"Uploaded {len(result.inserted_ids)} catalog items")
        return result.inserted_ids    

def upload_catalog(file_path: str, table_name: str):
    catalog = AstraCatalog()
    catalog_content = json.load(open(file_path))
    catalog_content = add_underscore_to_dict_keys(catalog_content)
    catalog.upload_catalog(catalog_content, table_name)

def main():
    parser = argparse.ArgumentParser(description="Astra MCP Server Catalog Uploader")
    parser.add_argument("-f", "--file_path", help="Path to the catalog file")
    parser.add_argument("-t", "--table_name", default=os.getenv("ASTRA_DB_CATALOG_COLLECTION") or "tool_catalog", help="Table name")

    args = parser.parse_args()
    upload_catalog(args.file_path, args.table_name)

if __name__ == "__main__":
    main()
