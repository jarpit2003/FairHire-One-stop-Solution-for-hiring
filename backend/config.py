from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/fairhire"
    ENVIRONMENT: str = "development"

    # Upload
    MAX_UPLOAD_SIZE_MB: float = 10.0

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # SMTP email — legacy, use RESEND_API_KEY instead
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # Brevo (Sendinblue) — transactional email, sends to any address, no domain needed
    BREVO_API_KEY: str = ""
    BREVO_FROM_EMAIL: str = ""
    BREVO_FROM_NAME: str = "FairHire AI"

    # Resend — fallback
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "FairHire AI <onboarding@resend.dev>"

    # X (Twitter) API v2
    X_ENABLED: bool = False
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    X_ACCESS_TOKEN: str = ""
    X_ACCESS_TOKEN_SECRET: str = ""

    # Google Forms
    GOOGLE_FORMS_ENABLED: bool = False
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # JWT
    JWT_SECRET: str = "CHANGE_ME_SET_JWT_SECRET_IN_DOT_ENV"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours

    # Webhook
    WEBHOOK_SECRET: str = ""  # shared secret for POST /webhook/test-score


settings = Settings()
