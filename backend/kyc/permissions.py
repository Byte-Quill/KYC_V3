from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsReviewer(BasePermission):
    """Allow access only to reviewers/admins."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_reviewer)


class IsOwnerOrReviewer(BasePermission):
    """Applicants can access their own applications; reviewers can access all (read-only)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Reviewers are read-only on application resources
        if request.user.is_reviewer and request.method not in SAFE_METHODS:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_reviewer:
            # Reviewers can only read (has_permission already blocks writes)
            return request.method in SAFE_METHODS
        return obj.applicant_id == request.user.id
