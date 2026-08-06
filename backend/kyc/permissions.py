from rest_framework.permissions import BasePermission


class IsReviewer(BasePermission):
    """Allow access only to reviewers/admins."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_reviewer)


class IsOwnerOrReviewer(BasePermission):
    """Applicants can access their own applications; reviewers can access all."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_reviewer:
            return True
        return obj.applicant_id == request.user.id
