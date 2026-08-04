from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import AuditLog, Document, KYCApplication

User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT serializer that authenticates with email instead of username."""

    username_field = "email"

    def validate(self, attrs):
        attrs["username"] = attrs.get("email", "")
        return super().validate(attrs)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "first_name", "last_name")

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Role.APPLICANT,
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "role")
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "doc_type", "file", "original_filename", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ("id", "action", "detail", "actor_email", "created_at")
        read_only_fields = fields


class KYCApplicationSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True, default=None)

    class Meta:
        model = KYCApplication
        fields = (
            "id",
            "applicant_email",
            "status",
            "full_name",
            "date_of_birth",
            "nationality",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "id_type",
            "id_number",
            "id_expiry",
            "reviewer_email",
            "review_notes",
            "reviewed_at",
            "documents",
            "created_at",
            "updated_at",
            "submitted_at",
        )
        read_only_fields = (
            "id",
            "status",
            "applicant_email",
            "reviewer_email",
            "review_notes",
            "reviewed_at",
            "created_at",
            "updated_at",
            "submitted_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        # Applicants may only edit while the application is a draft or needs resubmission
        if self.instance and request and not request.user.is_reviewer:
            editable = (
                KYCApplication.Status.DRAFT,
                KYCApplication.Status.RESUBMISSION_REQUESTED,
            )
            if self.instance.status not in editable:
                raise serializers.ValidationError(
                    "This application can no longer be edited."
                )
        return attrs


class ReviewSerializer(serializers.Serializer):
    DECISIONS = ("approve", "reject", "request_resubmission")

    decision = serializers.ChoiceField(choices=DECISIONS)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["decision"] in ("reject", "request_resubmission") and not attrs["notes"].strip():
            raise serializers.ValidationError(
                {"notes": "Notes are required when rejecting or requesting resubmission."}
            )
        return attrs
