from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service status")


class TildaWebhookPayload(BaseModel):
    tran_id: str | None = Field(default=None, alias="tranid")
    form_id: str | None = Field(default=None, alias="formid")
    test: str | None = Field(default=None, description="Tilda webhook test flag")
    file_url: str | None = Field(default=None, description="Resolved file URL from Tilda payload")
    payload: dict[str, str] = Field(
        default_factory=dict,
        exclude=True,
        description="Sanitized raw Tilda webhook payload",
    )

    @property
    def is_test_request(self) -> bool:
        return self.test == "test"


class TildaWebhookAcceptedResponse(BaseModel):
    tilda_job_id: int = Field(description="Stored Tilda job identifier")
    tran_id: str = Field(description="Unique Tilda submission identifier")
    duplicate: bool = Field(default=False, description="Whether this webhook had already been saved before")
