from zoneinfo import ZoneInfo

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    name: str = Field(default="API_tilda", description="The name of the application")
    host: str = Field(default="0.0.0.0", description="The host address of the application")
    port: int = Field(default=8003, description="The port number of the application")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Application log level")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    db_schema: str = Field(default="integration_tilda", description="Database schema used by this service")


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

    echo: bool = Field(default=True, description="Disable SQLAlchemy echo in production")
    pool_size: int = Field(default=5, description="Database connection pool size")
    max_overflow: int = Field(default=15, description="Maximum overflow size of the connection pool")

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@"
            f"{self.host}:{self.port}/{self.database}"
        )


class NextcloudStorageConfig(BaseSettings):
    """Nextcloud WebDAV file storage configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="NEXTCLOUD_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: str = Field(default="", description="Base URL of the Nextcloud instance")
    username: str = Field(default="", description="Nextcloud username")
    app_password: SecretStr = Field(default=SecretStr(""), description="Nextcloud app password")
    dav_user_id: str | None = Field(
        default=None,
        description="Optional Nextcloud WebDAV files user id if it differs from username",
    )
    remote_dir: str = Field(default="tilda", description="Nextcloud directory for uploaded files")
    public_base_url: str | None = Field(
        default=None, description="Optional public base URL for uploaded files"
    )
    timeout_seconds: int = Field(default=30, description="WebDAV timeout for Nextcloud storage")


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
        default="storage/tilda_downloads", description="Project-relative directory for downloaded Tilda files"
    )
    max_size_mb: int = Field(default=25, description="Maximum allowed size for downloaded files in megabytes")
    allowed_extensions: str = Field(
        default="zip,rar",
        description="Comma-separated whitelist of allowed file extensions",
    )

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {
            extension.strip().lower().lstrip(".")
            for extension in self.allowed_extensions.split(",")
            if extension.strip()
        }


class WorkerConfig(BaseSettings):
    """Background worker configuration settings"""

    model_config = SettingsConfigDict(
        env_prefix="WORKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    id: str = Field(default="tilda-worker", description="Stable identifier of the worker instance")
    poll_interval_seconds: int = Field(
        default=5, description="Delay before polling again when there are no ready jobs"
    )
    error_backoff_seconds: int = Field(default=10, description="Delay after unexpected worker loop errors")
    lock_seconds: int = Field(default=300, description="Lease duration for claimed jobs")
    retry_delay_seconds: int = Field(default=300, description="Delay before retrying retryable job failures")
    max_attempts: int = Field(default=10, description="Maximum processing attempts for one job")
    shutdown_grace_seconds: int = Field(default=30, description="Maximum graceful shutdown wait time")


app_config = AppConfig()
database_config = DatabaseConfig()
nextcloud_storage_config = NextcloudStorageConfig()
file_downloader_config = FileDownloaderConfig()
worker_config = WorkerConfig()
