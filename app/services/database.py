from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger("pharmacy_module.database")

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            try:
                cls._instance.client = MongoClient(os.getenv("MONGO_URI"))
                cls._instance.db = cls._instance.client["pharmacy_db"]
                logger.info("Database connection established")
            except ConnectionFailure as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        return cls._instance

    def get_db(self):
        return self.db

db_instance = Database()
get_db = db_instance.get_db