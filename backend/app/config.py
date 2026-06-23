from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./rider_starter.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    sql_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
