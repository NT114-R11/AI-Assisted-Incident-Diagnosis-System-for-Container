import os
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")

        if not self.api_key:
            raise RuntimeError("LLM_API_KEY is not configured")

        self.base_url = os.getenv(
            "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/")

        self.model = os.getenv(
            "LLM_MODEL",
            "gemini-2.5-flash")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url)

    async def diagnose(self,incident: dict[str, Any],correlation: dict[str, Any]) -> str:
        prompt = self._build_prompt(
            incident=incident,
            correlation=correlation,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an incident diagnosis assistant "
                        "for a containerized e-commerce microservice system."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

        return response.choices[0].message.content or ""

    @staticmethod
    def _build_prompt(incident: dict[str, Any],correlation: dict[str, Any]) -> str:
        candidates = correlation.get("root_cause_candidates", [])
        signals = correlation.get("signals", [])

        return f"""
You are an incident diagnosis assistant for a containerized
e-commerce microservice system.

Your job is to explain a deterministic diagnosis produced by
the monitoring system.

IMPORTANT RULES:
- Do not invent evidence.
- Do not claim access to systems you were not given access to.
- Do not replace the deterministic root-cause ranking.
- Use only the incident and correlation data provided below.
- Clearly distinguish confirmed evidence from inference.
- If the top candidate is broad or generic, do not invent a more specific
  cause; explain what the available evidence supports and state the uncertainty.
- Keep the explanation concise and operationally useful.

Incident:
{incident}

Correlation signals:
{signals}

Root-cause candidates:
{candidates}

Provide:
1. The most likely root cause.
2. A concise explanation.
3. The affected service.
4. The operational impact.
5. Recommended next actions.
""".strip()