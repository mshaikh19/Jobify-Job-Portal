from django import forms
from django.contrib.auth.forms import UserCreationForm

from job_portal.models import CustomUser


class UserRegistrationForm(UserCreationForm):
    # Explicitly declare required fields
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_first_name',
            'autocomplete': 'on'
        })
    )
    
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_last_name',
            'autocomplete': 'on'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'id_email',
            'autocomplete': 'on'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Password fields configuration
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control password-input',
            'placeholder': 'Create password (min 8 characters)',
            'autocomplete': 'new-password'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control password-input',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })

class UserRegistrationFormForCompany(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "id": "id_email",
            "autocomplete": "on",
            "placeholder": "Enter your email"
        })
    )

    class Meta:
        model = CustomUser
        fields = [ "email", "password1", "password2", "profile_picture"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update({
            "class": "form-control password-input",
            "placeholder": "Create password (min 8 characters)",
            "autocomplete": "new-password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control password-input",
            "placeholder": "Confirm your password",
            "autocomplete": "new-password"
        })

    def clean_email(self):
        """Validate that the email is unique before saving"""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email