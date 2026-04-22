import sqlalchemy as sa

from setting.config import app_config


def sync_reference_data(connection) -> None:
    inspector = sa.inspect(connection)
    if not inspector.has_table("tilda_job_status", schema=app_config.db_schema):
        return

    connection.execute(
        sa.text(
            f"""
            INSERT INTO {app_config.db_schema}.tilda_job_status (tilda_job_status_id, status_code) VALUES
                (1, 'queued'),
                (2, 'processing'),
                (3, 'done'),
                (4, 'failed'),
                (5, 'retry_wait')
            ON CONFLICT (tilda_job_status_id)
            DO UPDATE SET status_code = EXCLUDED.status_code
            """
        )
    )
