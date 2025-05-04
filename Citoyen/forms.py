# citizens/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from .models import User, Citizen, Problem, Complaint, Category, Municipality
from django.utils.translation import gettext_lazy as _
import re # For phone number validation

# --- Base CSS Classes ---
text_input_css = 'form-input block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition duration-150 ease-in-out'
select_css = 'form-select block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition duration-150 ease-in-out'
textarea_css = 'form-textarea block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition duration-150 ease-in-out'
checkbox_css = 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-150 ease-in-out'
file_input_css = 'form-input block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer'


# --- Authentication Forms ---

class LoginForm(forms.Form):
    # Changed placeholder to reflect new login options
    identifier = forms.CharField(
        label=_("Numéro de téléphone ou Email"),
        max_length=254,
        widget=forms.TextInput(attrs={'class': text_input_css, 'placeholder': _('Numéro de téléphone ou Email')})
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={'class': text_input_css, 'placeholder': _('Mot de passe')})
    )

class CitizenRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label=_("Nom complet"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': text_input_css, 'placeholder': _('Votre nom complet')})
    )
    phone_number = forms.CharField(
        label=_("Numéro de téléphone"),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': text_input_css, 'placeholder': _('Ex: 22xxxxxx')})
    )
    nni = forms.CharField(
        label=_("NNI (Numéro National d'Identité)"),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': text_input_css, 'placeholder': _('Votre NNI')})
    )
    municipality = forms.ModelChoiceField(
        label=_("Municipalité de résidence"),
        queryset=Municipality.objects.all().order_by('name'),
        required=True,
        widget=forms.Select(attrs={'class': select_css})
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={'class': text_input_css, 'placeholder': _('Choisissez un mot de passe')}),
        required=True
    )
    password_confirm = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={'class': text_input_css, 'placeholder': _('Confirmez votre mot de passe')}),
        required=True
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Basic validation: check if it contains only digits and is within a reasonable length
        if not re.match(r'^\d{8,}$', phone): # Example: At least 8 digits
            raise forms.ValidationError(_("Numéro de téléphone invalide. Utilisez uniquement des chiffres (minimum 8)."))
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(_("Ce numéro de téléphone est déjà utilisé."))
        return phone

    def clean_nni(self):
        nni = self.cleaned_data.get('nni')
        # Basic validation: check if it contains only digits and is 10 digits long (adjust as needed)
        if not re.match(r'^\d{10}$', nni): # Example: Exactly 10 digits
            raise forms.ValidationError(_("NNI invalide. Il doit contenir 10 chiffres."))
        if Citizen.objects.filter(nni=nni).exists():
            raise forms.ValidationError(_("Ce NNI est déjà utilisé."))
        return nni

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', _("Les mots de passe ne correspondent pas."))

        return cleaned_data

    def save(self, commit=True):
        if not commit:
            # This form doesn't support commit=False easily as it creates two objects
            raise NotImplementedError("commit=False not supported")

        phone_number = self.cleaned_data['phone_number']
        password = self.cleaned_data['password']
        full_name = self.cleaned_data['full_name']
        nni = self.cleaned_data['nni']
        municipality = self.cleaned_data['municipality']

        # Create User using the custom manager
        user = User.objects.create_user(
            identifier=phone_number,
            password=password,
            user_type='CITIZEN'
        )

        # Create Citizen profile
        Citizen.objects.create(
            user=user,
            full_name=full_name,
            nni=nni,
            municipality=municipality
        )
        return user

# --- Problem/Complaint Forms (Keep existing ones, update if needed) ---

class ProblemReportForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = Problem
        fields = ['description', 'photo', 'location', 'latitude', 'longitude', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'class': textarea_css, 'rows': 4, 'placeholder': _('Décrivez le problème en détail...')}),
            'photo': forms.ClearableFileInput(attrs={'class': file_input_css}),
            'location': forms.TextInput(attrs={'class': text_input_css, 'placeholder': _('Ex: Devant la boulangerie, Rue de la Paix'), 'readonly': True }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_category(self):
        category = self.cleaned_data.get('category')
        return category

class ComplaintForm(forms.ModelForm):
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': select_css}),
        label="Municipalité",
        required=True
    )

    class Meta:
        model = Complaint
        fields = ['subject', 'description', 'evidence', 'municipality']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': text_input_css,
                'placeholder': _('Objet de la réclamation')
            }),
            'description': forms.Textarea(attrs={
                'class': textarea_css,
                'rows': 4,
                'placeholder': _('Décrivez votre réclamation...')
            }),
            'evidence': forms.ClearableFileInput(attrs={
                'class': file_input_css
            }),
        }

    def clean_municipality(self):
        # Additional cleaning (if needed)
        return self.cleaned_data.get('municipality')

# --- Profile Forms ---

class CitizenProfileForm(forms.ModelForm):
    # Add email field from User model if needed for display/update (optional)
    # email = forms.EmailField(label=_("Email (optionnel)"), required=False, widget=forms.EmailInput(attrs={'class': text_input_css}))

    class Meta:
        model = Citizen
        # Removed 'phone' as it's now on User model
        fields = ['full_name', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': text_input_css}),
            'address': forms.TextInput(attrs={'class': text_input_css}),
        }

    # If allowing email update:
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if self.instance and self.instance.user:
    #         self.fields['email'].initial = self.instance.user.email

    # def save(self, commit=True):
    #     citizen = super().save(commit=commit)
    #     if commit and 'email' in self.cleaned_data:
    #         citizen.user.email = self.cleaned_data['email']
    #         citizen.user.save()
    #     return citizen

# Add forms for Admin/Superadmin if needed, e.g., password change


