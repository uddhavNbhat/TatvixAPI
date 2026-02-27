from pydantic_settings import SettingsConfigDict, BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent #Temp resoltion, should be dynamic in nature not static like this.

class Settings(BaseSettings):
    SQLITE_DB_NAME: str
    JWT_SECRET_KEY: str
    ENC_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ALLOWED_ORIGIN: str
    MONGODB_URI: str
    FILE_SERVICE_URI: str
    WEAVIATE_SERVER: str
    GOOGLE_API_KEY: str
    MCP_SERVER: str
    GROQ_API_KEY : str
    OPEN_ROUTER_API_KEY: str
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env") #Read your .env file

# Instantiate settings so that you can import the instance directly
settings = Settings()

if __name__ == "__main__":
    print(f"Loaded DB: {settings.SQLITE_DB_NAME}")