from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from zoneinfo import ZoneInfo

APP_TIMEZONE = "Europe/Moscow"
APP_TIMEZONE_INFO = ZoneInfo(APP_TIMEZONE)

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
    db_schema: str = Field(
        default="integration_tilda",
        description="Database schema used by this service"
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


class KafkaConfig(BaseSettings):
    """Kafka configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    enabled: bool = Field(default=False, description="Enable Kafka integration")
    bootstrap_servers: str = Field(
        default="localhost:9094",
        description="Comma-separated Kafka bootstrap servers"
    )
    client_id: str = Field(
        default="tilda-api",
        description="Kafka client id for this service"
    )
    tilda_job_created_topic: str = Field(
        default="tilda.job.created",
        description="Topic for created Tilda jobs"
    )

    @property
    def bootstrap_servers_list(self) -> list[str]:
        return [
            server.strip()
            for server in self.bootstrap_servers.split(",")
            if server.strip()
        ]


class GoogleDriveConfig(BaseSettings):
    """Google Drive configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_DRIVE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    access_token: SecretStr = Field(
        default=SecretStr(""),
        description="OAuth access token used for Google Drive uploads"
    )
    folder_id: str | None = Field(
        default=None,
        description="Optional Google Drive folder id for uploaded files"
    )
    timeout_seconds: int = Field(
        default=60,
        description="Upload timeout for Google Drive requests"
    )


class FileDownloaderConfig(BaseSettings):
    """File downloader configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="FILE_DOWNLOADER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    dir: str = Field(
        default="storage/tilda_downloads",
        description="Project-relative directory for downloaded Tilda files"
    )
    max_size_mb: int = Field(
        default=25,
        description="Maximum allowed size for downloaded files in megabytes"
    )
    allowed_extensions: str = Field(
        default="pdf,doc,docx,xls,xlsx,csv,png,jpg,jpeg",
        description="Comma-separated whitelist of allowed file extensions"
    )

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {
            extension.strip().lower().lstrip(".")
            for extension in self.allowed_extensions.split(",")
            if extension.strip()
        }


app_config = AppConfig()  
database_config = DatabaseConfig()
kafka_config = KafkaConfig()
google_drive_config = GoogleDriveConfig()
file_downloader_config = FileDownloaderConfig()
