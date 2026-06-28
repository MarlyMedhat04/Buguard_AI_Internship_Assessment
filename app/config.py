from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/darkatlas"
    MODEL_NAME: str = "gemini-flash-latest"
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    CERT_EXPIRING_DAYS: int = 30
    LOG_LEVEL: str = "INFO"
    JWT_SECRET: str = "change_me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
