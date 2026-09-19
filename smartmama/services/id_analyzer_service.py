import os
import httpx

IDANALYZER_API_KEY = os.getenv("IDANALYZER_API_KEY")
# Base endpoint for Core Scan API
CORE_SCAN_ENDPOINT = "https://idanalyzer.com"
# Dedicated endpoint for DocuPass
DOCUPASS_ENDPOINT = "https://api.idanalyzer.com"

class IDAnalyzerService:
    def __init__(self):
        self.api_key = IDANALYZER_API_KEY
        self.endpoint = CORE_SCAN_ENDPOINT
        self.docupass_endpoint = DOCUPASS_ENDPOINT

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

    # ==================== NEW DOCUPASS METHODS ====================

    async def create_docupass_session(self, chv_id: str, callback_url: str) -> dict:
        """
        Creates a hosted DocuPass verification link for the user.
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "company_name": "SmartMama",
            "reference": chv_id,
            "callback_url": callback_url,
            # 1 = Document verification + Face verification
            "verification_mode": 1, 
            # Forces web-camera liveness scan execution
            "biometric_photo": True,
            "liveness_check": True
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.docupass_endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def parse_docupass_result(self, payload: dict) -> dict:
        """
        Parses incoming payload data delivered by the IDAnalyzer webhooks.
        """
        # IDAnalyzer returns 'status' as 1 for a successful, authentic user match
        success_status = payload.get("status")
        
        return {
            "is_approved": str(success_status) == "1",
            "document_type": payload.get("documentType"),
            "raw": payload
        }


id_analyzer_service = IDAnalyzerService()
