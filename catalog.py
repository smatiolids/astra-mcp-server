from database import AstraDBManager
from logger import get_logger
import os
import json
import argparse

class AstraCatalog:
    def __init__(self):
        self.astra_db_manager = AstraDBManager()
        self.logger = get_logger("catalog")

    def get_catalog(self):
        return self.astra_db_manager.get_catalog()
    
    def upload_catalog(self, catalog: dict):
        collection_name = os.getenv("ASTRA_DB_CATALOG_COLLECTION")
        collection = self.astra_db_manager.db.get_collection(collection_name)
        self.logger.info(f"Deleting all catalog items from {collection_name}")
        collection.delete_many({})
        self.logger.info(f"Uploading {len(catalog)} catalog items to {collection_name}")
        result = collection.insert_many(catalog)
        self.logger.info(f"Uploaded {len(result.inserted_ids)} catalog items")
        return result.inserted_ids    

def upload_catalog(file_path: str):
    catalog = AstraCatalog()
    catalog_content = json.load(open(file_path))
    print(catalog_content)
    catalog.upload_catalog(catalog_content)

def main():
    parser = argparse.ArgumentParser(description="Astra MCP Server Catalog Uploader")
    parser.add_argument("-f", "--file_path", help="Path to the catalog file")

    args = parser.parse_args()
    upload_catalog(args.file_path)

if __name__ == "__main__":
    main()
