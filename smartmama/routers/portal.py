from fastapi import APIRouter, Depends, Form, Request
from pydantic import SecretStr
from smartmama.services.pdf import PdfService, get_pdf_service
from pydantic import BaseModel
from ..schemas.pdf import PdfLinkResponse, MotherPinVerificationRequest



router = APIRouter(
    prefix="/portal",
    tags=["PDF Portal Access Engine"],
)


class MonthPinRequest(BaseModel):
    pin: str


@router.get("/view/{filename}")
def view_pdf(
    request: Request,
    filename: str,
    pdf_service: PdfService = Depends(get_pdf_service),
):
    client_ip = request.client.host if request.client else None
    record = pdf_service.get_authorized_report(
        filename=filename,
        client_ip=client_ip,
    )
    return pdf_service.serve_pdf_file(record["link_url"].rsplit("/", 1)[-1])


@router.post(
    "/verify/{filename}",
    response_model=PdfLinkResponse,
)
def verify_pin(
    request: Request,
    filename: str,
    pin: SecretStr = Form(...),
    pdf_service: PdfService = Depends(get_pdf_service),
):
    client_ip = request.client.host if request.client else None
    download_url = pdf_service.verify_pin_by_filename(
        filename=filename,
        pin=pin.get_secret_value(),
        client_ip=client_ip,
    )
    return PdfLinkResponse(
        success=True,
        download_url=download_url,
    )


@router.post("/month/{year}/{month}/verify-pin")
def verify_month_pin(
    request: Request,
    year: int,
    month: int,
    payload: MonthPinRequest,
    pdf_service: PdfService = Depends(get_pdf_service),
):
    client_ip = request.client.host if request.client else None
    result = pdf_service.verify_pin_for_month_portal(
        year=year,
        month=month,
        pin=payload.pin,
        client_ip=client_ip,
    )
    return result
