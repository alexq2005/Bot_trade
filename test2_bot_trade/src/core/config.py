import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # IOL Credentials
    IOL_USERNAME: str = ""
    IOL_PASSWORD: str = ""

    # IOL API Endpoints
    IOL_API_URL: str = "https://api.invertironline.com/api/v2"
    IOL_TOKEN_URL: str = "https://api.invertironline.com/token"

    # App Settings
    APP_ENV: str = "development"
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
