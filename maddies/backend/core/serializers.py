from rest_framework import serializers

from .models import ActivityLog, Assignment, Maddie, Task, User


class UserSerializer(serializers.ModelSerializer):
    manager_email = serializers.EmailField(source="manager.email", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "role", "phone", "manager", "manager_email",
        ]
        read_only_fields = ["id"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "role", "phone", "manager",
                  "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate_role(self, value):
        request = self.context["request"]
        # A user may only create accounts strictly below their own rank.
        target_rank = User.ROLE_RANK.get(value, 99)
        if target_rank <= request.user.rank:
            raise serializers.ValidationError(
                "You can only create accounts with a role below your own."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MaddieSerializer(serializers.ModelSerializer):
    managed_by_email = serializers.EmailField(source="managed_by.email", read_only=True, default=None)
    active_assignments = serializers.SerializerMethodField()

    class Meta:
        model = Maddie
        fields = [
            "id", "full_name", "phone", "email", "address", "skills",
            "hourly_rate", "status", "photo", "managed_by", "managed_by_email",
            "active_assignments", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_active_assignments(self, obj):
        return obj.assignments.filter(status=Assignment.Status.ACTIVE).count()


class AssignmentSerializer(serializers.ModelSerializer):
    maddie_name = serializers.CharField(source="maddie.full_name", read_only=True)
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, default=None)

    class Meta:
        model = Assignment
        fields = [
            "id", "maddie", "maddie_name", "client_name", "client_address",
            "start_date", "end_date", "status", "assigned_to", "assigned_to_email",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status", "priority", "due_date",
            "owner", "owner_email", "assignment", "created_at",
        ]
        read_only_fields = ["id", "created_at", "owner"]


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = ActivityLog
        fields = ["id", "actor", "actor_email", "action", "detail", "created_at"]
        read_only_fields = fields
