import os

import httpx
from dotenv import load_dotenv

from app.schemas.diagnosis_result import DiagnosisResult

load_dotenv()


class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

        if not self.chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID is not configured")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, message: str) -> None:
        url = f"{self.base_url}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

        response.raise_for_status()

    async def send_diagnosis(self, diagnosis: DiagnosisResult) -> None:
        message = (
            "INCIDENT DETECTED\n\n"
            f"Service: {diagnosis.affected_service}\n"
            f"Root Cause: {diagnosis.root_cause}\n\n"
            f"Explanation:\n{diagnosis.explanation}\n\n"
            "Evidence:\n"
            + "\n".join(f"• {item}" for item in diagnosis.evidence)
            + "\n\n"
            f"Confidence: {diagnosis.confidence:.1%}\n\n"
            f"Impact:\n{diagnosis.impact}\n\n"
            "Recommendations:\n"
            + "\n".join(
                f"• {item}" for item in diagnosis.recommendations
            )
        )
        await self.send_message(message)

    async def send_resolved(self,service: str,alertname: str | None = None,) -> None:
        message = (
            "INCIDENT RESOLVED\n\n"
            f"Service: {service}\n"
            f"Alert: {alertname or 'unknown'}\n\n"
            "The service has recovered and the alert is no longer firing."
        )
        await self.send_message(message)