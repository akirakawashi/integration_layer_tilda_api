from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship

from database.base import BaseModel
if TYPE_CHECKING:
    from .tilda_job_status import TildaJobStatus

class TildaJob(BaseModel, table=True):
    __tablename__ = "tilda_job"

    tilda_job_id: int | None = Field(
        default=None,
        primary_key=True,
        description="Unique identifier for each Tilda job"
    )

    webhook_event_id: str = Field(
        nullable=False,
        unique=True,
        index=True,
        description="Unique identifier for the webhook event from Tilda"
    )

    payload_json: dict = Field(
        sa_column=Column(
            JSONB, 
            nullable=False
            ), 
        description="Raw webhook request data received from Tilda"
    )

    tilda_job_status_id: int = Field(
        foreign_key="tilda_job_status.tilda_job_status_id",
        nullable=False,
        index=True,
        description="Reference to the current status of the job"
    )

    attempt_count: int = Field(
        default=0,
        nullable=False,
        description="Number of processing attempts already made"
    )

    date_create: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(), 
            nullable=False),
        description="Timestamp when the job was created"
    )

    date_update: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        ),
        description="Timestamp when the job was last updated"
    )

    status: "TildaJobStatus" = Relationship(back_populates="jobs")
