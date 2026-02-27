from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from typing import List
import os
from pathlib import Path
from app.config.settings import settings
from app.utils.logger import logger

class Gemini:
    """
    Gemini Class that holds all supported gemini models to make use of:
        Supported models:
            1. gemini-2.5-flash-lite
            2. gemini-2.5-flash
            3. gemini-2.5-pro
    """
    _api_key : str = settings.GOOGLE_API_KEY
    _supported_models : List[str] = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemma-3-27b-it"
    ]
    def __init__(self, model_name):
        self.model = self._init_model(model_name=model_name)

    def _init_model(self, model_name) -> ChatGoogleGenerativeAI:
        """ Method to return instance of selected model """
        if model_name not in self._supported_models:
            raise Exception("Model not supported!")

        return ChatGoogleGenerativeAI(
            model = model_name,
            google_api_key = self._api_key,
        )


class OpenRouter:
    """
        Open Router Class that holds all supported Open Router models to make use of:
        Supported models:
            1.  openai/gpt-oss-120b:free
            2.  openai/gpt-oss-20b:free
    """
    _api_key : str = settings.GOOGLE_API_KEY
    _supported_models : List[str] = [
        "openai/gpt-oss-120b:free",
        "openai/gpt-oss-20b:free"
    ]
    def __init__(self, model_name):
        self.model = self._init_model(model_name=model_name)

    def _init_model(self, model_name) -> ChatOpenAI:
        """ Method to return instance of selected model """
        if model_name not in self._supported_models:
            raise Exception("Model not supported!")

        return ChatOpenAI(
            model = model_name,
            api_key = settings.OPEN_ROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

class Groq:
    """
    Groq Class that holds all supported groq models to make use of:
        Supported models:
            1. llama-3.1-8b-instant
            2. llama-3.3-70b-versatile
            3. openai/gpt-oss-20b
            4. qwen/qwen3-32b
    """
    _api_key : str = settings.GROQ_API_KEY
    _supported_models : List[str] = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-20b",
        "qwen/qwen3-32b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "groq/compound",
    ]
    def __init__(self, model_name):
        self.model = self._init_model(model_name=model_name)

    def _init_model(self, model_name) -> ChatGroq:
        """ Method to return instance of selected model """
        if model_name not in self._supported_models:
            raise Exception("Model not supported!")

        return ChatGroq(
            model=model_name,
            api_key=self._api_key,
            max_retries=2
        )


class Ollama:
    """
    Ollama Class that holds all supported Ollama models to make use of:
        Supported models:
            1. qwen3:4b
        Can expand to more based on your hardware spec, as this is a local family model.
    """
    _supported_models : List[str] = [
        "qwen3:4b",
        "qwen3:8b"
    ]

    def __init__(self, model_name):
        self.model = self._init_model(model_name=model_name)

    @staticmethod
    def _sanitize_ssl_env() -> None:
        ssl_cert_file = os.getenv("SSL_CERT_FILE")
        if ssl_cert_file and not Path(ssl_cert_file).exists():
            logger.warning(f"Invalid SSL_CERT_FILE detected: {ssl_cert_file}. Clearing it for Ollama client.")
            os.environ.pop("SSL_CERT_FILE", None)

        ssl_cert_dir = os.getenv("SSL_CERT_DIR")
        if ssl_cert_dir and not Path(ssl_cert_dir).exists():
            logger.warning(f"Invalid SSL_CERT_DIR detected: {ssl_cert_dir}. Clearing it for Ollama client.")
            os.environ.pop("SSL_CERT_DIR", None)

    def _init_model(self, model_name) -> ChatOllama:
        """ Method to return instance of selected model """
        if model_name not in self._supported_models:
            raise Exception("Model not supported!")

        self._sanitize_ssl_env()

        return ChatOllama(
            model=model_name,
            base_url=getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        )

class ModelFactory:
    _providers : dict = {
        "gemini": Gemini,
        "ollama": Ollama,
        "groq": Groq,
        "router": OpenRouter
    }
    
    @classmethod
    def initialize_model(cls, model_family, model_name) -> Gemini | Ollama | Groq | OpenRouter:
        """ class constructor Method to return model instance according to selected family and model name """
        if model_family not in cls._providers:
            raise Exception("Model not supported!")

        return cls._providers[model_family](model_name) #Return model instance accordingly.


