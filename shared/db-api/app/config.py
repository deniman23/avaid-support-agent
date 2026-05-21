from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://support_reader:support_reader_pass@localhost:5433/avaid_support"
    support_api_key: str = "change-me-local-dev-key"
    max_rows: int = 50
    rate_limit_per_minute: int = 30
    # readonly — только GET; readwrite — PATCH для рубильников и привязки (роль support_writer)
    db_api_mode: Literal["readonly", "readwrite"] = "readwrite"

    class Config:
        env_file = ".env"

    @property
    def writes_enabled(self) -> bool:
        return self.db_api_mode == "readwrite"


settings = Settings()
