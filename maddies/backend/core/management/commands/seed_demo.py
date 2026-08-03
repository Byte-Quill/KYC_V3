from django.core.management.base import BaseCommand

from core.models import Assignment, Maddie, Task, User


class Command(BaseCommand):
    help = "Seed demo users (one per role), maddies, assignments and tasks."

    def handle(self, *args, **options):
        ceo, _ = User.objects.get_or_create(
            email="ceo@maddies.local",
            defaults={"username": "ceo", "role": User.Role.CEO, "is_staff": True, "is_superuser": True},
        )
        ceo.set_password("Ceo@12345")
        ceo.save()

        superadmin, _ = User.objects.get_or_create(
            email="superadmin@maddies.local",
            defaults={"username": "superadmin", "role": User.Role.SUPERADMIN, "manager": ceo},
        )
        superadmin.set_password("Super@12345")
        superadmin.save()

        admin, _ = User.objects.get_or_create(
            email="admin@maddies.local",
            defaults={"username": "admin", "role": User.Role.ADMIN, "manager": superadmin},
        )
        admin.set_password("Admin@12345")
        admin.save()

        employee, _ = User.objects.get_or_create(
            email="employee@maddies.local",
            defaults={"username": "employee", "role": User.Role.EMPLOYEE, "manager": admin},
        )
        employee.set_password("Employee@123")
        employee.save()

        m1, _ = Maddie.objects.get_or_create(
            full_name="Asha Verma",
            defaults={
                "phone": "9000000001", "skills": "cleaning, cooking",
                "hourly_rate": 150, "managed_by": admin, "status": Maddie.Status.AVAILABLE,
            },
        )
        m2, _ = Maddie.objects.get_or_create(
            full_name="Priya Nair",
            defaults={
                "phone": "9000000002", "skills": "childcare, cooking",
                "hourly_rate": 200, "managed_by": admin, "status": Maddie.Status.AVAILABLE,
            },
        )

        assignment, _ = Assignment.objects.get_or_create(
            maddie=m1, client_name="Sharma Residence",
            defaults={
                "client_address": "12 Lake View Rd", "start_date": "2026-08-01",
                "assigned_to": employee, "status": Assignment.Status.ACTIVE,
            },
        )
        m1.status = Maddie.Status.ASSIGNED
        m1.save(update_fields=["status"])

        Task.objects.get_or_create(
            title="Onboard Asha at Sharma Residence",
            defaults={
                "owner": employee, "assignment": assignment,
                "priority": Task.Priority.HIGH, "status": Task.Status.TODO,
            },
        )
        Task.objects.get_or_create(
            title="Collect monthly timesheet",
            defaults={"owner": employee, "priority": Task.Priority.MEDIUM},
        )

        self.stdout.write(self.style.SUCCESS(
            "Seeded demo data.\n"
            "  ceo@maddies.local / Ceo@12345\n"
            "  superadmin@maddies.local / Super@12345\n"
            "  admin@maddies.local / Admin@12345\n"
            "  employee@maddies.local / Employee@123"
        ))
