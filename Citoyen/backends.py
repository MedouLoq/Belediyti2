# Citoyen/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class PhoneOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # The `username` argument from authenticate() might be phone or email
        identifier = username # Rename for clarity

        if not identifier:
            return None

        # Try to find a user matching the identifier as either phone_number or email
        # We use Q objects to create an OR query
        try:
            user = UserModel.objects.get(Q(phone_number=identifier) | Q(email__iexact=identifier))
        except UserModel.DoesNotExist:
            # If no user is found with the identifier as phone or email, return None
            # Django will then try the next backend in AUTHENTICATION_BACKENDS
            return None
        except UserModel.MultipleObjectsReturned:
            # This shouldn't happen if phone_number and email are unique, but handle defensively
            return None

        # Check the password
        if user.check_password(password):
            # Check if the user is active
            if self.user_can_authenticate(user):
                return user

        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

