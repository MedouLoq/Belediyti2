from django import forms
from Citoyen.models import Municipality
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.template.loader import render_to_string

class MunicipalityForm(forms.ModelForm):
    class Meta:
        model = Municipality
        fields = ['name', 'latitude', 'longitude', 'boundary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la municipalité')}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Latitude'), 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Longitude'), 'step': 'any'}),
            'boundary': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('GeoJSON des limites'), 'rows': 3}),
        }
        labels = {
            'name': _('Nom'),
            'latitude': _('Latitude'),
            'longitude': _('Longitude'),
            'boundary': _('Limites géographiques (GeoJSON)'),
        }
    
    def as_json(self):
        """Generate HTML form content without requiring a separate template"""
        csrf_token = '<input type="hidden" name="csrfmiddlewaretoken" value="{% csrf_token %}">'
        
        # Determine the form action URL based on whether it's a new or existing municipality
        if self.instance.pk:
            action = f'/superadmin/municipality/update/{self.instance.pk}/'
        else:
            action = '/superadmin/municipality/create/'
            
        # Start form HTML
        html = f'<form id="municipalityForm" method="post" action="{action}">{csrf_token}'
        
        # Add non-field errors if any
        if self.non_field_errors():
            html += '<div class="alert alert-danger">'
            for error in self.non_field_errors():
                html += f'<div>{error}</div>'
            html += '</div>'
        
        # Add form fields
        for field_name, field in self.fields.items():
            field_instance = self[field_name]
            html += '<div class="mb-3">'
            html += f'<label for="{field_instance.id_for_label}" class="form-label">{field_instance.label}</label>'
            html += str(field_instance)
            
            # Add field errors if any
            if field_instance.errors:
                html += '<div class="text-danger">'
                for error in field_instance.errors:
                    html += f'<small>{error}</small>'
                html += '</div>'
            
            # Add help text if any
            if field_instance.help_text:
                html += f'<small class="form-text text-muted">{field_instance.help_text}</small>'
            
            html += '</div>'
        
        # Add submit button
        html += '''
        <div class="mt-4 d-flex justify-content-end">
            <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">''' + _("Annuler") + '''</button>
            <button type="submit" class="btn btn-primary">''' + _("Enregistrer") + '''</button>
        </div>
        '''
        
        # Close form
        html += '</form>'
        
        return html