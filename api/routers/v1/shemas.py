from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(description="Service status")


class TildaWebhookAcceptedResponse(BaseModel):
    tilda_job_id: int = Field(description="Stored Tilda job identifier")
    tran_id: str = Field(description="Unique Tilda submission identifier")
    duplicate: bool = Field(
        default=False,
        description="Whether this webhook had already been saved before"
    )


class ProcessNextTildaJobResponse(BaseModel):
    processed: bool = Field(description="Whether a queued job was picked for processing")
    status: str = Field(description="Processing status for the picked job")
    message: str = Field(description="Human-readable processing result")
    tilda_job_id: int | None = Field(
        default=None,
        description="Processed Tilda job identifier"
    )
    tran_id: str | None = Field(
        default=None,
        description="Processed Tilda submission identifier"
    )
    google_drive_file_id: str | None = Field(
        default=None,
        description="Uploaded Google Drive file identifier when available"
    )
