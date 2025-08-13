from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field


class Settings(BaseSettings):
    bot_token: SecretStr
    admin_id: int = Field(..., alias='LAWYER_ID')
    database: str = Field(..., alias='DATABASE')
    db_host: str = Field(..., alias='DB_HOST')
    db_port: str = Field(..., alias='DB_PORT')
    db_user: str = Field(..., alias='DB_USER')
    db_password: str = Field(..., alias='DB_PASSWORD')
    # webhook_url: str = Field(..., alias='webhook_url')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )

settings = Settings()