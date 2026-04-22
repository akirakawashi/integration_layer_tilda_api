from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from infrastructure.database.base import BaseModel
from infrastructure.database.models.tilda_job import TildaJob  # noqa: F401
from infrastructure.database.models.tilda_job_status import TildaJobStatus  # noqa: F401
from infrastructure.database.models.tilda_job_status_his import TildaJobStatusHistory  # noqa: F401
from infrastructure.database.reference_data import sync_reference_data
from setting.config import app_config, database_config

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseModel.metadata

db_url = (
    f"postgresql+asyncpg://{database_config.user}:"
    f"{database_config.password.get_secret_value()}@"
    f"{database_config.host}:{database_config.port}/{database_config.database}"
)
config.set_main_option("sqlalchemy.url", db_url)


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == app_config.db_schema

    schema_name = parent_names.get("schema_name")
    return schema_name == app_config.db_schema


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=app_config.db_schema,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema=app_config.db_schema,
        include_name=include_name,
    )

    with context.begin_transaction():
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{app_config.db_schema}"'))
        context.run_migrations()
        sync_reference_data(connection)


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
