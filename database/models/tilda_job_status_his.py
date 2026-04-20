from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship

from database.base import BaseModel

if TYPE_CHECKING:
    from .tilda_job import TildaJob
    from .tilda_job_status import TildaJobStatus


class TildaJobStatusHistory(BaseModel, table=True):
    __tablename__ = "tilda_job_status_history"

    tilda_job_status_history_id: int | None = Field(
        default=None,
        primary_key=True,
        description="Unique identifier for each Tilda job status history record"
    )

    tilda_job_id: int = Field(
        foreign_key="tilda_job.tilda_job_id",
        nullable=False,
        description="Reference to the related Tilda job"
    )

    tilda_job_status_id: int = Field(
        foreign_key="tilda_job_status.tilda_job_status_id",
        nullable=False,
        description="Reference to the job status at the moment of the change"
    )

    date_create: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        ),
        description="Timestamp when the status history record was created"
    )

    job: "TildaJob" = Relationship()
    status: "TildaJobStatus" = Relationship()
