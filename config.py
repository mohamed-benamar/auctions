import os
from pathlib import Path
from typing import List, Optional
from pydantic import PostgresDsn, EmailStr, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Paramètres de configuration pour l'application.
    Les valeurs sont lues depuis le fichier .env à la racine du projet.
    """
    
    # Configuration de base
    APP_NAME: str = "Plateforme d'Enchères Judiciaires Simple"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Configuration serveur
    HOST: str = "127.0.0.1"
    PORT: int = 9000
    CORS_ORIGINS: List[str] = ["*"]
    
    # Configuration pour le stockage des fichiers
    STATIC_FILES_DIR: Path = Path(__file__).resolve().parent.parent / "static"
    IMAGES_DIR: str = "images"
    DOCUMENTS_DIR: str = "documents"
    MEDIA_BASE_URL: str = "/static"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_DOCUMENT_TYPES: List[str] = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    # Configuration de la base de données
    DATABASE_URL: str
    
    # Configuration JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Configuration Email
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_TLS: bool = False
    MAIL_SSL: bool = False
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    
    # Informations admin pour l'initialisation
    ADMIN_EMAIL: EmailStr
    ADMIN_PASSWORD: str
    SUPERADMIN_EMAIL: EmailStr
    SUPERADMIN_PASSWORD: str
    
    # Chemins
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent / "templates"
    
    # Méthode pour déterminer si nous sommes en production
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Instance unique des paramètres, à utiliser dans toute l'application
settings = Settings()
