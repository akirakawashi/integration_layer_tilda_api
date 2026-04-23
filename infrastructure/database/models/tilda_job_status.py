from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship

from infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from .tilda_job import TildaJob


class TildaJobStatus(BaseModel, table=True):
    __tablename__ = "tilda_job_status"

    tilda_job_status_id: int | None = Field(
        default=None, primary_key=True, description="Unique identifier for the Tilda job status"
    )

    status_code: str = Field(
        nullable=False,
        unique=True,
        index=True,
        description="Unique code of the job status (e.g., queued, processing, done, failed)",
    )

    jobs: List["TildaJob"] = Relationship(back_populates="status")
