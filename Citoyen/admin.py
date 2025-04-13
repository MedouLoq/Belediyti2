from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

# Import your models
from .models import (
    User,
    Municipality,
    Citizen,
    Admin as MunicipalityAdminProfile, # Renamed to avoid conflict with django.contrib.admin
    Category,
    Problem,
    Complaint,
    StatusLog,
    Notification
)

# --- Custom Admin Classes ---

# Enhance the default User admin
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        # Add Custom Fields here
        (_('User Type'), {'fields': ('user_type',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('User Type'), {'fields': ('user_type',)}),
    )

@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'get_user_email', 'phone', 'address', 'created_at')
    search_fields = ('full_name', 'user__username', 'user__email', 'phone', 'address')
    list_filter = ('created_at',)
    raw_id_fields = ('user',) # Better for performance if many users

    @admin.display(description=_('Email Utilisateur'), ordering='user__email')
    def get_user_email(self, obj):
        return obj.user.email

@admin.register(MunicipalityAdminProfile)
class MunicipalityAdminProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'municipality', 'admin_title', 'created_at')
    search_fields = ('user__username', 'municipality__name', 'admin_title')
    list_filter = ('municipality', 'created_at')
    raw_id_fields = ('user', 'municipality') # Better for performance

    @admin.display(description=_('Nom d\'utilisateur'), ordering='user__username')
    def get_username(self, obj):
        return obj.user.username

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'citizen', 'municipality', 'category', 'status', 'location_short', 'created_at')
    list_filter = ('status', 'municipality', 'category', 'created_at')
    search_fields = ('id__iexact', 'description', 'location', 'citizen__full_name', 'municipality__name', 'category__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('citizen', 'municipality', 'category')
    list_select_related = ('citizen', 'municipality', 'category') # Performance optimization

    fieldsets = (
        (None, {
            'fields': ('id', 'citizen', 'municipality', 'category', 'status')
        }),
        (_('Details'), {
            'fields': ('description', 'photo', 'location', 'latitude', 'longitude')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description=_('Adresse (courte)'))
    def location_short(self, obj):
        if obj.location and len(obj.location) > 50:
            return f"{obj.location[:50]}..."
        return obj.location

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'citizen', 'municipality', 'subject_short', 'status', 'created_at')
    list_filter = ('status', 'municipality', 'created_at')
    search_fields = ('id__iexact', 'subject', 'description', 'citizen__full_name', 'municipality__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('citizen', 'municipality')
    list_select_related = ('citizen', 'municipality') # Performance optimization

    fieldsets = (
        (None, {
            'fields': ('id', 'citizen', 'municipality', 'status')
        }),
        (_('Details'), {
            'fields': ('subject', 'description')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description=_('Sujet (court)'))
    def subject_short(self, obj):
        if obj.subject and len(obj.subject) > 50:
            return f"{obj.subject[:50]}..."
        return obj.subject


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ('get_record_link', 'record_type', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('record_type', 'changed_at', 'new_status', 'old_status')
    search_fields = ('record_id__iexact', 'changed_by__username')
    readonly_fields = ('record_type', 'record_id', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_select_related = ('changed_by',) # Performance optimization

    # Prevent adding/changing/deleting logs via admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False # Allow viewing only

    # def has_delete_permission(self, request, obj=None):
    #     return False # Optional: uncomment if you want to prevent deletion too

    @admin.display(description=_('Enregistrement Lié'), ordering='record_id')
    def get_record_link(self, obj):
        """Creates a link to the related Problem or Complaint admin change page."""
        if obj.record_type == 'PROBLEM':
            url = reverse('admin:%s_%s_change' % (Problem._meta.app_label, Problem._meta.model_name), args=[obj.record_id])
            return format_html('<a href="{}">Problème #{}</a>', url, str(obj.record_id)[:8] + "...")
        elif obj.record_type == 'COMPLAINT':
            url = reverse('admin:%s_%s_change' % (Complaint._meta.app_label, Complaint._meta.model_name), args=[obj.record_id])
            return format_html('<a href="{}">Réclamation #{}</a>', url, str(obj.record_id)[:8] + "...")
        return obj.record_id


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'read_at', 'created_at', 'data_preview')
    list_filter = ('type', 'read_at', 'created_at')
    search_fields = ('user__username', 'type', 'data__icontains') # Note: data search might be slow depending on DB
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    list_select_related = ('user',) # Performance optimization

    @admin.display(description=_('Aperçu Données'))
    def data_preview(self, obj):
        import json
        try:
            preview = json.dumps(obj.data, indent=2, ensure_ascii=False)
            if len(preview) > 100:
                preview = preview[:100] + "..."
            return format_html("<pre>{}</pre>", preview)
        except Exception:
            return str(obj.data)