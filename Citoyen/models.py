from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

# Utilisateur personnalisé
class User(AbstractUser):
    USER_TYPE_CHOICES = (
    ('CITIZEN', _('Citoyen')),
    ('ADMIN', _('Administrateur')),
    ('SUPERADMIN', _('Superadministrateur')),
)

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='CITIZEN')

    def __str__(self):
        return self.email

# Municipalité
class Municipality(models.Model):
    name = models.CharField(_('Nom'), max_length=255)
    latitude = models.FloatField(_('Latitude'), blank=True, null=True)
    longitude = models.FloatField(_('Longitude'), blank=True, null=True)
    boundary = models.TextField(_('Limites géographiques'), blank=True, null=True)  # Stockage GeoJSON
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Municipalité')
        verbose_name_plural = _('Municipalités')

    def __str__(self):
        return self.name

# Profil Citoyen
class Citizen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='citizen_profile')
    full_name = models.CharField(_('Nom complet'), max_length=255)
    phone = models.CharField(_('Téléphone'), max_length=50, blank=True, null=True)
    address = models.CharField(_('Adresse'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Citoyen')
        verbose_name_plural = _('Citoyens')

    def __str__(self):
        return self.full_name

# Profil Administrateur
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='administrators')
    admin_title = models.CharField(_('Titre'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Administrateur')
        verbose_name_plural = _('Administrateurs')

    def __str__(self):
        return f"{self.user.username} - {self.municipality.name}"

# Catégories de Problèmes
class Category(models.Model):
    name = models.CharField(_('Nom'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')

    def __str__(self):
        return self.name

# Problèmes Signalés
class Problem(models.Model):
    STATUS_CHOICES = (
        ('PENDING', _('En attente')),
        ('IN_PROGRESS', _('En cours')),
        ('DELEGATED', _('Délégué')),
        ('RESOLVED', _('Résolu')),
        ('REJECTED', _('Rejeté')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='problems')
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='problems')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='problems',blank=True, null=True)
    description = models.TextField(_('Description'))
    photo = models.ImageField(_('Photo'), upload_to='problem_photos/', blank=True, null=True)
    location = models.CharField(_('Adresse'), max_length=255, blank=True, null=True)
    latitude = models.FloatField(_('Latitude'))
    longitude = models.FloatField(_('Longitude'))
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Problème')
        verbose_name_plural = _('Problèmes')


# Réclamations
class Complaint(models.Model):
    STATUS_CHOICES = (
        ('PENDING', _('En attente')),
        ('REVIEWING', _('En examen')),
        ('RESOLVED', _('Résolu')),
        ('REJECTED', _('Rejeté')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='complaints')
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(_('Sujet'), max_length=255)
    description = models.TextField(_('Description'))
    evidence = models.FileField(_('Evidence'), upload_to='Reclamation_fiche/', blank=True, null=True)
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Réclamation')
        verbose_name_plural = _('Réclamations')

    def __str__(self):
        return f"Réclamation #{self.id} - {self.subject}"

# Journal des Statuts
class StatusLog(models.Model):
    RECORD_TYPE_CHOICES = (
        ('PROBLEM', _('Problème')),
        ('COMPLAINT', _('Réclamation')),
    )
    
    record_type = models.CharField(_('Type d\'enregistrement'), max_length=10, choices=RECORD_TYPE_CHOICES)
    record_id = models.UUIDField(_('ID d\'enregistrement'))
    old_status = models.CharField(_('Ancien statut'), max_length=20)
    new_status = models.CharField(_('Nouveau statut'), max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_changes')
    changed_at = models.DateTimeField(_('Modifié le'), default=timezone.now)
    def get_related_object(self):
        if self.record_type == 'PROBLEM':
            return Problem.objects.get(id=self.record_id)
        elif self.record_type == 'COMPLAINT':
            return Complaint.objects.get(id=self.record_id)

    class Meta:
        verbose_name = _('Journal de statut')
        verbose_name_plural = _('Journaux de statut')

    def __str__(self):
        return f"{self.record_type} #{self.record_id} - {self.old_status} -> {self.new_status}"

# Notifications
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(_('Type'), max_length=50)
    data = models.JSONField(_('Données'))
    read_at = models.DateTimeField(_('Lu le'), blank=True, null=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return f"Notification pour {self.user.username} - {self.type}"