from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_client_id: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    google_sheets_id: str = ""
    google_service_account_file: str = "credentials.json"
    resend_api_key: str = ""
    resend_sender: str = "onboarding@resend.dev"
    cors_origins: str = "http://localhost:3000"
    cookie_name: str = "access_token"
    cookie_secure: bool = False
    spicedb_endpoint: str = "spicedb:50051"
    spicedb_token: str = "bcsd-dev-token"
    model_config = {"env_file": ".env"}
