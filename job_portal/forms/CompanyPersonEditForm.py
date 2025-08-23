from django import forms
from django.core.exceptions import ValidationError

from job_portal.models import CompanyPerson, CustomUser


class CompanyPersonEditForm(forms.ModelForm):
    class Meta:
        model = CompanyPerson
        fields = ['linkedin_profile', 'position']
        widgets = {
            'linkedin_profile': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'position': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            })


class CustomUserFormForCompanyPerson(forms.ModelForm):
    
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name',  'profile_picture']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', None)
        
        # Ensure that phone_number is not None
        if phone_number is None:
            raise forms.ValidationError("Phone number is required.")

        # If phone_number is not None, proceed with the length check
        if len(phone_number) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        
        # If valid, return the phone number
        return phone_number


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            })
