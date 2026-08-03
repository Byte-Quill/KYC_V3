from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Assignment, Maddie, Task, User


def make_user(email, role, manager=None, password="Passw0rd!x"):
    u = User(email=email, username=email.split("@")[0], role=role, manager=manager)
    u.set_password(password)
    u.save()
    return u


class BaseCase(APITestCase):
    def setUp(self):
        self.ceo = make_user("ceo@x.com", User.Role.CEO)
        self.superadmin = make_user("sa@x.com", User.Role.SUPERADMIN, manager=self.ceo)
        self.admin = make_user("admin@x.com", User.Role.ADMIN, manager=self.superadmin)
        self.employee = make_user("emp@x.com", User.Role.EMPLOYEE, manager=self.admin)

    def login(self, user, password="Passw0rd!x"):
        res = self.client.post(reverse("token_obtain_pair"), {"email": user.email, "password": password})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")


class AuthTests(BaseCase):
    def test_login_and_me(self):
        self.login(self.employee)
        res = self.client.get(reverse("me"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["role"], "employee")

    def test_me_requires_auth(self):
        res = self.client.get(reverse("me"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class RoleHierarchyTests(BaseCase):
    def test_admin_cannot_create_superadmin(self):
        self.login(self.admin)
        res = self.client.post("/api/users/", {
            "email": "x@x.com", "username": "x", "password": "Passw0rd!x",
            "role": User.Role.SUPERADMIN,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_create_employee(self):
        self.login(self.admin)
        res = self.client.post("/api/users/", {
            "email": "new@x.com", "username": "new", "password": "Passw0rd!x",
            "role": User.Role.EMPLOYEE,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_employee_cannot_create_users(self):
        self.login(self.employee)
        res = self.client.post("/api/users/", {
            "email": "y@x.com", "username": "y", "password": "Passw0rd!x",
            "role": User.Role.EMPLOYEE,
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class MaddieTests(BaseCase):
    def test_employee_cannot_create_maddie(self):
        self.login(self.employee)
        res = self.client.post("/api/maddies/", {"full_name": "Test Maddie"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_maddie(self):
        self.login(self.admin)
        res = self.client.post("/api/maddies/", {"full_name": "Test Maddie", "hourly_rate": 100})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_assignment_marks_maddie_assigned(self):
        maddie = Maddie.objects.create(full_name="M", managed_by=self.admin)
        self.login(self.admin)
        res = self.client.post("/api/assignments/", {
            "maddie": str(maddie.id), "client_name": "Client", "start_date": "2026-08-01",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        maddie.refresh_from_db()
        self.assertEqual(maddie.status, Maddie.Status.ASSIGNED)


class DashboardTests(BaseCase):
    def test_each_role_gets_own_dashboard(self):
        for user, expected_scope in [
            (self.ceo, "organization"),
            (self.superadmin, "operations"),
            (self.admin, "team"),
            (self.employee, "workspace"),
        ]:
            self.login(user)
            res = self.client.get(reverse("dashboard"))
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data["scope"], expected_scope)
            self.assertIn("stats", res.data)

    def test_employee_dashboard_shows_own_tasks(self):
        Task.objects.create(title="My task", owner=self.employee)
        Task.objects.create(title="Other task", owner=self.admin)
        self.login(self.employee)
        res = self.client.get(reverse("dashboard"))
        self.assertEqual(res.data["stats"]["my_tasks"], 1)
