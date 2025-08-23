from django import forms

from job_portal.models import CustomUser


class PhoneVerificationForm(forms.Form):
    country_code = forms.ChoiceField(
        choices=[('+1', 'USA (+1)'), ('+91', 'India (+91)'), ('+44', 'UK (+44)')],  # Add more as needed
        initial='+1',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'width: 100px; display: inline-block;'
        })
    )
     
    phone_number = forms.CharField(
        max_length=10, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '1234567890',
            'class': 'form-control'
        })
    )
    otp = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter OTP',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Remove request from kwargs
        super().__init__(*args, **kwargs)
    
    def clean_phone_number(self):
        country_code = self.cleaned_data.get('country_code')
        phone_number = self.cleaned_data['phone_number']
        if country_code and phone_number:
            # Combine and validate full phone number
            full_phone = f"{country_code}{phone_number}"
            if not full_phone.startswith('+'):
                raise forms.ValidationError("Phone number must include country code")
            
            # Store the combined phone number
            self.cleaned_data['full_phone'] = full_phone

            # Check if phone exists (only during OTP sending)
            if 'send_otp' in self.data:
                user_id = self.request.session.get('registering_user_id')
                if user_id and CustomUser.objects.exclude(id=user_id).filter(phone_number=full_phone).exists():
                     self.add_error('phone_number', 'This phone number is already registered')
        return full_phone