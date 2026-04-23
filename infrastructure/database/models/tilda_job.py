from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship

from infrastructure.database.base import BaseModel
from setting.config import app_config

if TYPE_CHECKING:
    from .tilda_job_status import TildaJobStatus


class TildaJob(BaseModel, table=True):
    __tablename__ = "tilda_job"

    tilda_job_id: int | None = Field(
        default=None, primary_key=True, description="Unique identifier for each Tilda job"
    )

    tran_id: str = Field(
        nullable=False, unique=True, index=True, description="Unique identifier of the Tilda form submission"
    )

    form_id: str = Field(nullable=False, index=True, description="Identifier of the Tilda form")

    payload: dict = Field(
        sa_column=Column(JSONB, nullable=False), description="Raw webhook request data received from Tilda"
    )

    file_url: str = Field(nullable=False, description="Direct URL of the uploaded file received from Tilda")

    tilda_job_status_id: int = Field(
        foreign_key=f"{app_config.db_schema}.tilda_job_status.tilda_job_status_id",
        nullable=False,
        index=True,
        description="Reference to the current status of the job",
    )

    next_retry_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
        description="Timestamp when the job may be retried after a recoverable failure",
    )

    locked_by: str | None = Field(
        default=None, index=True, description="Identifier of the worker that currently holds the job lease"
    )

    locked_until: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
        description="Timestamp when the current worker lease expires",
    )

    attempt_count: int = Field(
        default=0, nullable=False, description="Number of processing attempts already made"
    )

    last_error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Last human-readable processing error",
    )

    stored_file_name: str | None = Field(
        default=None,
        nullable=True,
        description="Generated file name used by the storage backend after successful upload",
    )

    date_create: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="Timestamp when the job was created",
    )

    date_update: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
        ),
        description="Timestamp when the job was last updated",
    )

    status: "TildaJobStatus" = Relationship(back_populates="jobs")
