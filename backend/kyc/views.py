from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from . import supabase_client
from .models import AuditLog, Document, KYCApplication
from .permissions import IsOwnerOrReviewer, IsReviewer
from .serializers import (
    AuditLogSerializer,
    DocumentSerializer,
    KYCApplicationSerializer,
    RegisterSerializer,
    ReviewSerializer,
    UserSerializer,
)

User = get_user_model()


def log_action(application, actor, action, detail=""):
    AuditLog.objects.create(
        application=application, actor=actor, action=action, detail=detail
    )
    # Broadcast status changes to Supabase Realtime so the frontend can update
    # live without polling. No-op when Supabase is not configured.
    if action in (
        AuditLog.Action.SUBMITTED,
        AuditLog.Action.APPROVED,
        AuditLog.Action.REJECTED,
        AuditLog.Action.RESUBMISSION_REQUESTED,
    ):
        supabase_client.broadcast_status_change(
            str(application.id), application.status, detail
        )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class KYCApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = KYCApplicationSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReviewer)
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = KYCApplication.objects.select_related("applicant", "reviewer").prefetch_related("documents")
        user = self.request.user
        if user.is_reviewer:
            status_filter = self.request.query_params.get("status")
            if status_filter:
                qs = qs.filter(status=status_filter)
            return qs
        return qs.filter(applicant=user)

    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        log_action(application, self.request.user, AuditLog.Action.CREATED)

    def perform_update(self, serializer):
        application = serializer.save()
        log_action(application, self.request.user, AuditLog.Action.UPDATED)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        application = self.get_object()
        if application.applicant_id != request.user.id:
            raise ValidationError("Only the applicant can submit this application.")
        if not application.documents.exists():
            raise ValidationError("At least one supporting document is required before submission.")
        try:
            application.submit()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message)
        log_action(application, request.user, AuditLog.Action.SUBMITTED)
        return Response(self.get_serializer(application).data)

    @action(detail=True, methods=["post"], parser_classes=(MultiPartParser, FormParser))
    def documents(self, request, pk=None):
        application = self.get_object()
        if application.applicant_id != request.user.id:
            raise ValidationError("Only the applicant can upload documents.")
        if application.status not in (
            KYCApplication.Status.DRAFT,
            KYCApplication.Status.RESUBMISSION_REQUESTED,
        ):
            raise ValidationError("Documents can only be uploaded while the application is editable.")

        file_obj = request.FILES.get("file")
        doc_type = request.data.get("doc_type")
        if not file_obj:
            raise ValidationError({"file": "No file provided."})
        if doc_type not in Document.DocType.values:
            raise ValidationError({"doc_type": f"Must be one of {list(Document.DocType.values)}."})

        document = Document(
            application=application,
            doc_type=doc_type,
            file=file_obj,
            original_filename=file_obj.name,
        )
        try:
            document.full_clean()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        document.save()

        # Mirror the file to Supabase Storage when configured. The local copy
        # remains the source of truth for the FileField; Supabase provides the
        # durable, CDN-backed copy and public/signed URLs.
        if supabase_client.is_configured():
            file_obj.seek(0)
            storage_path = f"{application.id}/{document.id}_{file_obj.name}"
            uploaded = supabase_client.upload_document(
                storage_path, file_obj.read(), file_obj.content_type or "application/octet-stream"
            )
            if uploaded:
                document.storage_path = uploaded
                document.save(update_fields=["storage_path"])

        log_action(
            application,
            request.user,
            AuditLog.Action.DOCUMENT_UPLOADED,
            detail=f"{doc_type}: {file_obj.name}",
        )
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=(IsAuthenticated, IsReviewer))
    def review(self, request, pk=None):
        application = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        notes = serializer.validated_data["notes"]
        try:
            application.apply_review(reviewer=request.user, decision=decision, notes=notes)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message)
        action_map = {
            "approve": AuditLog.Action.APPROVED,
            "reject": AuditLog.Action.REJECTED,
            "request_resubmission": AuditLog.Action.RESUBMISSION_REQUESTED,
        }
        log_action(application, request.user, action_map[decision], detail=notes)
        return Response(self.get_serializer(application).data)

    @action(detail=True, methods=["get"])
    def audit(self, request, pk=None):
        application = self.get_object()
        logs = application.audit_logs.select_related("actor")
        return Response(AuditLogSerializer(logs, many=True).data)


class ReviewQueueView(generics.ListAPIView):
    """Reviewer-facing queue of applications awaiting a decision."""

    serializer_class = KYCApplicationSerializer
    permission_classes = (IsAuthenticated, IsReviewer)

    def get_queryset(self):
        return (
            KYCApplication.objects.filter(
                status__in=[
                    KYCApplication.Status.SUBMITTED,
                    KYCApplication.Status.UNDER_REVIEW,
                ]
            )
            .select_related("applicant")
            .prefetch_related("documents")
        )
