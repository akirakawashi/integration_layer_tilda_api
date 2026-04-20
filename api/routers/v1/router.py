from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.provider import DatabaseProvider

router = APIRouter(tags=["tilda"])

@router.post(
    "/webhooks/tilda",
    summary="Accept Tilda webhook",
)
async def accept_tilda_webhook(
    request: Request,
    session: AsyncSession = Depends(DatabaseProvider.get_session)
):
    return {"message": "Tilda webhook received successfully"}
