import os
import logging
import httpx

logger = logging.getLogger(__name__)

SMSLEOPARD_API_KEY = os.getenv("SMSLEOPARD_API_KEY")
SMSLEOPARD_API_SECRET = os.getenv("SMSLEOPARD_API_SECRET")
SMSLEOPARD_SENDER_ID = os.getenv("SMSLEOPARD_SENDER_ID")
SMSLEOPARD_URL = "https://api.smsleopard.com/v1/sms/send"


async def dispatch_system_sms(destination_phone: str, sms_text: str) -> bool:
    if not SMSLEOPARD_API_KEY or not SMSLEOPARD_API_SECRET:
        logger.error("SMS Leopard credentials missing.")
        return False

    clean_phone = destination_phone.replace("+", "").strip()
    payload = {
        "source": SMSLEOPARD_SENDER_ID,
        "message": sms_text,
        "destination": [{"number": clean_phone}],
        "status_url": "",
        "status_secret": "",
    }

    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "SmartMama-Backend/1.0"}) as client:
        try:
            response = await client.post(
                SMSLEOPARD_URL,
                json=payload,
                auth=(SMSLEOPARD_API_KEY, SMSLEOPARD_API_SECRET),
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            error_body = getattr(e.response, "text", "") if hasattr(e, "response") else ""
            logger.error(f"SMS Leopard network request failed: {e}. Details: {error_body}")
            return False

        try:
            data = response.json()
        except ValueError:
            logger.error(f"SMS Leopard returned a non-JSON response: {response.text}")
            return False

        if not data.get("success", False):
            logger.error(f"SMS Leopard rejected the message: {data}")
            return False

        masked_phone = clean_phone[-4:] if len(clean_phone) >= 4 else clean_phone
        logger.info(f"SMS Leopard accepted message for{masked_phone}: {data}")
        return True


def dispatch_system_sms_sync(destination_phone: str, sms_text: str) -> bool:
    if not SMSLEOPARD_API_KEY or not SMSLEOPARD_API_SECRET:
        logger.error("SMS Leopard credentials missing.")
        return False

    clean_phone = destination_phone.replace("+", "").strip()
    payload = {
        "source": SMSLEOPARD_SENDER_ID,
        "message": sms_text,
        "destination": [{"number": clean_phone}],
        "status_url": "",
        "status_secret": "",
    }

    with httpx.Client(timeout=10.0, headers={"User-Agent": "SmartMama-Backend/1.0"}) as client:
        try:
            response = client.post(
                SMSLEOPARD_URL,
                json=payload,
                auth=(SMSLEOPARD_API_KEY, SMSLEOPARD_API_SECRET),
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            error_body = getattr(e.response, "text", "") if hasattr(e, "response") else ""
            logger.error(f"SMS Leopard network request failed: {e}. Details: {error_body}")
            return False

        try:
            data = response.json()
        except ValueError:
            logger.error(f"SMS Leopard returned a non-JSON response: {response.text}")
            return False

        if not data.get("success", False):
            logger.error(f"SMS Leopard rejected the message: {data}")
            return False

        masked_phone = clean_phone[-4:] if len(clean_phone) >= 4 else clean_phone
        logger.info(f"SMS Leopard accepted message for{masked_phone}: {data}")
        return True


def build_risk_assessment_sms(mother_name: str, portal_url: str) -> str:
    return (
        f"Dear {mother_name}, your maternal risk assessment report is ready. "
        f"Use your PIN to access it here: {portal_url}"
    )
    