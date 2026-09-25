from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str

    jwt_secret: str
    access_token_lifetime_seconds: int = 3600

    # Also create the dataset's users (with known, development-only passwords: see app/seed_dataset.py).
    seed_dataset_users: bool = True
    dataset_path: str = "/app/data/AROL_Q2_synthetic_fleet_dataset.xlsx"

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    manuals_bucket: str = "manuals"
    manual_url_ttl_seconds: int = 60

    orchestrator_url: str = "http://orchestrator:8001"
    orchestrator_timeout_seconds: float = 120

    first_superuser_email: str | None = None
    first_superuser_password: str | None = None
    first_superuser_username: str = "admin"
    first_superuser_client_name: str = "default"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
