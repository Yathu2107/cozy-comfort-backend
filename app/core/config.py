from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = "mysql+pymysql://root:Yathu%402002%40@localhost:3306/cozy_comfort_db"

    # JWT configuration
    SECRET_KEY: str = "your-secret-key"  # Replace with a secure key in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Other settings
    PROJECT_NAME: str = "Cozy Comfort API"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

# Singleton instance
settings = Settings()