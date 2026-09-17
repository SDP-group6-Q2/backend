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

    # mcp-server's internal admin/service surface (see mcp-server/app/internal_api.py) --
    # used only for provisioning-time validation of user_id/company_id against the
    # fleet dataset, never for anything end-user-facing.
    mcp_server_url: str = "http://mcp-server:9000"
    internal_service_secret: str

    first_superuser_email: str | None = None
    first_superuser_password: str | None = None
    first_superuser_username: str = "admin"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
