from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers.chat import create_chat, read_chat, delete_chat
from app.routers.folders import create_folders, read_folders
from app.routers.setup import create_setup, delete_setup
from app.routers.auth import authenticate
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from langgraph.checkpoint.mongodb import MongoDBSaver

origins = [
    settings.ALLOWED_ORIGIN,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Method to instantiate/initialize certain objects and parameters during app startup and free them after shutdown"""
    from app.dbconfig import (
        get_sqlite_config,
        get_weaviate_client,
        get_pymongo_client,
    )

    app.state.sqlite_config = (
        get_sqlite_config()
    )  # This will initialize the database connection string.
    weaviate_obj = get_weaviate_client()
    app.state.weaviate_client = weaviate_obj.client
    # Create weaviate schema on first time boot.
    weaviate_obj.create_weaviate_schema()
    pymongo = get_pymongo_client()
    app.state.checkpointer = MongoDBSaver(pymongo.pymongo_client)
    yield
    app.state.weaviate_client.close()
    print("Server Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authenticate.router)
app.include_router(create_setup.router)
app.include_router(delete_setup.router)
app.include_router(create_chat.router)
app.include_router(read_chat.router)
app.include_router(delete_chat.router)
app.include_router(create_folders.router)
app.include_router(read_folders.router)
