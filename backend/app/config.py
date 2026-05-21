from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).parent.parent  # project root


class Settings(BaseSettings):

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str = ""

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    MODEL_PATH: str = "ml/ResNet50V2_neuroscan.h5"
    CLASSES_PATH: str = "ml/ResNet50V2_neuroscan_classes.json"

    FRONTEND_URLS: str = "http://localhost:5173,http://localhost:3000"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    #create url lists
    @property
    def frontend_urls_list(self) -> List[str]:
        return [u.strip() for u in self.FRONTEND_URLS.split(",") if u.strip()]

    #create uploads
    @property
    def upload_dir_path(self) -> Path:
        path = BASE_DIR / self.UPLOAD_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    #mb to byte
    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    #empty to none
    @property
    def cookie_domain_or_none(self) -> str | None:
        return self.COOKIE_DOMAIN if self.COOKIE_DOMAIN else None


settings = Settings()
