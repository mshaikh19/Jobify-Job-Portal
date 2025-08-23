from django import forms

from job_portal.models.Address import Address
from job_portal.models.Certifications import Certification
from job_portal.models.CustomUserModel import CustomUser
from job_portal.models.Education import Education
from job_portal.models.Experience import Experience
from job_portal.models.JobSeeker import JobSeekerProfile
from job_portal.models.SchoolAddres import SchoolAddress


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['street_address', 'city', 'state', 'country']
        widgets = {
            'street_address': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'country': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }


class SchoolAddressForm(forms.ModelForm):
    class Meta:
        model = SchoolAddress
        fields = ['school_name', 'school_city', 'school_state', 'school_country']
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'school_city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'school_state': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'school_country': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }


# class EducationForm(forms.ModelForm):
#     class Meta:
#         model = Education
#         fields = ['level', 'field', 'currently_enrolled', 'start_year', 'end_year']
#         widgets = {
#             'level': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
#             'field': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
#             'currently_enrolled': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
#             'start_year': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
#             'end_year': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
#         }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['level' , 'field' , 'currently_enrolled' , 'start_year' , 'end_year' ]
        widgets = {
            'level': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'field': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'currently_enrolled': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'start_year': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'end_year': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        # Pop `school_address_instance` if passed in
        school_address_instance = kwargs.pop('school_address_instance', None)
        super().__init__(*args, **kwargs)
        
        # Create nested school address form
        self.school_address_form = SchoolAddressForm(
            instance=school_address_instance or getattr(self.instance, 'school_address', None)
        )

    def is_valid(self):
        return super().is_valid() and self.school_address_form.is_valid()

    def save(self, commit=True):
        education = super().save(commit=False)
        school_address = self.school_address_form.save(commit=commit)
        education.school_address = school_address

        if commit:
            education.save()

        return education


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        exclude = ['user', 'certificates', 'experiences' , 'resume' , 'address']
        widgets = {
            'gender': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'age': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'about': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none', 'rows': 4}),
            'location_preference': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'onsite_location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'skills': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'work_experience': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'desired_position': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'relocation': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'job_type': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'profile_visibility': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'certificate_file']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none',
                'placeholder': 'Certification Name'
            }),
            'certificate_file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-600 file\:mr-4 file\:py-2 file\:px-4 file\:rounded-full file\:border-0 file\:text-sm file\:bg-blue-100 file\:text-blue-700 hover\:file\:bg-blue-200'
            }),
        }


class CustomUserFormForJobSeeker(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name' , 'last_name' , 'email', 'profile_picture']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['position', 'company', 'start_date', 'end_date', 'description']

        widgets = {
            'position': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none',
                'placeholder': 'Job Title'
            }),
            'company': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none',
                'placeholder': 'Company Name'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus\:ring-2 focus\:ring-dark-blue focus\:outline-none',
                'placeholder': 'Describe your role and achievements'
            }),
        }

# Optional: For inline multiple entries if used in template
CertificationFormSet = forms.modelformset_factory(Certification, form=CertificationForm, extra=1, can_delete=True)
WorkExperienceFormSet = forms.modelformset_factory(Experience, form=WorkExperienceForm, extra=1, can_delete=True)
