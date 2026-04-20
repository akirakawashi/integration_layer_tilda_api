from fastapi import APIRouter, Depends, Request, status

router = APIRouter(tags=["tilda"])

@router.post(
    "/webhooks/tilda",
    summary="Accept Tilda webhook",
)
async def accept_tilda_webhook(
    request: Request,
):
    return {"message": "Tilda webhook received successfully"}