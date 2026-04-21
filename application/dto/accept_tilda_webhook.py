from dataclasses import dataclass


@dataclass(slots=True)
class AcceptTildaWebhookCommand:
    tran_id: str
    form_id: str
    file_url: str
    payload: dict[str, str]


@dataclass(slots=True)
class AcceptTildaWebhookResult:
    tilda_job_id: int
    tran_id: str
    duplicate: bool = False
