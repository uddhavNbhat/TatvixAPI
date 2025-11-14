from fastmcp import FastMCP
import weaviate,requests
from McpServer.weaviate_client import get_weaviate_client
from weaviate.classes.query import MetadataQuery
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

WEAVIATE_SERVER=os.getenv("WEAVIATE_SERVER")

mcp = FastMCP(__name__)

weaviate_client = get_weaviate_client()

@mcp.tool
def document_search(query:str) -> dict:
    """ Tool to perform near vector search using gemma 300m embedding model with the help of weaviate vector db. """
    try:
        documents = weaviate_client.collections.use("Vectorbase")
        query_params = {
            'embed_type':'query'
        }
        response = requests.post(WEAVIATE_SERVER,params=query_params,json={"text":[query]})
        data = response.json()
        vector = data["vectors"][0]

        top_k_response = documents.query.near_vector(
            near_vector=vector,
            limit=5,
            return_metadata=MetadataQuery(distance=True),
        )

        final_response = defaultdict(list)

        for o in top_k_response.objects: #Logs for testing.
            final_response["text"].append(o.properties["text"])
            final_response["document_name"].append(o.properties["doc_name"])
            final_response["image_id"].append(o.properties["image_id"])
            print(o.properties["doc_name"])
            print(o.metadata.distance)


        return final_response

    except Exception as e:
        return {"Error":f"Exception -> {e}"}


if __name__ == "__main__": #For dev use case to run the file as script, so we define file specific entry point, can be run through CLI.
    mcp.run(transport="http",port=5050)
