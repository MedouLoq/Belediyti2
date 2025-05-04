from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm as BaseUserCreationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

# Import your models
from .models import (
    User,
    Municipality,
    Citizen,
    Admin as AdminProfile,  # Renamed to avoid conflict with built-in Admin
    Category,
    Problem,
    Complaint,
    StatusLog,
    Notification
)


class CustomUserCreationForm(BaseUserCreationForm):
    email = forms.EmailField(label=_("Adresse e-mail"), required=False)
    phone_number = forms.CharField(label=_("Numéro de téléphone"), required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("user_type", "email", "phone_number")

    def clean(self):
        cleaned_data = super().clean()
        # ... your existing clean method ...


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'  # Include all fields


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("username", "user_type", "email", "phone_number", "is_staff")
    list_filter = ("user_type", "is_staff", "is_active", "groups")
    search_fields = ("username", "email", "phone_number")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Informations Personnelles"), {"fields": ("first_name", "last_name", "email", "phone_number", "user_type")}),  # Updated fieldset
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Dates Importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("user_type", "email", "phone_number", "password", "password2"),
        }),
    )


    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        if obj:
            if obj.user_type == "CITIZEN":
                inline_instances.append(CitizenInline(self.model, self.admin_site))
            elif obj.user_type in ["ADMIN", "SUPERADMIN"]:
                inline_instances.append(AdminProfileInline(self.model, self.admin_site))
        return inline_instances
      
    def get_readonly_fields(self, request, obj=None):
        # Make 'username', 'user_type', 'email', and 'phone_number' read-only if user exists
        if obj:
          return ['username', 'user_type', 'email','phone_number'] + [field.name for field in obj._meta.fields if field.name not in ['username', 'user_type', 'is_superuser','is_active','is_staff', 'email','phone_number']] # Make other fileds read only
        return ['username', 'user_type']  # Only make these two fields read-only when creating a new user


class CitizenInline(admin.StackedInline):

    model = Citizen
    can_delete = False
    verbose_name_plural = _("Profil Citoyen")
    fk_name = 'user'
    fields = ('full_name', 'nni', 'municipality', 'address')



class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    verbose_name_plural = _("Profil Administrateur")
    fk_name = "user"
    fields = ("municipality", "admin_title")


#... (rest of your admin.py file: MunicipalityAdmin, CitizenAdmin, etc. remains the same) ...

# --- Custom Admin Forms ---

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        # Add or remove fields as needed
        fields = (
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "user_type",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = kwargs.get("instance")
        if user:
            # Dynamically adjust fields based on user_type
            if user.user_type == "CITIZEN":
                # Citizens use phone_number, email is not relevant
                self.fields["email"].widget = forms.HiddenInput()
                self.fields["email"].required = False
                self.fields["phone_number"].required = True
                self.fields["username"].help_text = _("Modifié automatiquement basé sur le numéro de téléphone.")
            else:
                # Admins/Superadmins use email, phone_number is not relevant
                self.fields["phone_number"].widget = forms.HiddenInput()
                self.fields["phone_number"].required = False
                self.fields["email"].required = True
                self.fields["username"].help_text = _("Modifié automatiquement basé sur l\"email.")

        # Make username read-only as it's derived
        self.fields["username"].disabled = True

class CustomUserCreationForm(BaseUserCreationForm):
    # Add fields needed for creation, especially for Admins via Admin interface
    email = forms.EmailField(label=_("Adresse e-mail"), required=False)
    phone_number = forms.CharField(label=_("Numéro de téléphone"), required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("user_type", "email", "phone_number") # Start with these, password handled by UserCreationForm

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        email = cleaned_data.get("email")
        phone_number = cleaned_data.get("phone_number")

        if user_type == "CITIZEN":
            if not phone_number:
                self.add_error("phone_number", _("Le numéro de téléphone est requis pour les citoyens."))
            if email:
                 self.add_error("email", _("L\"email n\"est pas utilisé pour les citoyens."))
            # Check phone uniqueness
            if phone_number and User.objects.filter(phone_number=phone_number).exists():
                 self.add_error("phone_number", _("Ce numéro de téléphone existe déjà."))

        elif user_type in ["ADMIN", "SUPERADMIN"]:
            if not email:
                self.add_error("email", _("L\"email est requis pour les administrateurs."))
            if phone_number:
                self.add_error("phone_number", _("Le numéro de téléphone n\"est pas utilisé pour les administrateurs."))
            # Check email uniqueness
            if email and User.objects.filter(email=email).exists():
                 self.add_error("email", _("Cet email existe déjà."))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data["user_type"]
        user.user_type = user_type

        if user_type == "CITIZEN":
            user.phone_number = self.cleaned_data["phone_number"]
            user.username = user.phone_number # Set username from phone
        else:
            user.email = self.cleaned_data["email"]
            user.username = user.email # Set username from email

        if commit:
            user.save()
        return user

# # --- Main Admin Classes ---

# @admin.register(User)
# class CustomUserAdmin(BaseUserAdmin):
#     form = CustomUserChangeForm
#     add_form = CustomUserCreationForm
#     list_display = (
#         "username",
#         "user_type",
#         "email",
#         "phone_number",
#         "first_name",
#         "last_name",
#         "is_staff",
#         "is_active",
#     )
#     list_filter = ("user_type", "is_staff", "is_active", "groups")
#     search_fields = ("username", "email", "phone_number", "first_name", "last_name")
#     ordering = ("username",)

#     fieldsets = (
#         (None, {"fields": ("username", "password")}),
#         (_("Type & Identifiants"), {"fields": ("user_type", "email", "phone_number")}),
#         (_("Personal info"), {"fields": ("first_name", "last_name")}),
#         (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
#         (_("Important dates"), {"fields": ("last_login", "date_joined")}),
#     )
#     # Fieldsets for adding a user
#     add_fieldsets = (
#         (None, {
#             "classes": ("wide",),
#             "fields": ("user_type", "email", "phone_number", "password", "password2"), # Use password/password2 from UserCreationForm
#         }),
#     )
#     # Use inlines based on user type (conditionally if possible, else show both)
#     # Conditional inlines are complex, showing both might be simpler initially
#     inlines = [CitizenInline, AdminProfileInline]

#     # Make username read-only in the change view
#     def get_readonly_fields(self, request, obj=None):
#         if obj: # editing an existing object
#             return self.readonly_fields + (
#                 "username",
#                 "user_type", # Prevent changing type after creation?
#             )
#         return self.readonly_fields

#     # Hide irrelevant inlines based on user type (requires JS or more complex logic)
#     # For simplicity, we show both. Superadmin needs to fill the correct one.

@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("created_at",)

# Unregister the default Citizen and AdminProfile if using inlines
# admin.site.unregister(Citizen)
# admin.site.unregister(AdminProfile)

# Re-register with potential modifications if needed outside of inline
@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user_link",
        "nni",
        "municipality",
        "address",
        "created_at",
    )
    search_fields = (
        "full_name",
        "user__username",
        "user__email",
        "user__phone_number",
        "nni",
        "address",
        "municipality__name",
    )
    list_filter = ("municipality", "created_at")
    raw_id_fields = ("user", "municipality") # Better for performance
    readonly_fields = ("user_link",)

    @admin.display(description=_("Utilisateur"), ordering="user__username")
    def user_link(self, obj):
        link = reverse("admin:Citoyen_user_change", args=[obj.user.id])
        return format_html("<a href=\"{}\">{}</a>", link, obj.user)

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "municipality",
        "admin_title",
        "created_at",
    )
    search_fields = ("user__username", "user__email", "municipality__name", "admin_title")
    list_filter = ("municipality", "created_at")
    raw_id_fields = ("user", "municipality") # Better for performance
    readonly_fields = ("user_link",)

    @admin.display(description=_("Utilisateur"), ordering="user__username")
    def user_link(self, obj):
        link = reverse("admin:Citoyen_user_change", args=[obj.user.id])
        return format_html("<a href=\"{}\">{}</a>", link, obj.user)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "citizen_link",
        "municipality",
        "category",
        "status",
        "location_short",
        "created_at",
    )
    list_filter = ("status", "municipality", "category", "created_at")
    search_fields = (
        "id__iexact",
        "description",
        "location",
        "citizen__full_name",
        "citizen__nni",
        "municipality__name",
        "category__name",
    )
    readonly_fields = ("id", "created_at", "updated_at", "citizen_link")
    date_hierarchy = "created_at"
    raw_id_fields = ("citizen", "municipality", "category")
    list_select_related = ("citizen", "municipality", "category")

    fieldsets = (
        (None, {"fields": ("id", "citizen_link", "municipality", "category", "status")}),
        (_("Details"), {"fields": ("description", "photo", "location", "latitude", "longitude")}),
        (_("Metadata"), {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Adresse (courte)"))
    def location_short(self, obj):
        return (obj.location or "")[:50] + ("..." if len(obj.location or "") > 50 else "")

    @admin.display(description=_("Citoyen"), ordering="citizen__full_name")
    def citizen_link(self, obj):
        if not obj.citizen: return "-"
        link = reverse("admin:Citoyen_citizen_change", args=[obj.citizen.id])
        return format_html("<a href=\"{}\">{}</a>", link, obj.citizen)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "citizen_link",
        "municipality",
        "subject_short",
        "status",
        "created_at",
    )
    list_filter = ("status", "municipality", "created_at")
    search_fields = (
        "id__iexact",
        "subject",
        "description",
        "citizen__full_name",
        "citizen__nni",
        "municipality__name",
    )
    readonly_fields = ("id", "created_at", "updated_at", "citizen_link")
    date_hierarchy = "created_at"
    raw_id_fields = ("citizen", "municipality")
    list_select_related = ("citizen", "municipality")

    fieldsets = (
        (None, {"fields": ("id", "citizen_link", "municipality", "status")}),
        (_("Details"), {"fields": ("subject", "description", "evidence")}), # Added evidence
        (_("Metadata"), {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Sujet (court)"))
    def subject_short(self, obj):
        return (obj.subject or "")[:50] + ("..." if len(obj.subject or "") > 50 else "")

    @admin.display(description=_("Citoyen"), ordering="citizen__full_name")
    def citizen_link(self, obj):
        if not obj.citizen: return "-"
        link = reverse("admin:Citoyen_citizen_change", args=[obj.citizen.id])
        return format_html("<a href=\"{}\">{}</a>", link, obj.citizen)

@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = (
        "get_record_link",
        "record_type",
        "old_status",
        "new_status",
        "changed_by_link",
        "changed_at",
    )
    list_filter = ("record_type", "changed_at", "new_status", "old_status")
    search_fields = ("record_id__iexact", "changed_by__username")
    readonly_fields = (
        "record_type",
        "record_id",
        "old_status",
        "new_status",
        "changed_by_link",
        "changed_at",
        "get_record_link",
    )
    list_select_related = ("changed_by",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False # View only

    @admin.display(description=_("Enregistrement Lié"), ordering="record_id")
    def get_record_link(self, obj):
        record = obj.get_related_object()
        if not record: return obj.record_id
        app_label = record._meta.app_label
        model_name = record._meta.model_name
        url = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.record_id])
        label = _("Problème") if obj.record_type == "PROBLEM" else _("Réclamation")
        return format_html("<a href=\"{}\">{} #{}</a>", url, label, str(obj.record_id)[:8] + "...")

    @admin.display(description=_("Modifié par"), ordering="changed_by__username")
    def changed_by_link(self, obj):
        if not obj.changed_by: return "-"
        link = reverse("admin:Citoyen_user_change", args=[obj.changed_by.id])
        return format_html("<a href=\"{}\">{}</a>", link, obj.changed_by)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user_link", "type", "read_at", "created_at", "data_preview")
    list_filter = ("type", "read_at", "created_at")
    search_fields = ("user__username", "type", "data__icontains")
    readonly_fields = ("created_at", "user_link", "data_preview")
    date_hierarchy = "created_at"
    raw_id_fields = ("user",)
    list_select_related = ("user",)

    @admin.display(description=_("Aperçu Données"))
    def data_preview(self, obj):
        import json
        try:
            preview = json.dumps(obj.data, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", preview[:200] + ("..." if len(preview) > 200 else ""))
        except Exception:
            return str(obj.data)

    @admin.display(description=_("Utilisateur"), ordering="user__username")
    def user_link(self, obj):
        if not obj.user: return "-"
        link = reverse("admin:Citoyen_user_change", args=[obj.user.id])
        return format_html("<a href=\"{}\">{}</a>", link, obj.user)


