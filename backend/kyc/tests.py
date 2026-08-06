from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AuditLog, Document, KYCApplication

User = get_user_model()

APP_PAYLOAD = {
    "full_name": "Jane Doe",
    "date_of_birth": "1992-05-20",
    "nationality": "Indian",
    "phone": "+91-9000000000",
    "address_line1": "1 Main Street",
    "address_line2": "",
    "city": "Pune",
    "state": "Maharashtra",
    "postal_code": "411001",
    "country": "India",
    "id_type": "passport",
    "id_number": "B7654321",
    "id_expiry": "2031-01-01",
}


def make_user(email, role, password="Passw0rd!"):
    return User.objects.create_user(
        email=email, username=email.split("@")[0], password=password, role=role
    )


class AuthTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_register_and_login(self):
        res = self.client.post(
            "/api/auth/register/",
            {"email": "new@kyc.local", "username": "newbie", "password": "Str0ngPass!"},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res = self.client.post(
            "/api/auth/token/", {"email": "new@kyc.local", "password": "Str0ngPass!"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_login_is_rate_limited(self):
        for _ in range(10):
            res = self.client.post(
                "/api/auth/token/",
                {"email": "unknown@kyc.local", "password": "wrong-password"},
            )
            self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS))

        res = self.client.post(
            "/api/auth/token/",
            {"email": "unknown@kyc.local", "password": "wrong-password"},
        )
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_register_is_rate_limited(self):
        for i in range(5):
            res = self.client.post(
                "/api/auth/register/",
                {"email": f"spam{i}@kyc.local", "username": f"spam{i}", "password": "Str0ngPass!"},
            )
            self.assertIn(res.status_code, (status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS))
        res = self.client.post(
            "/api/auth/register/",
            {"email": "spam6@kyc.local", "username": "spam6", "password": "Str0ngPass!"},
        )
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)


class ApplicationFlowTests(APITestCase):
    def setUp(self):
        self.applicant = make_user("user@kyc.local", User.Role.APPLICANT)
        self.other = make_user("other@kyc.local", User.Role.APPLICANT)
        self.reviewer = make_user("rev@kyc.local", User.Role.REVIEWER)

    def auth(self, user, password="Passw0rd!"):
        res = self.client.post("/api/auth/token/", {"email": user.email, "password": password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def create_app(self):
        res = self.client.post("/api/applications/", APP_PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        return res.data["id"]

    def upload_doc(self, app_id):
        file = SimpleUploadedFile("passport.pdf", b"%PDF-1.4 fake", content_type="application/pdf")
        return self.client.post(
            f"/api/applications/{app_id}/documents/",
            {"doc_type": "id_proof", "file": file},
            format="multipart",
        )

    def test_full_approval_flow(self):
        self.auth(self.applicant)
        app_id = self.create_app()

        # cannot submit without documents
        res = self.client.post(f"/api/applications/{app_id}/submit/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.upload_doc(app_id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res = self.client.post(f"/api/applications/{app_id}/submit/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "submitted")

        # applicant cannot review their own application
        res = self.client.post(f"/api/applications/{app_id}/review/", {"decision": "approve"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # reviewer approves
        self.auth(self.reviewer)
        res = self.client.post(f"/api/applications/{app_id}/review/", {"decision": "approve"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "approved")

        # audit trail recorded every step
        res = self.client.get(f"/api/applications/{app_id}/audit/")
        actions = [entry["action"] for entry in res.data]
        self.assertEqual(
            actions,
            ["approved", "submitted", "document_uploaded", "created"],
        )

    def test_rejection_requires_notes(self):
        self.auth(self.applicant)
        app_id = self.create_app()
        self.upload_doc(app_id)
        self.client.post(f"/api/applications/{app_id}/submit/")

        self.auth(self.reviewer)
        res = self.client.post(f"/api/applications/{app_id}/review/", {"decision": "reject"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.post(
            f"/api/applications/{app_id}/review/",
            {"decision": "reject", "notes": "Blurry ID scan"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "rejected")

    def test_applicant_cannot_see_others_applications(self):
        self.auth(self.applicant)
        app_id = self.create_app()

        self.auth(self.other)
        res = self.client.get(f"/api/applications/{app_id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        res = self.client.get("/api/applications/")
        self.assertEqual(len(res.data["results"]), 0)

    def test_list_is_paginated(self):
        self.auth(self.applicant)
        for _ in range(25):
            self.create_app()
        res = self.client.get("/api/applications/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 25)
        self.assertEqual(len(res.data["results"]), 20)
        self.assertIsNotNone(res.data["next"])
        res2 = self.client.get("/api/applications/?page=2")
        self.assertEqual(len(res2.data["results"]), 5)

    def test_reviewer_cannot_patch_applicant_fields(self):
        self.auth(self.applicant)
        app_id = self.create_app()
        self.auth(self.reviewer)
        res = self.client.patch(
            f"/api/applications/{app_id}/",
            {"full_name": "Tampered Name"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_queue_only_for_reviewers(self):
        self.auth(self.applicant)
        self.create_app()
        res = self.client.get("/api/review-queue/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.auth(self.reviewer)
        res = self.client.get("/api/review-queue/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_invalid_file_type_rejected(self):
        self.auth(self.applicant)
        app_id = self.create_app()
        file = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")
        res = self.client.post(
            f"/api/applications/{app_id}/documents/",
            {"doc_type": "id_proof", "file": file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_content_mismatch_rejected(self):
        """An executable renamed to .pdf must be rejected by content sniffing."""
        self.auth(self.applicant)
        app_id = self.create_app()
        file = SimpleUploadedFile("fake.pdf", b"MZ\x90\x00 executable", content_type="application/pdf")
        res = self.client.post(
            f"/api/applications/{app_id}/documents/",
            {"doc_type": "id_proof", "file": file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oversized_upload_rejected(self):
        self.auth(self.applicant)
        app_id = self.create_app()
        big = SimpleUploadedFile("big.pdf", b"%PDF-1.4 " + b"0" * (6 * 1024 * 1024), content_type="application/pdf")
        res = self.client.post(
            f"/api/applications/{app_id}/documents/",
            {"doc_type": "id_proof", "file": big},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
