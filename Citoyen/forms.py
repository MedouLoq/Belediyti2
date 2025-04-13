# citizens/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Citizen, Problem, Complaint, Category

# --- Base CSS Classes ---
text_input_css = 'form-input block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition duration-150 ease-in-out'
select_css = 'form-select block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition duration-150 ease-in-out'
textarea_css = 'form-textarea block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition duration-150 ease-in-out'
checkbox_css = 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-150 ease-in-out'
file_input_css = 'form-input block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer'


# --- Forms ---

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': text_input_css, 'placeholder': 'Nom d\'utilisateur ou Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': text_input_css, 'placeholder': 'Mot de passe'})
    )

class CitizenRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label="Nom complet", widget=forms.TextInput(attrs={'class': text_input_css}))
    phone = forms.CharField(max_length=50, required=False, label="Téléphone", widget=forms.TextInput(attrs={'class': text_input_css}))
    address = forms.CharField(max_length=255, required=False, label="Adresse", widget=forms.TextInput(attrs={'class': text_input_css}))
    email = forms.EmailField(required=True, label="Email", widget=forms.EmailInput(attrs={'class': text_input_css}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'full_name', 'phone', 'address')
        widgets = {
            'username': forms.TextInput(attrs={'class': text_input_css}),
            'email': forms.EmailInput(attrs={'class': text_input_css}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'CITIZEN'
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            Citizen.objects.update_or_create(
                user=user,
                defaults={
                    'full_name': self.cleaned_data.get('full_name', ''),
                    'phone': self.cleaned_data.get('phone'),
                    'address': self.cleaned_data.get('address')
                }
            )
        return user


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
            'description': forms.Textarea(attrs={'class': textarea_css, 'rows': 4, 'placeholder': 'Décrivez le problème en détail...'}),
            'photo': forms.ClearableFileInput(attrs={'class': file_input_css}),
            'location': forms.TextInput(attrs={'class': text_input_css, 'placeholder': 'Ex: Devant la boulangerie, Rue de la Paix', 'readonly': True }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_category(self):
        category = self.cleaned_data.get('category')
        return category


from django import forms
from .models import Complaint, Municipality

class ComplaintForm(forms.ModelForm):
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg'}),
        label="Municipalité",
        required=True
    )

    class Meta:
        model = Complaint
        fields = ['subject', 'description', 'evidence', 'municipality']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg',
                'placeholder': 'Objet de la réclamation'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea block w-full px-4 py-3 leading-tight text-gray-700 bg-gray-50 border border-gray-300 rounded-lg',
                'rows': 4,
                'placeholder': 'Décrivez votre réclamation...'
            }),
            'evidence': forms.ClearableFileInput(attrs={
                'class': 'form-input block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer'
            }),
        }

    def clean_municipality(self):
        # Additional cleaning (if needed)
        return self.cleaned_data.get('municipality')


class CitizenProfileForm(forms.ModelForm):
    class Meta:
        model = Citizen
        fields = ['full_name', 'phone', 'address']
        widgets = {
           
            'full_name': forms.TextInput(attrs={'class': text_input_css}),
            'phone': forms.TextInput(attrs={'class': text_input_css}),
            'address': forms.TextInput(attrs={'class': text_input_css}),
        }