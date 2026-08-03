import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Platform user with a role in the hierarchy CEO > Superadmin > Admin > Employee."""

    class Role(models.TextChoices):
        CEO = "ceo", "CEO"
        SUPERADMIN = "superadmin", "Super Admin"
        ADMIN = "admin", "Admin"
        EMPLOYEE = "employee", "Employee"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    phone = models.CharField(max_length=32, blank=True)
    # Admins/employees belong to a manager higher up the hierarchy.
    manager = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="team"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    # Role rank: lower number = more privilege.
    ROLE_RANK = {
        Role.CEO: 0,
        Role.SUPERADMIN: 1,
        Role.ADMIN: 2,
        Role.EMPLOYEE: 3,
    }

    @property
    def rank(self) -> int:
        return self.ROLE_RANK.get(self.role, 99)

    @property
    def is_ceo(self) -> bool:
        return self.role == self.Role.CEO

    @property
    def is_superadmin(self) -> bool:
        return self.role == self.Role.SUPERADMIN

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    def can_manage(self, other: "User") -> bool:
        """True if this user outranks `other` (strictly higher privilege)."""
        return self.rank < other.rank

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"


class Maddie(models.Model):
    """A maid / domestic worker managed by the platform."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ASSIGNED = "assigned", "Assigned"
        ON_LEAVE = "on_leave", "On Leave"
        INACTIVE = "inactive", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    skills = models.CharField(max_length=300, blank=True, help_text="Comma-separated skills")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    photo = models.ImageField(upload_to="maddies/", null=True, blank=True)
    # The admin responsible for this maddie.
    managed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="maddies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self) -> str:
        return self.full_name


class Assignment(models.Model):
    """Assigns a Maddie to a client location, owned by an employee."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maddie = models.ForeignKey(Maddie, on_delete=models.CASCADE, related_name="assignments")
    client_name = models.CharField(max_length=200)
    client_address = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    # The employee who owns this assignment.
    assigned_to = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assignments"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

    def __str__(self) -> str:
        return f"{self.maddie} → {self.client_name}"


class Task(models.Model):
    """A work item in an employee's workspace."""

    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    assignment = models.ForeignKey(
        Assignment, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "due_date"]

    def __str__(self) -> str:
        return self.title


class ActivityLog(models.Model):
    """Audit trail of important actions, shown on dashboards."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="activities")
    action = models.CharField(max_length=100)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.actor} {self.action}"
