from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_client_id: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    google_sheets_id: str = ""
    google_service_account_file: str = "credentials.json"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    firebase_credentials_file: str = "firebase-credentials.json"

    model_config = {"env_file": ".env"}
