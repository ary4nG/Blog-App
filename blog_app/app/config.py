from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    # blog_app runs on the host, so it reaches the broker via the EXTERNAL listener
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()