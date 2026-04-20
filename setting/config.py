from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    """Application configuration settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    name: str = Field(
        default="API_tilda", 
        description="The name of the application"
        )
    host: str = Field(
        default="0.0.0.0",
        description="The host address of the application"
    )
    port: int = Field(
        default=8003,
        description="The port number of the application"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    api_prefix: str = Field(
        default="/api/v1",
        description="API prefix"
    )

class DatabaseConfig(BaseSettings):
    """Database configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    user: str = Field(default="tilda_api", description="Database user")
    password: SecretStr = Field(default=SecretStr("tilda_api"), description="Database password")
    database: str = Field(default="tilda_api", description="Database name")

    url: str = Field(
        default="postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
        description="Asynchronous database URL"
    )
    echo: bool = Field(default=True, description="Disable SQLAlchemy echo in production")
    pool_size: int = Field(default=5, description="Database connection pool size")
    max_overflow: int = Field(default=15, description="Maximum overflow size of the connection pool")


app_config = AppConfig()  
database_config = DatabaseConfig()