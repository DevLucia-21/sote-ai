from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "S:ote OCR API"

    # Spring Boot
    SPRING_SERVER_URL: str

    # GCP
    GOOGLE_APPLICATION_CREDENTIALS: str

    class Config:
        env_file = ".env"

settings = Settings()
