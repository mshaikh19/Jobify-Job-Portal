from django import forms

from job_portal.models import JobSeekerProfile


class Step1BasicInfoForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['desired_position', 'location_preference', 'onsite_location']
        widgets = {
            'desired_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Python Developer, UI/UX Designer'
            }),
            'onsite_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preferred city/country if onsite'
            }),
        }

class Step2SkillsForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['skills', 'work_experience']
        widgets = {
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your skills separated by commas',
                'rows': 3
            }),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your work experience',
                'rows': 5
            }),
        }

class Step3EducationForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['education', 'expected_salary', 'resume']
        widgets = {
            'education': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your educational qualifications',
                'rows': 3
            }),
            'expected_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expected salary (per annum)'
            }),
        }