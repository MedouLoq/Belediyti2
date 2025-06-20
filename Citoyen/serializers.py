# Citoyen/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

# Citoyen/serializers.py (Example - adjust based on StatusLog fields)
from rest_framework import serializers
from .models import StatusLog

class StatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusLog
        fields = ['record_type', 'record_id', 'old_status', 'new_status', 'changed_at']


from rest_framework import serializers
from .models import Problem, Complaint

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'description', 'created_at', 'status']  # Add created_at, status and other required info

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id', 'subject', 'description', 'created_at', 'status'] # Add created_at,status and other requierd info


from rest_framework import serializers
from .models import Problem, Category, Municipality, User # Import necessary models

# Assuming these serializers exist or can be defined as needed
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"] # Adjust fields as needed

class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = ["id", "name"]

# --- Corrected Problem Detail Serializer ---
class ProblemDetailSerializer(serializers.ModelSerializer):
    # Nested serializers for related objects
    category = CategorySerializer(read_only=True)
    municipality = MunicipalitySerializer(read_only=True)
    
    # Method fields to generate full URLs for media files
    photo_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    voice_record_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    document_name = serializers.SerializerMethodField()
    
    # Human-readable status
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Problem
        fields = [
            "id", 
            "description", 
            "latitude", 
            "longitude", 
            "status", 
            "status_display",
            "created_at", 
            "updated_at",
            "comment", # Admin comment
            "category", 
            "municipality",
            # URLs for single media files
            "photo_url", 
            "video_url", 
            "voice_record_url", 
            "document_url",
            "document_name", # Include document filename
            "location", # Include location string if needed
        ]
        read_only_fields = fields # Make all fields read-only for detail view

    def _get_absolute_url(self, field):
        request = self.context.get("request")
        if field and hasattr(field, "url"):
            try:
                return request.build_absolute_uri(field.url)
            except Exception as e:
                # Log error if URL generation fails
                print(f"Error building absolute URI for {field.name}: {e}")
                return None
        return None

    def get_photo_url(self, obj):
        return self._get_absolute_url(obj.photo)

    def get_video_url(self, obj):
        return self._get_absolute_url(obj.video)

    def get_voice_record_url(self, obj):
        return self._get_absolute_url(obj.voice_record)

    def get_document_url(self, obj):
        return self._get_absolute_url(obj.document)
        
    def get_document_name(self, obj):
        if obj.document and hasattr(obj.document, "name"):
            # Extract filename from the path
            import os
            return os.path.basename(obj.document.name)
        return None

from .models import Citizen
class CitizenSerializer(serializers.ModelSerializer):
    # Make profile_picture read-only in this serializer, handle updates separately
    # Use SerializerMethodField to construct the full URL
    profile_picture_url = serializers.SerializerMethodField()
    municipality = MunicipalitySerializer(read_only=True)

    class Meta:
        model = Citizen
        fields = [
            "full_name", 
            "nni", 
            "municipality", 
            "address", 
            "profile_picture", # Keep the field itself for updates if needed elsewhere
            "profile_picture_url" # Expose the full URL
        ]
        read_only_fields = ["profile_picture"] # Prevent direct update via this serializer if nested

    def get_profile_picture_url(self, obj):
        request = self.context.get("request")
        if obj.profile_picture and hasattr(obj.profile_picture, "url"):
            # Build absolute URL if request context is available
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            # Fallback to relative URL if no request context (less ideal for APIs)
            return obj.profile_picture.url
        return None # Return null if no picture

class UserSerializer(serializers.ModelSerializer):
    # Nest the citizen profile information
    citizen_profile = CitizenSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", 
            "username", # Usually phone number for citizen
            "phone_number", 
            "email", # Likely null for citizen
            "user_type", 
            "citizen_profile" # Include the nested profile
        ]
        # Add other fields from User model if needed

# --- Serializer for Profile Update --- 
class CitizenProfileUpdateSerializer(serializers.ModelSerializer):
    # Allow writing to profile_picture field
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    # Include other fields that can be updated
    full_name = serializers.CharField(required=False, max_length=255)
    address = serializers.CharField(required=False, max_length=255, allow_blank=True)
    # Add NNI or other fields if they should be editable via API

    class Meta:
        model = Citizen
        fields = [
            "full_name", 
            "address", 
            "profile_picture",
            # Add other editable fields like "nni" if applicable
        ]

    def update(self, instance, validated_data):
        # Handle profile picture update/clearance
        # If profile_picture is not in validated_data, it means it wasn't sent or wasn't changed.
        # If profile_picture is None in validated_data, it means the user wants to clear it.
        if "profile_picture" in validated_data:
            if validated_data["profile_picture"] is None:
                # Clear the image
                instance.profile_picture.delete(save=False) # Delete file from storage
                instance.profile_picture = None
            else:
                # Update the image
                instance.profile_picture = validated_data.get("profile_picture", instance.profile_picture)
        
        # Update other fields
        instance.full_name = validated_data.get("full_name", instance.full_name)
        instance.address = validated_data.get("address", instance.address)
        # Update other fields...
        
        instance.save()
        return instance

# --- NEW: Complaint Detail Serializer ---
class ComplaintDetailSerializer(serializers.ModelSerializer):
    citizen = CitizenSerializer(read_only=True)
    municipality = MunicipalitySerializer(read_only=True)

    photo_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    voice_record_url = serializers.SerializerMethodField()
    evidence_url = serializers.SerializerMethodField()

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "subject",
            "description",
            "status",
            "status_display",
            "created_at",
            "updated_at",
            "comment",
            "citizen",
            "municipality",
            "photo_url",
            "video_url",
            "voice_record_url",
            "evidence_url",
        ]
        read_only_fields = fields

    def _get_absolute_url(self, field):
        request = self.context.get("request")
        if field and hasattr(field, "url"):
            try:
                return request.build_absolute_uri(field.url)
            except Exception as e:
                print(f"Error building absolute URI for {field.name}: {e}")
                return None
        return None

    def get_photo_url(self, obj):
        return self._get_absolute_url(obj.photo)

    def get_video_url(self, obj):
        return self._get_absolute_url(obj.video)

    def get_voice_record_url(self, obj):
        return self._get_absolute_url(obj.voice_record)

    def get_evidence_url(self, obj):
        return self._get_absolute_url(obj.evidence)