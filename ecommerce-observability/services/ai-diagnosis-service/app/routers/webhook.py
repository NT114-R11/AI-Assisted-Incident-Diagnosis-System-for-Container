from fastapi import APIRouter

from app.schemas.alertmanager import AlertmanagerWebhook
from app.services.incident import process_alert


router = APIRouter(
    prefix="/webhook",
    tags=["webhook"],
)


@router.post("/alertmanager")
def alertmanager_webhook(payload: AlertmanagerWebhook):
    return process_alert(payload)