from django import forms

from job_portal.models import CompanyPerson, CustomUser


class CustomUserFormForTeamMember(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'profile_picture', 'phone_number']
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
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', None)
        
        if phone_number is None:
            raise forms.ValidationError("Phone number is required.")
        
        if len(phone_number) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        
        return phone_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Form Fields:", list(self.fields.keys()))
        for name, field in self.fields.items():

            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            })


class AddTeamMemberForm(forms.ModelForm):
    class Meta:
        model = CompanyPerson
        fields = ['position', 'linkedin_profile', 'is_admin']
        widgets = {
            'position': forms.Select(choices=CompanyPerson.POSITION_CHOICES, attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'linkedin_profile': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'is_admin': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-dark-blue focus:ring-dark-blue border-gray-300 rounded'
            }),
        }

    
