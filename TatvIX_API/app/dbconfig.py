from app.config.settings import settings
from sqlmodel import create_engine,SQLModel
from weaviate import WeaviateClient
from pymongo import MongoClient
from app.utils.logger import logger
import weaviate
import weaviate.classes.config as wc
import time
# import asyncio

class SQLiteConfig():
    def __init__(self):
        self.file_name=settings.SQLITE_DB_NAME
        self.url=f"sqlite:///{self.file_name}"
        self.connection_args = {
            "check_same_thread":False #Make sure multi-threaded sessions are possible
        }
        self.engine = create_engine(self.url, connect_args=self.connection_args)
        self._create_db_and_tables()

    def _create_db_and_tables(self):
        """ Method to create database and all default tables if not created. """
        SQLModel.metadata.create_all(self.engine)

class PyMongoConfig():
    def __init__(self):
        self.pymongo_client = MongoClient(settings.MONGODB_URI)


class WeaviateConfig():
    def __init__(self):
        self.client: WeaviateClient = None
    
    @classmethod
    def initialize_weaviate_config(cls):
        self = cls()
        self.client = self._get_weaviate_client()
        self.client.connect()
        return self

    @staticmethod
    def _get_weaviate_client() -> WeaviateClient:
        """ Get weaviate client object """
        retries = 5
        for attempt in range(retries):
            try:
                client =  weaviate.connect_to_custom(
                    http_host="localhost",
                    http_secure=False,
                    http_port=8080,
                    grpc_host="localhost",
                    grpc_port=50051,
                    grpc_secure=False,
                )
                return client
            except Exception as e:
                logger.error(f"Weaviate connection failed (attempt {attempt}/{retries}): {e}")
                if attempt < retries -1:
                    time.sleep(5)
                else:
                    raise RuntimeError("Failed to connect to Weaviate after multiple retries.") from e


    def create_weaviate_schema(self):
        """Create a weaviate database collection with a defined schema."""
        try:
            existing = self.client.collections.list_all()
            if "Vectorbase" in existing:
                print("Collection 'Vectorbase' already exists. Skipping creation.")

            else:
                self.client.collections.create(
                    name="Vectorbase",
                    properties=[
                        wc.Property(name="text",data_type=wc.DataType.TEXT),
                        wc.Property(name="file_id",data_type=wc.DataType.TEXT),
                        wc.Property(name="page_no",data_type=wc.DataType.TEXT),
                    ],
                vector_config= wc.Configure.Vectors.self_provided(),
                )
        except Exception as e:
            print(f"Exception Occured : {e}")
            
    def close_client(self):
        """ method to close weaviate client object """
        if self.client is not None:
            self.client.close()


def get_sqlite_config():
    return SQLiteConfig()

def get_weaviate_client():
    return WeaviateConfig.initialize_weaviate_config()

def get_pymongo_client():
    return PyMongoConfig()

