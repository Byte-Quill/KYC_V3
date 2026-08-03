from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ActivityLog, Assignment, Maddie, Task, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "manager", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Maddies", {"fields": ("role", "phone", "manager")}),
    )


admin.site.register(Maddie)
admin.site.register(Assignment)
admin.site.register(Task)
admin.site.register(ActivityLog)
