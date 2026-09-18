import os
import httpx

IDANALYZER_API_KEY = os.getenv("IDANALYZER_API_KEY")
CORE_SCAN_ENDPOINT = "https://idanalyzer.com"

class IDAnalyzerService:
    def __init__(self):
        self.api_key = IDANALYZER_API_KEY
        self.endpoint = CORE_SCAN_ENDPOINT

    async def verify_user_identity(self, chv_id: str, document_base64: str, face_base64: str):
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "document": document_base64,
            "face": face_base64,
            "reference": chv_id,
            "verify_document": True,
            "verify_face": True,
            "output": "json"
        }

        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def parse_verification_result(self, payload: dict):
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
