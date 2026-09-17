import os
import httpx

IDANALYZER_API_KEY = os.getenv("IDANALYZER_API_KEY")
DOCUPASS_ENDPOINT = "https://idanalyzer.com"

class IDAnalyzerService:
    def __init__(self):
        self.api_key = IDANALYZER_API_KEY
        self.endpoint = DOCUPASS_ENDPOINT

    async def create_docupass_session(self, chv_id: str, callback_url: str):
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "reference": chv_id,
            "callback_url": callback_url,
            "output": "json",
            "verify_document": True,
            "verify_face": True,
            "biometric": True,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def parse_docupass_result(self, payload: dict):
        verification = payload.get("verification", {})
        document = verification.get("document", {})
        face = verification.get("face", {})

        return {
            "document_authenticity": document.get("authenticity_score"),
            "face_match_score": face.get("match_score"),
            "liveness_score": face.get("liveness_score"),
            "raw": payload,
        }

id_analyzer_service = IDAnalyzerService()

