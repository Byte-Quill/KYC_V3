from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import KYCApplicationViewSet, MeView, RegisterView, ReviewQueueView

router = DefaultRouter()
router.register("applications", KYCApplicationViewSet, basename="application")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("review-queue/", ReviewQueueView.as_view(), name="review_queue"),
    path("", include(router.urls)),
]
