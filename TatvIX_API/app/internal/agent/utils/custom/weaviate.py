from weaviate import WeaviateClient
from weaviate.classes.query import Filter
from weaviate.classes.query import MetadataQuery
from typing import Callable, List
from httpx import AsyncClient
from app.utils.logger import logger
from app.config.settings import settings
from app.dbconfig import WeaviateClientFactory

"""
self.client.collections.create(
                    name="UserQueryStore",
                    properties=[
                        wc.Property(name="thread_id", data_type=wc.DataType.TEXT),
                        wc.Property(name="user_query", data_type=wc.DataType.TEXT),
                    ],
                    vector_config=wc.Configure.Vectors.self_provided(),
                )
"""


class WeaviateStore:
    def __init__(self):
        self.client: WeaviateClient = WeaviateClientFactory.get_client()
        self.collection = self.client.collections.use("UserQueryStore")

    async def put(self, thread_id: str, user_query: str):
        """Method to store embedding of a user query along with thread id as meta data for search filters"""
        doc = {"thread_id": thread_id, "user_query": user_query}
        async with AsyncClient() as embed_client:
            try:
                embedding_response = await embed_client.post(
                    settings.WEAVIATE_SERVER,
                    params={
                        "embed_type": "query",
                    },
                    json={"text": [user_query]},
                )
                embedding_response.raise_for_status()
                vector_data = embedding_response.json().get("vectors", [])
                if not vector_data:
                    raise ValueError("Embedding response did not contain vectors")
                vector = vector_data[0]

                self.collection.data.insert(properties=doc, vector=vector)

            except Exception as e:
                logger.error(f"Error at agent.utils.custom.weaviate.put: {e}")
                raise e

    async def search(self, thread_id: str, user_query: str) -> List[str]:
        async with AsyncClient() as embed_client:
            try:
                embedding_response = await embed_client.post(
                    settings.WEAVIATE_SERVER,
                    params={
                        "embed_type": "query",
                    },
                    json={"text": [user_query]},
                )
                embedding_response.raise_for_status()
                vector_data = embedding_response.json().get("vectors", [])
                if not vector_data:
                    raise ValueError("Embedding response did not contain vectors")
                vector = vector_data[0]

                response = self.collection.query.near_vector(
                    near_vector=vector,
                    filters=Filter.by_property("thread_id").equal(thread_id),
                    limit=3,
                    return_metadata=MetadataQuery(distance=True),
                )

                final_response = []

                for o in response.objects:
                    final_response.append(o.properties["user_query"])

                return final_response

            except Exception as e:
                logger.error(f"Error at agent.utils.custom.weaviate.search: {e}")
                raise e
