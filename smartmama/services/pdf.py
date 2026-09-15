import logging
import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from smartmama.security import verify_password
from database import get_db

logger = logging.getLogger("smartmama.audit")

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 6

STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "storage",
    "assessments",
)


class PdfService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _validate_pin(pin: str, label: str, client_ip: Optional[str]) -> None:
        if not (
            isinstance(pin, str)
            and pin.isdigit()
            and PIN_MIN_LENGTH <= len(pin) <= PIN_MAX_LENGTH
        ):
            logger.warning(
                "%s denied reason=invalid_pin_format ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"PIN must be {PIN_MIN_LENGTH} to {PIN_MAX_LENGTH} digits",
            )

    @staticmethod
    def _safe_filename(
        filename: str, label: str, client_ip: Optional[str]
    ) -> str:
        safe = os.path.basename(filename)
        if not safe or safe != filename:
            logger.warning(
                "%s denied reason=invalid_filename ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename",
            )
        return safe

    @staticmethod
    def serve_pdf_file(safe_filename: str):
        file_path = os.path.join(STORAGE_DIR, safe_filename)
        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=404,
                detail="PDF file not found",
            )
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"risk_report_{safe_filename}",
            headers={"Content-Disposition": f'attachment; filename="risk_report_{safe_filename}"'},
        )

    def _find_report_by_risk_id(self, risk_id: str):
        return self.db.execute(
            text(
                """
                SELECT
                    r.risk_id,
                    r.link_url,
                    r.pdf_password,
                    m.hashed_pin
                FROM risk_assessments r
                JOIN mothers m
                    ON m.mother_id = r.mother_id
                WHERE r.risk_id = :risk_id
                """
            ),
            {"risk_id": risk_id},
        ).mappings().first()

    def _find_report_by_filename(self, safe_filename: str):
        return self.db.execute(
            text(
                """
                SELECT
                    r.risk_id,
                    r.link_url,
                    r.pdf_password,
                    m.hashed_pin
                FROM risk_assessments r
                JOIN mothers m
                    ON m.mother_id = r.mother_id
                WHERE r.link_url LIKE :file_match
                """
            ),
            {"file_match": f"%{safe_filename}%"},
        ).mappings().first()

    @staticmethod
    def _build_portal_url(link_url: str) -> str:
        base_url = os.getenv("PUBLIC_API_BASE_URL")
        if not base_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PUBLIC_API_BASE_URL is not configured",
            )
        filename = os.path.basename(link_url)
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid PDF report reference",
            )
        return f"{base_url.rstrip('/')}/portal/view/{quote(filename)}"


    def _consume_pin(
        self,
        record,
        pin: str,
        label: str,
        client_ip: Optional[str],
    ) -> str:
        risk_id = record["risk_id"]

        if record["pdf_password"]:
            logger.warning(
                "%s denied risk_id=%s reason=already_accessed ip=%s",
                label,
                risk_id,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This report has already been accessed",
            )

        if not record["hashed_pin"]:
            logger.warning(
                "%s denied risk_id=%s reason=pin_not_configured ip=%s",
                label,
                risk_id,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="PIN verification is not available",
            )

        if not verify_password(pin, record["hashed_pin"]):
            logger.warning(
                "%s denied risk_id=%s reason=invalid_pin ip=%s",
                label,
                risk_id,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN",
            )

        if not record["link_url"]:
            logger.warning(
                "%s denied risk_id=%s reason=pdf_not_found ip=%s",
                label,
                risk_id,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF report not found",
            )

        self.db.execute(
            text(
                """
                UPDATE risk_assessments
                SET pdf_password = :accessed_at
                WHERE risk_id = :risk_id
                """
            ),
            {
                "accessed_at": datetime.now(timezone.utc).isoformat(),
                "risk_id": risk_id,
            },
        )
        self.db.commit()

        logger.info(
            "%s success risk_id=%s ip=%s",
            label,
            risk_id,
            client_ip,
        )
        return self._build_portal_url(record["link_url"])

    def verify_pin_and_get_link(
        self,
        risk_id: str,
        pin: str,
        client_ip: Optional[str] = None,
    ) -> str:
        label = "pdf_verify_pin"
        self._validate_pin(pin, label, client_ip)
        record = self._find_report_by_risk_id(risk_id)
        if record is None:
            logger.warning(
                "%s denied reason=record_not_found ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk assessment not found",
            )
        return self._consume_pin(record, pin, label, client_ip)

    def verify_pin_by_filename(
        self,
        filename: str,
        pin: str,
        client_ip: Optional[str] = None,
    ) -> str:
        label = "portal_verify_pin"
        self._validate_pin(pin, label, client_ip)
        safe_filename = self._safe_filename(filename, label, client_ip)
        record = self._find_report_by_filename(safe_filename)
        if record is None:
            logger.warning(
                "%s denied reason=record_not_found ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Smartmama record not found",
            )
        return self._consume_pin(record, pin, label, client_ip)

    def verify_pin_for_month_portal(self, year: int, month: int, pin: str, client_ip: Optional[str] = None):
        label = "portal_month_pin"
        self._validate_pin(pin, label, client_ip)

        mother = self.db.execute(
            text(
                """
                SELECT mother_id, first_name, last_name, hashed_pin
                FROM mothers
                WHERE hashed_pin IS NOT NULL
                """
            )
        ).mappings().all()

        matched_mother = None
        for m in mother:
            if verify_password(pin, m["hashed_pin"]):
                matched_mother = m
                break

        if not matched_mother:
            logger.warning(
                "%s denied reason=invalid_pin ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN",
            )

        mother_id = matched_mother["mother_id"]
        pdfs = self.db.execute(
            text(
                """
                SELECT
                    r.risk_id,
                    r.link_url,
                    r.risk_level,
                    r.created_at
                FROM risk_assessments r
                WHERE r.mother_id = :mother_id
                AND extract(year FROM r.created_at) = :year
                AND extract(month FROM r.created_at) = :month
                ORDER BY r.created_at DESC
                """
            ),
            {"mother_id": mother_id, "year": year, "month": month},
        ).mappings().all()

        pdf_list = []
        for pdf in pdfs:
            pdf_list.append({
                "risk_id": str(pdf["risk_id"]),
                "filename": os.path.basename(pdf["link_url"]) if pdf["link_url"] else None,
                "risk_level": pdf["risk_level"],
                "created_at": pdf["created_at"].isoformat() if pdf["created_at"] else None,
            })

        logger.info(
            "%s success mother_id=%s ip=%s month=%s-%s pdfs=%d",
            label,
            mother_id,
            client_ip,
            year,
            month,
            len(pdfs),
        )

        return {
            "success": True,
            "mother_id": str(mother_id),
            "mother_name": f"{matched_mother['first_name']} {matched_mother['last_name']}",
            "month": datetime(year, month, 1).strftime("%B %Y"),
            "year": year,
            "month_num": month,
            "pdfs": pdf_list,
        }

    def verify_mother_pin(self, pin: str, client_ip: Optional[str] = None):
        label = "portal_mother_pin"
        self._validate_pin(pin, label, client_ip)

        mother = self.db.execute(
            text(
                """
                SELECT mother_id, first_name, last_name, hashed_pin
                FROM mothers
                WHERE hashed_pin IS NOT NULL
                """
            )
        ).mappings().all()

        matched_mother = None
        for m in mother:
            if verify_password(pin, m["hashed_pin"]):
                matched_mother = m
                break

        if not matched_mother:
            logger.warning(
                "%s denied reason=invalid_pin ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN",
            )

        mother_id = matched_mother["mother_id"]
        from ..repositories import risk_assessment_repository as risk_repo
        pdfs = risk_repo.get_pdfs_by_mother(self.db, mother_id)

        months = {}
        for pdf in pdfs:
            year = int(pdf.year)
            month = int(pdf.month)
            key = f"{year}-{month:02d}"
            if key not in months:
                months[key] = {
                    "year": year,
                    "month": month,
                    "label": f"{datetime(year, month, 1).strftime('%B %Y')}",
                    "pdfs": [],
                }
            months[key]["pdfs"].append({
                "risk_id": str(pdf.risk_id),
                "created_at": pdf.created_at.isoformat() if pdf.created_at else None,
                "risk_level": pdf.risk_level,
                "filename": os.path.basename(pdf.link_url) if pdf.link_url else None,
            })

        month_list = sorted(months.values(), key=lambda x: (x["year"], x["month"]), reverse=True)

        logger.info(
            "%s success mother_id=%s ip=%s pdfs=%d",
            label,
            mother_id,
            client_ip,
            len(pdfs),
        )

        return {
            "success": True,
            "mother_id": str(mother_id),
            "mother_name": f"{matched_mother['first_name']} {matched_mother['last_name']}",
            "months": month_list,
        }

    def get_authorized_report(
        self,
        filename: str,
        client_ip: Optional[str] = None,
    ):
        label = "portal_view"
        safe_filename = self._safe_filename(filename, label, client_ip)
        record = self.db.execute(
            text(
                """
                SELECT
                    r.risk_id,
                    r.link_url,
                    r.pdf_password
                FROM risk_assessments r
                WHERE r.link_url LIKE :file_match
                """
            ),
            {"file_match": f"%{safe_filename}%"},
        ).mappings().first()
        if record is None:
            logger.warning(
                "%s denied reason=record_not_found ip=%s",
                label,
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Smartmama Summary record not found",
            )
        if not record["pdf_password"]:
            logger.warning(
                "%s_unauthorized risk_id=%s ip=%s",
                label,
                record["risk_id"],
                client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="PDF access has not been authorized",
            )
        return record


def get_pdf_service(
    db: Session = Depends(get_db),
) -> PdfService:
    return PdfService(db)
