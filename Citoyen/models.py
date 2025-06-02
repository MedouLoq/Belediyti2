from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, identifier, password=None, **extra_fields):
        """Creates and saves a User with the given identifier and password."""
        if not identifier:
            raise ValueError(_("The identifier must be set"))

        user_type = extra_fields.get("user_type", "CITIZEN")

        if user_type == "CITIZEN":
            # Identifier is phone_number for CITIZEN
            extra_fields["phone_number"] = identifier
            extra_fields["username"] = identifier # Use phone number as username for citizens
            extra_fields.pop("email", None) # Citizens don't use email for login
        else:
            # Identifier is email for ADMIN/SUPERADMIN
            email = self.normalize_email(identifier)
            extra_fields["email"] = email
            extra_fields["username"] = email # Use email as username for admins
            extra_fields.pop("phone_number", None)

        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """Creates and saves a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "SUPERADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        # Superadmin uses email as identifier
        return self.create_user(username, password, **extra_fields)

# Utilisateur personnalisé
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ("CITIZEN", _("Citoyen")),
        ("ADMIN", _("Administrateur")),
        ("SUPERADMIN", _("Superadministrateur")),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="CITIZEN")
    phone_number = models.CharField(_("Numéro de téléphone"), max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(_("Adresse e-mail"), unique=True, null=True, blank=True)
    phone_verified = models.BooleanField(default=False, blank=True, null=True)
    # Remove email from required fields if user is CITIZEN
    REQUIRED_FIELDS = [] # No fields required besides username/password by default
    USERNAME_FIELD = "username" # Keep username as the main identifier internally

    objects = UserManager()

    def __str__(self):
        if self.user_type == "CITIZEN":
            return self.phone_number or self.username
        else:
            return self.email or self.username

    def save(self, *args, **kwargs):
        # Ensure username uniqueness based on user type
        if self.user_type == "CITIZEN":
            if not self.phone_number:
                raise ValueError(_("Citizen users must have a phone number."))
            self.username = self.phone_number
            self.email = None # Ensure email is null for citizens
        else:
            if not self.email:
                raise ValueError(_("Admin/Superadmin users must have an email."))
            self.username = self.email
            self.phone_number = None # Ensure phone number is null for admins
        super().save(*args, **kwargs)

# Municipalité
class Municipality(models.Model):
    name = models.CharField(_("Nom"), max_length=255)
    latitude = models.FloatField(_("Latitude"), blank=True, null=True)
    longitude = models.FloatField(_("Longitude"), blank=True, null=True)
    boundary = models.TextField(_("Limites géographiques"), blank=True, null=True)  # Stockage GeoJSON
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Municipalité")
        verbose_name_plural = _("Municipalités")

    def __str__(self):
        return self.name

# Profil Citoyen
class Citizen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="citizen_profile", limit_choices_to={"user_type": "CITIZEN"})
    full_name = models.CharField(_("Nom complet"), max_length=255)
    nni = models.CharField(_("NNI"), max_length=50, unique=True, null=True) # Added NNI field
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name="citizens", verbose_name=_("Municipalité de résidence") ,null=True) # Added Municipality
    address = models.CharField(_("Adresse"), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    profile_picture = models.ImageField(_("Photo de profil"), upload_to="profile_pics/", blank=True, null=True)
    class Meta:
        verbose_name = _("Citoyen")
        verbose_name_plural = _("Citoyens")

    def __str__(self):
        return self.full_name

# Profil Administrateur
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile", limit_choices_to={"user_type__in": ["ADMIN", "SUPERADMIN"]})
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="administrators", null=True, blank=True) # Admins might not be tied to one municipality (Superadmin)
    admin_title = models.CharField(_("Titre"), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Administrateur")
        verbose_name_plural = _("Administrateurs")

    def __str__(self):
        municipality_name = self.municipality.name if self.municipality else "Global"
        return f"{self.user.username} - {municipality_name}"

# Catégories de Problèmes
class Category(models.Model):
    name = models.CharField(_("Nom"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")

    def __str__(self):
        return self.name

# Problèmes Signalés
class Problem(models.Model):
    STATUS_CHOICES = (
        ("PENDING", _("En attente")),
        ("IN_PROGRESS", _("En cours")),
        ("DELEGATED", _("Délégué")),
        ("RESOLVED", _("Résolu")),
        ("REJECTED", _("Rejeté")),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name="problems")
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="problems")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="problems", blank=True, null=True)
    description = models.TextField(_("Description"))
    comment = models.TextField(null=True,blank=True)
        
    # Media fields (as requested)
    photo = models.ImageField(_("Photo"), upload_to="problem_photos/", blank=True, null=True)
    video = models.FileField(_("Video"), upload_to="problem_videos/", blank=True, null=True)
    voice_record = models.FileField(_("Voice Record"), upload_to="problem_voice/", blank=True, null=True)
    document = models.FileField(_("Document"), upload_to="problem_documents/", blank=True, null=True)
    
    location = models.CharField(_("Adresse"), max_length=255, blank=True, null=True)
    latitude = models.FloatField(_("Latitude"))
    longitude = models.FloatField(_("Longitude"))
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Problème")
        verbose_name_plural = _("Problèmes")

# Réclamations
class Complaint(models.Model):
    STATUS_CHOICES = (
        ("PENDING", _("En attente")),
        ("REVIEWING", _("En examen")),
        ("RESOLVED", _("Résolu")),
        ("REJECTED", _("Rejeté")),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name="complaints")
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="complaints")
    subject = models.CharField(_("Sujet"), max_length=255)
    description = models.TextField(_("Description"))
    evidence = models.FileField(_("Evidence"), upload_to="Reclamation_fiche/", blank=True, null=True)
    comment = models.TextField(null=True,blank=True)
        
    # Media fields (as requested)
    photo = models.ImageField(_("Photo"), upload_to="Reclamation_photos/", blank=True, null=True)
    video = models.FileField(_("Video"), upload_to="Reclamation_videos/", blank=True, null=True)
    voice_record = models.FileField(_("Voice Record"), upload_to="Reclamation_voice/", blank=True, null=True)    
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Réclamation")
        verbose_name_plural = _("Réclamations")

    def __str__(self):
        return f"Réclamation #{self.id} - {self.subject}"

# Journal des Statuts
class StatusLog(models.Model):
    RECORD_TYPE_CHOICES = (
        ("PROBLEM", _("Problème")),
        ("COMPLAINT", _("Réclamation")),
    )

    record_type = models.CharField(_("Type d'enregistrement"), max_length=10, choices=RECORD_TYPE_CHOICES)
    record_id = models.UUIDField(_("ID d'enregistrement"))
    old_status = models.CharField(_("Ancien statut"), max_length=20)
    new_status = models.CharField(_("Nouveau statut"), max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_changes")
    changed_at = models.DateTimeField(_("Modifié le"), default=timezone.now)
    comment = models.TextField(blank=True, null=True)
    def get_related_object(self):
        if self.record_type == "PROBLEM":
            return Problem.objects.filter(id=self.record_id).first()
        elif self.record_type == "COMPLAINT":
            return Complaint.objects.filter(id=self.record_id).first()
        return None

    class Meta:
        verbose_name = _("Journal de statut")
        verbose_name_plural = _("Journaux de statut")

    def __str__(self):
        return f"{self.record_type} #{self.record_id} - {self.old_status} -> {self.new_status}"

# Notifications
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('PROBLEM_UPDATE', 'Problem Update'),
        ('COMPLAINT_UPDATE', 'Complaint Update'),
        ('ANNOUNCEMENT', 'Announcement'),
        ('OTHER', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, null=True)
    message = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='OTHER')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, null=True)
    related_id = models.CharField(max_length=50, blank=True, null=True)  # UUID of related entity
    related_type = models.CharField(max_length=20, blank=True, null=True)  # Type of related entity
    
    class Meta:
        ordering = ['-created_at']

class NotificationPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    problem_updates = models.BooleanField(default=True)
    complaint_updates = models.BooleanField(default=True)
    news_and_announcements = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Notification Preferences'

from django.conf import settings

class VerificationCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.phone_number} - {self.code}"
