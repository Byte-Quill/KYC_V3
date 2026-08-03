from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, Document, KYCApplication, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    list_display = ("email", "username", "role", "is_staff")


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


@admin.register(KYCApplication)
class KYCApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "applicant", "status", "created_at")
    list_filter = ("status", "id_type")
    search_fields = ("full_name", "id_number", "applicant__email")
    inlines = [DocumentInline]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "application", "actor", "created_at")
    list_filter = ("action",)
    readonly_fields = ("application", "actor", "action", "detail", "created_at")
