import uuid
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import httpx
import pyotp

import main
from database import SessionLocal
from smartmama.models.person_model import Person
from smartmama.models.user_model import User
from smartmama.models.chv import CHV
from smartmama.models.supervisor_model import Supervisor
from smartmama.security import hash_password, create_access_token, create_mfa_challenge_token

client = TestClient(main.app)


def _create_person(db: Session, **overrides) -> Person:
    data = {
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+254700000000",
        "location_name": "Nairobi",
        "profile_photo_url": None,
    }
    data.update(overrides)
    p = Person(**data)
    db.add(p)
    db.flush()
    return p


def _create_user(db: Session, role: str = "chv", **overrides) -> User:
    person = _create_person(db, **overrides.pop("person_overrides", {}))
    data = {
        "person_id": person.person_id,
        "email": f"{role}_{uuid.uuid4().hex[:6]}@test.com",
        "hashed_password": hash_password("password123"),
        "role": role,
        "is_active": True,
        "mfa_secret": None,
        "mfa_enabled": False,
        "last_login_at": None,
    }
    data.update(overrides)
    user = User(**data)
    db.add(user)
    db.flush()
    return user


def _auth_headers(user_id: uuid.UUID, role: str) -> dict:
    token = create_access_token(str(user_id), role)
    return {"Authorization": f"Bearer {token}"}


class TestAuthEndpoints:
    def test_chv_login_returns_token_and_user(self):
        db = SessionLocal()
        try:
            user = _create_user(db, role="chv")
            from smartmama.models.chv import CHV
            chv = CHV(user_id=user.user_id, certificate_status="Pending")
            db.add(chv)
            db.commit()
            r = client.post("/api/v1/auth/chv/login", json={
                "email": user.email,
                "password": "password123",
            })
            assert r.status_code == 200, r.text
            body = r.json()
            assert "access_token" in body
            assert body["user"]["chv_id"] is not None
            assert body["user"]["email"] == user.email
        finally:
            db.close()

    def test_chv_login_wrong_password(self):
        db = SessionLocal()
        try:
            user = _create_user(db, role="chv")
            db.commit()
            r = client.post("/api/v1/auth/chv/login", json={
                "email": user.email,
                "password": "wrong",
            })
            assert r.status_code == 401
        finally:
            db.close()

    def test_chv_signup_returns_profile(self):
        r = client.post("/api/v1/auth/chv/signup", json={
            "first_name": "Alice",
            "last_name": "CHV",
            "email": f"chv_{uuid.uuid4().hex[:6]}@test.com",
            "phone_number": "+254711111111",
            "password": "StrongPass1!",
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert "chv_id" in body
        assert body["certificate_status"] == "Pending"

    def test_login_wrong_password_returns_401(self):
        db = SessionLocal()
        try:
            user = _create_user(db, role="chv")
            db.commit()
            r = client.post("/api/v1/auth/login", json={
                "email": user.email,
                "password": "wrongpass",
            })
            assert r.status_code == 401
        finally:
            db.close()

    def test_login_mfa_required_returns_challenge(self):
        db = SessionLocal()
        try:
            secret = pyotp.random_base32()
            user = _create_user(db, role="chv", mfa_enabled=True, mfa_secret=secret)
            db.commit()
            r = client.post("/api/v1/auth/login", json={
                "email": user.email,
                "password": "password123",
            })
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["mfa_required"] is True
            assert "challenge_token" in body
        finally:
            db.close()

    def test_mfa_verify_success(self):
        db = SessionLocal()
        try:
            secret = pyotp.random_base32()
            user = _create_user(db, role="chv", mfa_enabled=True, mfa_secret=secret)
            db.commit()
            challenge = create_mfa_challenge_token(str(user.user_id))
            code = pyotp.TOTP(secret).now()
            r = client.post("/api/v1/auth/mfa/verify", json={
                "challenge_token": challenge,
                "code": code,
            })
            assert r.status_code == 200, r.text
            assert "access_token" in r.json()
        finally:
            db.close()

    def test_forgot_password_returns_message(self):
        db = SessionLocal()
        try:
            user = _create_user(db, role="chv")
            db.commit()
            with patch("smartmama.services.auth_service.dispatch_system_sms_sync", return_value=True):
                r = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
            assert r.status_code == 200, r.text
            assert "message" in r.json()
        finally:
            db.close()

    def test_logout_revokes_token(self):
        db = SessionLocal()
        try:
            user = _create_user(db, role="chv")
            db.commit()
            token = create_access_token(str(user.user_id), "chv")
            r = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 200, r.text
        finally:
            db.close()


class TestCHVEndpoints:
    def test_chv_profile_requires_auth(self):
        r = client.get("/api/v1/auth/chv/current")
        assert r.status_code == 401

    def test_chv_login_returns_valid_token(self):
        db = SessionLocal()
        try:
            user = _create_user(db, role="chv")
            from smartmama.models.chv import CHV
            chv = CHV(user_id=user.user_id, certificate_status="Pending")
            db.add(chv)
            db.commit()
            r = client.post("/api/v1/auth/chv/login", json={
                "email": user.email,
                "password": "password123",
            })
            assert r.status_code == 200
            body = r.json()
            assert "access_token" in body
            assert "user" in body
            assert body["user"]["email"] == user.email
        finally:
            db.close()


class TestSupervisorEndpoints:
    def test_list_supervisors_requires_admin(self):
        r = client.get("/api/v1/supervisors")
        assert r.status_code == 401

    def test_supervisor_current_requires_auth(self):
        r = client.get("/api/v1/supervisors/current")
        assert r.status_code == 401

    def test_list_chvs_requires_supervisor(self):
        r = client.get("/api/v1/supervisors/chvs")
        assert r.status_code == 401

    def test_list_mothers_requires_supervisor(self):
        r = client.get("/api/v1/supervisors/mothers")
        assert r.status_code == 401

    def test_list_pending_chvs_requires_supervisor(self):
        r = client.get("/api/v1/supervisors/chv-verifications")
        assert r.status_code == 401

    def test_verify_chv_requires_supervisor(self):
        r = client.patch(
            "/api/v1/supervisors/chv-verifications/00000000-0000-0000-0000-000000000000",
            params={"decision": "approve"},
        )
        assert r.status_code == 401

    def test_verify_chv_rejects_invalid_decision(self):
        db = SessionLocal()
        try:
            sup = _create_user(db, role="supervisor")
            sup_profile = Supervisor(user_id=sup.user_id)
            db.add(sup_profile)
            db.commit()
            chv = _create_user(db, role="chv")
            chv_profile = CHV(user_id=chv.user_id, certificate_status="Pending")
            db.add(chv_profile)
            db.commit()
            r = client.patch(
                f"/api/v1/supervisors/chv-verifications/{chv_profile.chv_id}",
                params={"decision": "invalid"},
                headers=_auth_headers(sup.user_id, "supervisor"),
            )
            assert r.status_code == 400, r.text
        finally:
            db.close()

    def test_verify_chv_approve_returns_updated(self):
        db = SessionLocal()
        try:
            sup = _create_user(db, role="supervisor")
            sup_profile = Supervisor(user_id=sup.user_id)
            db.add(sup_profile)
            db.commit()
            chv = _create_user(db, role="chv")
            chv_profile = CHV(user_id=chv.user_id, certificate_status="Pending")
            db.add(chv_profile)
            db.commit()
            r = client.patch(
                f"/api/v1/supervisors/chv-verifications/{chv_profile.chv_id}",
                params={"decision": "approve"},
                headers=_auth_headers(sup.user_id, "supervisor"),
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["certificate_status"] == "Verified"
            assert body["verified_by"] == str(sup_profile.supervisor_id)
            assert body["verified_at"] is not None
        finally:
            db.close()

    def test_verify_chv_reject_returns_rejection(self):
        db = SessionLocal()
        try:
            sup = _create_user(db, role="supervisor")
            sup_profile = Supervisor(user_id=sup.user_id)
            db.add(sup_profile)
            db.commit()
            chv = _create_user(db, role="chv")
            chv_profile = CHV(user_id=chv.user_id, certificate_status="Pending")
            db.add(chv_profile)
            db.commit()
            r = client.patch(
                f"/api/v1/supervisors/chv-verifications/{chv_profile.chv_id}",
                params={"decision": "reject", "rejection_notes": "Bad cert"},
                headers=_auth_headers(sup.user_id, "supervisor"),
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["certificate_status"] == "Rejected"
            assert body["rejection_notes"] == "Bad cert"
        finally:
            db.close()


class TestAdminEndpoints:
    def test_invite_requires_super_admin(self):
        r = client.post("/api/v1/admins/invite", json={
            "first_name": "X", "last_name": "Y", "email": "x@test.com",
            "phone_number": "+254700000000", "password": "StrongPass1!",
        })
        assert r.status_code == 401

    def test_list_admins_requires_super_admin(self):
        r = client.get("/api/v1/admins")
        assert r.status_code == 401


class TestTicketEndpoints:
    def test_list_tickets_requires_admin(self):
        r = client.get("/api/v1/tickets")
        assert r.status_code == 401

    def test_raise_ticket_requires_auth(self):
        r = client.post("/api/v1/tickets", json={
            "description": "Test ticket",
            "raised_by_type": "chv",
            "raised_by_id": str(uuid.uuid4()),
        })
        assert r.status_code == 401

    def test_top_solvers_requires_admin(self):
        r = client.get("/api/v1/tickets/top-solvers")
        assert r.status_code == 401


class TestAuditLogEndpoints:
    def test_audit_logs_requires_admin(self):
        r = client.get("/api/v1/admin/logs/audit")
        assert r.status_code == 401


class TestLocationEndpoints:
    def test_create_location(self):
        r = client.post("/api/v1/locations/", json={
            "location_name": "Kibera",
            "latitude": -1.313,
            "longitude": 36.789,
        })
        assert r.status_code == 201, r.text

    def test_list_locations(self):
        r = client.get("/api/v1/locations/")
        assert r.status_code == 200


class TestVisitEndpoints:
    def test_create_visit_requires_auth(self):
        r = client.post("/api/v1/visits", json={
            "mother_id": str(uuid.uuid4()),
            "visit_date": "2024-01-01",
            "notes": "Routine",
        })
        assert r.status_code == 401


class TestPregnancyEndpoints:
    def test_create_pregnancy_returns_expected_status(self):
        mother_id = uuid.uuid4()
        r = client.post("/api/v1/pregnancies/", json={
            "mother_id": str(mother_id),
            "last_menstrual_period": "2024-01-01",
            "expected_delivery_date": "2024-10-01",
            "pregnancy_status": "active",
            "gestational_age": 12,
            "parity": 0,
        })
        assert r.status_code in (200, 201, 404), r.text


class TestRiskAssessmentEndpoints:
    def test_create_risk_assessment_returns_expected_status(self):
        r = client.post("/api/v1/risk-assessments/", json={
            "pregnancy_id": str(uuid.uuid4()),
            "visit_id": str(uuid.uuid4()),
            "risk_level": "low",
            "confidence_score": 0.95,
        })
        assert r.status_code in (200, 201, 404), r.text


class TestPortalAndPdf:
    def test_verify_pin_returns_422_without_pin(self):
        r = client.post("/api/v1/pdf/verify-pin", json={})
        assert r.status_code == 422

    def test_verify_mother_pin_returns_422_without_pin(self):
        r = client.post("/api/v1/pdf/verify-mother-pin", json={})
        assert r.status_code == 422


class TestThirdPartyIntegrations:
    def test_sms_send_success(self):
        from smartmama.services.sms_service import dispatch_system_sms_sync
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"success": True}
        with patch("httpx.Client.post", return_value=mock_resp):
            result = dispatch_system_sms_sync("+254700000000", "Hello")
        assert result is True

    def test_sms_send_failure_returns_false(self):
        from smartmama.services.sms_service import dispatch_system_sms_sync
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPError("boom")
        mock_resp.response.text = "error"
        with patch("httpx.Client.post", return_value=mock_resp):
            result = dispatch_system_sms_sync("+254700000000", "Hello")
        assert result is False

    def test_idanalyzer_docupass_mocked(self):
        import asyncio
        from smartmama.services.id_analyzer_service import id_analyzer_service
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"url": "https://example.com", "reference": "abc123"}
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            result = asyncio.get_event_loop().run_until_complete(
                id_analyzer_service.create_docupass_session("chv1", "https://callback")
            )
        assert result["reference"] == "abc123"

    def test_attachment_scanner_mocked(self):
        import asyncio
        from smartmama.services.attachment_scanner_service import attachment_scanner_service
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        mock_resp.json.return_value = {"status": "completed", "malicious": False}
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            result = asyncio.get_event_loop().run_until_complete(
                attachment_scanner_service.scan_file_url("https://example.com/file.pdf")
            )
        assert attachment_scanner_service.is_file_safe(result) is True

        mock_resp2 = MagicMock()
        mock_resp2.raise_for_status.return_value = None
        mock_resp2.json.return_value = {"status": "completed", "malicious": True}
        with patch("httpx.AsyncClient.post", return_value=mock_resp2):
            result2 = asyncio.get_event_loop().run_until_complete(
                attachment_scanner_service.scan_file_url("https://example.com/bad.exe")
            )
        assert attachment_scanner_service.is_file_safe(result2) is False
