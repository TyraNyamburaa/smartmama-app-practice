from fastapi import APIRouter, Depends, Request

from smartmama.schemas.pdf import (
    PinVerificationRequest,
    PdfLinkResponse,
    MotherPinVerificationRequest,
    MotherDashboardResponse,
)
from smartmama.services.pdf import (
    PdfService,
    get_pdf_service,
)


router = APIRouter(
    prefix="/pdf",
    tags=["PDF"],
)


@router.post(
    "/verify-pin",
    response_model=PdfLinkResponse,
)
def verify_pin(
    request: Request,
    payload: PinVerificationRequest,
    pdf_service: PdfService = Depends(get_pdf_service),
):
    client_ip = request.client.host if request.client else None
    download_url = pdf_service.verify_pin_and_get_link(
        risk_id=str(payload.risk_id),
        pin=payload.pin.get_secret_value(),
        client_ip=client_ip,
    )
    return PdfLinkResponse(
        success=True,
        download_url=download_url,
    )


@router.post(
    "/verify-mother-pin",
    response_model=MotherDashboardResponse,
)
def verify_mother_pin(
    request: Request,
    payload: MotherPinVerificationRequest,
    pdf_service: PdfService = Depends(get_pdf_service),
):
    client_ip = request.client.host if request.client else None
    result = pdf_service.verify_mother_pin(
        pin=payload.pin.get_secret_value(),
        client_ip=client_ip,
    )
    return MotherDashboardResponse(**result)
