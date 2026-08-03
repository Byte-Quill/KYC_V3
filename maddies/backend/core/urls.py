from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ActivityLogViewSet,
    AssignmentViewSet,
    DashboardView,
    MaddieViewSet,
    MeView,
    TaskViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("maddies", MaddieViewSet, basename="maddie")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("tasks", TaskViewSet, basename="task")
router.register("activity", ActivityLogViewSet, basename="activity")

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]
