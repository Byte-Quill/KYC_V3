"""Seed demo users and a sample application for local development."""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from kyc.models import AuditLog, KYCApplication

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users (admin/reviewer/applicant) and a sample application."

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            email="admin@kyc.local",
            defaults={
                "username": "admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("Admin@123")
            admin.save()

        reviewer, created = User.objects.get_or_create(
            email="reviewer@kyc.local",
            defaults={"username": "reviewer", "role": User.Role.REVIEWER, "is_staff": True},
        )
        if created:
            reviewer.set_password("Review@123")
            reviewer.save()

        applicant, created = User.objects.get_or_create(
            email="user@kyc.local",
            defaults={"username": "applicant", "role": User.Role.APPLICANT},
        )
        if created:
            applicant.set_password("User@123")
            applicant.save()

        if not applicant.applications.exists():
            app = KYCApplication.objects.create(
                applicant=applicant,
                full_name="Demo Applicant",
                date_of_birth=date(1990, 1, 15),
                nationality="Indian",
                phone="+91-9876543210",
                address_line1="221B Baker Street",
                city="Mumbai",
                state="Maharashtra",
                postal_code="400001",
                country="India",
                id_type=KYCApplication.IDType.PASSPORT,
                id_number="A1234567",
                id_expiry=date(2030, 12, 31),
            )
            AuditLog.objects.create(
                application=app, actor=applicant, action=AuditLog.Action.CREATED
            )
            self.stdout.write(self.style.SUCCESS("Created sample draft application."))

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("  admin@kyc.local / Admin@123")
        self.stdout.write("  reviewer@kyc.local / Review@123")
        self.stdout.write("  user@kyc.local / User@123")
