from django import forms

from job_portal.models.Company import Company
from job_portal.models.CustomUserModel import CustomUser


class CompanyEditForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 
            'description', 
            'website', 
            'industry',
            'founded', 
            'company_size', 
            'linkedin_profile',
            'tagline', 
            'registration_number', 
            'business_license', 
            'company_policy_link'
        ]

        widgets = {
            'business_license': forms.ClearableFileInput(attrs={'multiple': False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any customizations to form fields (e.g., adding CSS classes)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'})


class CustomUserFormForCompany(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'profile_picture']
        
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can add any customizations here if needed
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'})
