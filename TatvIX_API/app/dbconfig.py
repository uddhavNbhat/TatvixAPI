from app.config.settings import settings
from sqlmodel import create_engine, SQLModel
from weaviate import WeaviateClient
from pymongo import MongoClient
from typing import Callable
from app.utils.logger import logger
import weaviate
import weaviate.classes.config as wc
import time

# import asyncio


class SQLiteConfig:
    def __init__(self):
        self.file_name = settings.SQLITE_DB_NAME
        self.url = f"sqlite:///{self.file_name}"
        self.connection_args = {
            "check_same_thread": False  # Make sure multi-threaded sessions are possible
        }
        self.engine = create_engine(self.url, connect_args=self.connection_args)
        self._create_db_and_tables()

    def _create_db_and_tables(self):
        """Method to create database and all default tables if not created."""
        SQLModel.metadata.create_all(self.engine)


class PyMongoConfig:
    def __init__(self):
        self.pymongo_client = MongoClient(settings.MONGODB_URI)


class WeaviateClientFactory:
    """
    Weaviate client factory that generates weaviate client object. (Used only once throughout app lifecycle as a singleton)
    Purpose of using a factory is implementation of langgraph store in weaviate and a seperate weaviate object for performing doc embeddings.
    """

    _client: WeaviateClient | None = None

    @classmethod
    def get_client(cls) -> WeaviateClient:
        if cls._client is None:
            cls._client = cls._create_client()
            cls._client.connect()
        return cls._client

    @staticmethod
    def _create_client() -> WeaviateClient:
        retries = 5
        for attempt in range(retries):
            try:
                return weaviate.connect_to_custom(
                    http_host="localhost",
                    http_secure=False,
                    http_port=8080,
                    grpc_host="localhost",
                    grpc_port=50051,
                    grpc_secure=False,
                )
            except Exception as e:
                logger.error(f"Attempt {attempt}: {e}")
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    raise


class WeaviateConfig:
    def __init__(self):
        self.client: WeaviateClient = WeaviateClientFactory.get_client()

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
                        wc.Property(name="text", data_type=wc.DataType.TEXT),
                        wc.Property(name="file_id", data_type=wc.DataType.TEXT),
                        wc.Property(name="page_no", data_type=wc.DataType.TEXT),
                        wc.Property(name="folder_id", data_type=wc.DataType.TEXT),
                    ],
                    vector_config=wc.Configure.Vectors.self_provided(),
                )

                self.client.collections.create(
                    name="UserQueryStore",
                    properties=[
                        wc.Property(name="thread_id", data_type=wc.DataType.TEXT),
                        wc.Property(name="user_query", data_type=wc.DataType.TEXT),
                    ],
                    vector_config=wc.Configure.Vectors.self_provided(),
                )

        except Exception as e:
            print(f"Exception Occured : {e}")

    def close_client(self):
        """method to close weaviate client object"""
        if self.client is not None:
            self.client.close()


def get_sqlite_config():
    return SQLiteConfig()


def get_weaviate_client():
    return WeaviateConfig()


def get_pymongo_client():
    return PyMongoConfig()
