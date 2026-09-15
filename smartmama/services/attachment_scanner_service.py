import os
import httpx
from typing import Any, Dict

ATTACHMENT_SCANNER_API_KEY = os.getenv("ATTACHMENT_SCANNER_API_KEY")
ATTACHMENT_SCANNER_ENDPOINT = "https://eu-west-1.attachmentscanner.com/v1.0/scans"

class AttachmentScannerService:
    def __init__(self):
        self.api_key = ATTACHMENT_SCANNER_API_KEY
        self.endpoint = ATTACHMENT_SCANNER_ENDPOINT

    async def scan_file_url(self, file_url: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "fileUrl": file_url,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def is_file_safe(self, scan_result: Dict[str, Any]) -> bool:
        status = scan_result.get("status")
        malicious = scan_result.get("malicious", False)

        if status == "completed" and not malicious:
            return True
        return False

attachment_scanner_service = AttachmentScannerService()
