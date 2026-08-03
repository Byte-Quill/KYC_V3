import logging

from django.db.models import Count, Q, Sum
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivityLog, Assignment, Maddie, Task, User
from .permissions import CanManageUsers, IsAdminOrAbove
from .serializers import (
    ActivityLogSerializer,
    AssignmentSerializer,
    MaddieSerializer,
    TaskSerializer,
    UserCreateSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


def log_activity(actor, action, detail=""):
    ActivityLog.objects.create(actor=actor, action=action, detail=detail)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    """Manage team members. You only see/manage users below your own rank."""

    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer

    def get_queryset(self):
        u = self.request.user
        if u.is_ceo:
            return User.objects.all().order_by("role", "email")
        # See yourself plus everyone strictly below your rank.
        return User.objects.filter(
            Q(id=u.id) | Q(role__in=[r for r, rank in User.ROLE_RANK.items() if rank > u.rank])
        ).order_by("role", "email")

    def get_permissions(self):
        return [CanManageUsers()]

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(self.request.user, "user_created", f"Created {user.email} ({user.role})")


class MaddieViewSet(viewsets.ModelViewSet):
    serializer_class = MaddieSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrAbove()]
        return super().get_permissions()

    def get_queryset(self):
        u = self.request.user
        qs = Maddie.objects.annotate(
            active_count=Count("assignments", filter=Q(assignments__status=Assignment.Status.ACTIVE))
        )
        # Admins see the maddies they manage; higher roles see all.
        if u.is_admin_role:
            return qs.filter(Q(managed_by=u) | Q(managed_by__isnull=True))
        return qs

    def perform_create(self, serializer):
        maddie = serializer.save()
        log_activity(self.request.user, "maddie_created", f"Added maddie {maddie.full_name}")

    def perform_update(self, serializer):
        maddie = serializer.save()
        log_activity(self.request.user, "maddie_updated", f"Updated maddie {maddie.full_name}")


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        u = self.request.user
        qs = Assignment.objects.select_related("maddie", "assigned_to")
        if u.rank <= User.ROLE_RANK[User.Role.ADMIN]:
            return qs
        # Employees see only their own assignments.
        return qs.filter(assigned_to=u)

    def perform_create(self, serializer):
        assignment = serializer.save()
        if assignment.status == Assignment.Status.ACTIVE:
            assignment.maddie.status = Maddie.Status.ASSIGNED
            assignment.maddie.save(update_fields=["status"])
        log_activity(
            self.request.user, "assignment_created",
            f"Assigned {assignment.maddie.full_name} to {assignment.client_name}",
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        assignment = self.get_object()
        assignment.status = Assignment.Status.COMPLETED
        assignment.save(update_fields=["status"])
        assignment.maddie.status = Maddie.Status.AVAILABLE
        assignment.maddie.save(update_fields=["status"])
        log_activity(request.user, "assignment_completed", f"Completed {assignment}")
        return Response(self.get_serializer(assignment).data)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        u = self.request.user
        qs = Task.objects.select_related("owner", "assignment")
        if u.rank <= User.ROLE_RANK[User.Role.ADMIN]:
            return qs
        return qs.filter(owner=u)

    def perform_create(self, serializer):
        task = serializer.save(owner=self.request.user)
        log_activity(self.request.user, "task_created", f"Created task '{task.title}'")

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        """Move a task to the next status: todo -> in_progress -> done."""
        task = self.get_object()
        order = [Task.Status.TODO, Task.Status.IN_PROGRESS, Task.Status.DONE]
        try:
            task.status = order[order.index(task.status) + 1]
        except (ValueError, IndexError):
            return Response({"detail": "Task already done."}, status=status.HTTP_400_BAD_REQUEST)
        task.save(update_fields=["status"])
        return Response(self.get_serializer(task).data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        u = self.request.user
        if u.rank <= User.ROLE_RANK[User.Role.SUPERADMIN]:
            return ActivityLog.objects.select_related("actor")
        return ActivityLog.objects.filter(actor=u).select_related("actor")


class DashboardView(APIView):
    """Role-aware dashboard payload — one endpoint, shape depends on the caller's role."""

    def get(self, request):
        u = request.user
        data = {"role": u.role}

        if u.is_ceo:
            data["scope"] = "organization"
            data["stats"] = {
                "total_users": User.objects.count(),
                "superadmins": User.objects.filter(role=User.Role.SUPERADMIN).count(),
                "admins": User.objects.filter(role=User.Role.ADMIN).count(),
                "employees": User.objects.filter(role=User.Role.EMPLOYEE).count(),
                "total_maddies": Maddie.objects.count(),
                "active_assignments": Assignment.objects.filter(status=Assignment.Status.ACTIVE).count(),
                "revenue_estimate": float(
                    Maddie.objects.filter(status=Maddie.Status.ASSIGNED)
                    .aggregate(total=Sum("hourly_rate"))["total"] or 0
                ),
            }
            data["recent_activity"] = ActivityLogSerializer(
                ActivityLog.objects.select_related("actor")[:10], many=True
            ).data

        elif u.is_superadmin:
            data["scope"] = "operations"
            data["stats"] = {
                "admins": User.objects.filter(role=User.Role.ADMIN).count(),
                "employees": User.objects.filter(role=User.Role.EMPLOYEE).count(),
                "total_maddies": Maddie.objects.count(),
                "available_maddies": Maddie.objects.filter(status=Maddie.Status.AVAILABLE).count(),
                "active_assignments": Assignment.objects.filter(status=Assignment.Status.ACTIVE).count(),
                "open_tasks": Task.objects.exclude(status=Task.Status.DONE).count(),
            }
            data["maddies_by_status"] = list(
                Maddie.objects.values("status").annotate(count=Count("id"))
            )
            data["recent_activity"] = ActivityLogSerializer(
                ActivityLog.objects.select_related("actor")[:10], many=True
            ).data

        elif u.is_admin_role:
            my_maddies = Maddie.objects.filter(managed_by=u)
            data["scope"] = "team"
            data["stats"] = {
                "my_maddies": my_maddies.count(),
                "available": my_maddies.filter(status=Maddie.Status.AVAILABLE).count(),
                "assigned": my_maddies.filter(status=Maddie.Status.ASSIGNED).count(),
                "team_members": User.objects.filter(manager=u).count(),
                "active_assignments": Assignment.objects.filter(
                    maddie__managed_by=u, status=Assignment.Status.ACTIVE
                ).count(),
            }
            data["my_maddies"] = MaddieSerializer(my_maddies[:8], many=True).data

        else:  # employee
            my_tasks = Task.objects.filter(owner=u)
            data["scope"] = "workspace"
            data["stats"] = {
                "my_tasks": my_tasks.count(),
                "todo": my_tasks.filter(status=Task.Status.TODO).count(),
                "in_progress": my_tasks.filter(status=Task.Status.IN_PROGRESS).count(),
                "done": my_tasks.filter(status=Task.Status.DONE).count(),
                "my_assignments": Assignment.objects.filter(
                    assigned_to=u, status=Assignment.Status.ACTIVE
                ).count(),
            }
            data["my_tasks"] = TaskSerializer(
                my_tasks.exclude(status=Task.Status.DONE)[:8], many=True
            ).data
            data["my_assignments"] = AssignmentSerializer(
                Assignment.objects.filter(assigned_to=u, status=Assignment.Status.ACTIVE)[:5],
                many=True,
            ).data

        return Response(data)
