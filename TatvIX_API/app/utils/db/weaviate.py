from typing import List
from sqlmodel import select
from weaviate import WeaviateClient
from weaviate.exceptions import UnexpectedStatusCodeError
from httpx import AsyncClient
from app.models.models import Images, Files
from app.config.settings import settings
from app.utils.logger import logger
from app.utils.db.sql import SQLSessionDep
from app.validators.setup import PopulateWeaviate
from app.validators.setup import WeaviateMetaDataSchema


async def get_data(
    session: SQLSessionDep, file_data: PopulateWeaviate
) -> List[WeaviateMetaDataSchema]:
    """Method to perform a read and retrieve data from SQL database for weaviate meta data to reference"""
    try:
        file_paths = list({x.file_id for x in file_data.files})
        # Get all file data from written files.
        file_db_response = session.exec(
            select(Images)
            .join(Files, Images.file_id == Files.id)
            .where(Files.file_path.in_(file_paths))
        ).all()
        # Construct weaviate payload.
        data = [
            {
                "text": t.text,
                "file_id": str(t.file_id) if t.file_id is not None else "",
                "page_no": str(t.page_no) if t.page_no is not None else "",
            }
            for t in file_db_response
        ]

        return data
    except Exception as e:
        logger.error(f"Error at utils.db.weaviate.get_data: {e}")
        raise e


async def store_data(data: List[dict], weaviate_client: WeaviateClient, folder_id: str):
    """Method to store data in weaviate database through batches"""
    try:
        embeddings = weaviate_client.collections.get(
            "Vectorbase"
        )  # Can use, "use" too but using "get" as per previous implementation.
        embedding_errors = 0
        # batch system to dynamically set batch sizes for insertion of data as it is effecient to batch large amounts of data instead of passing it as an object.
        async with AsyncClient() as client:
            with embeddings.batch.fixed_size(batch_size=200) as batch:
                for index, item in enumerate(data, start=1):
                    try:
                        embedding_response = await client.post(
                            settings.WEAVIATE_SERVER,
                            params={"embed_type": "document"},
                            json={"text": [item["text"]]},
                        )
                        logger.info(
                            f"Status code for embedding: {embedding_response.status_code}"
                        )
                        embedding_response.raise_for_status()
                        vector_data = embedding_response.json().get("vectors", [])
                        if not vector_data:
                            raise ValueError(
                                "Embedding response did not contain vectors"
                            )
                        vector = vector_data[0]

                        properties = {
                            "text": item["text"],
                            "file_id": item["file_id"],
                            "page_no": item["page_no"],
                            "folder_id": folder_id,
                        }

                        batch.add_object(properties=properties, vector=vector)
                    except Exception as item_error:
                        embedding_errors += 1
                        logger.error(
                            f"Embedding/object preparation failed for row {index}: {item_error}"
                        )
                        if embedding_errors > 10:
                            logger.error(
                                "Batch import stopped due to excessive embedding/prep errors."
                            )
                            break

                    if batch.number_errors > 10:
                        logger.error(
                            "Batch import stopped due to excessive Weaviate batch errors."
                        )
                        break
        # Failed objects log
        failed_objects = embeddings.batch.failed_objects
        if failed_objects:
            logger.error(f"Number of failed imports: {len(failed_objects)}")
            logger.error(f"First failed object: {failed_objects[0]}")
            raise RuntimeError(
                f"Weaviate batch import failed for {len(failed_objects)} objects"
            )

    except UnexpectedStatusCodeError:
        raise

    except Exception as e:
        logger.error(f"Error at utils.db.weaviate: {e}")
        raise
