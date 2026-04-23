from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service status")


class TildaWebhookAcceptedResponse(BaseModel):
    tilda_job_id: int = Field(description="Stored Tilda job identifier")
    tran_id: str = Field(description="Unique Tilda submission identifier")
    duplicate: bool = Field(default=False, description="Whether this webhook had already been saved before")
