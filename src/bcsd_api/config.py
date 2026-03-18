from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_client_id: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    google_sheets_id: str = ""
    google_service_account_file: str = "credentials.json"
    resend_api_key: str = ""
    resend_sender: str = "onboarding@resend.dev"
    cors_origins: str = "http://localhost:3000"
    cookie_name: str = "access_token"
    cookie_secure: bool = True
    spicedb_host: str = "spicedb"
    spicedb_port: int = 50051
    spicedb_token: str = ""
    slack_bot_token: str = ""
    slack_error_channel: str = ""
    postgres_user: str = "bcsd"
    postgres_password: str = ""
    postgres_db: str = "bcsd"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    sync_token: str = ""
    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
