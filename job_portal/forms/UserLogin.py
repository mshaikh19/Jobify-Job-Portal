from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from job_portal.models import CustomUser


class UserLoginForm(AuthenticationForm):
    # username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white',
            'placeholder': 'Email'
        })
    )
    password = forms.CharField(
        
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white',
            'placeholder': 'Password'
        })
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user_obj = CustomUser.objects.get(email=email)
                print(f"🎯 Found user: {user_obj}")
                print(f"🧪 Authenticating with username={user_obj.username} and password={password}")

                user = authenticate(username=user_obj.username, password=password)
                print(user)
                if user is None:
                    raise forms.ValidationError("Incorrect email or password.")
                print(f"🧪 User Authenticated")
                # self._user = user
                self.user_cache = user

            except CustomUser.DoesNotExist:
                raise forms.ValidationError("No user found with this email.")
        return self.cleaned_data

    class Meta:
        model = CustomUser
        fields = ['username', 'password']
