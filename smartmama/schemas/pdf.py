from pydantic import BaseModel, SecretStr
from uuid import UUID
from datetime import date


class PinVerificationRequest(BaseModel):
    risk_id: UUID
    pin: SecretStr


class PdfLinkResponse(BaseModel):
    success: bool
    download_url: str


class MotherPinVerificationRequest(BaseModel):
    pin: SecretStr


class MotherPdfItem(BaseModel):
    risk_id: UUID
    created_at: str
    risk_level: str
    filename: str


class MotherMonthItem(BaseModel):
    year: int
    month: int
    label: str
    pdfs: list[MotherPdfItem]


class MotherDashboardResponse(BaseModel):
    success: bool
    mother_id: UUID
    mother_name: str
    months: list[MotherMonthItem]
