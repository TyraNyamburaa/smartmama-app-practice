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
        Creates a hosted DocuPass verification link using IDAnalyzer API V2.
        Explicitly handles and raises exceptions on identity provider errors.
        """
        # API V2 utilizes standard Bearer tokens for authentication
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "reference": chv_id,
            "callback_url": callback_url,
            "biometric": 1,
            "max_attempt": 3
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.docupass_endpoint, headers=headers, json=payload)
            
            # Catch standard network/HTTP status errors (e.g., 400, 401, 403, 500)
            resp.raise_for_status()
            
            response_data = resp.json()

            # EXPLICIT ERROR CHECK: Catch successful HTTP transfers that carry internal API failure keys
            if "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown IDAnalyzer error")
                error_code = response_data["error"].get("code", "N/A")
                raise ValueError(f"IDAnalyzer API Error (Code {error_code}): {error_msg}")

            return response_data

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
