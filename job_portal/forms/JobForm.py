from django import forms

from job_portal.models import Job, Location


class JobForm(forms.ModelForm):
    application_deadline = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
        }),
        required=True
    )
    expected_start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
        }),
        required=True
    )

    class Meta:
        model = Job
        fields = [
            'title',
            'job_type',
            'job_language',
            'work_location_type',
            'number_of_people',
            'salary',
            'description',
            'company_goal',
            'work_environment',
            'requirements',
            'additional_questions',
            'application_deadline',
            'expected_start_date',
            'experience_required'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Frontend Developer',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'job_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'job_language': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'work_location_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'number_of_people': forms.NumberInput(attrs={
                'placeholder': 'e.g. 5',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'experience_required': forms.NumberInput(attrs={
                'placeholder': 'e.g. 5 (in years)',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'salary': forms.NumberInput(attrs={
                'placeholder': 'e.g. 70000',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe job responsibilities...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'company_goal': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter company goals...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'work_environment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe the work environment...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'requirements': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'List job requirements...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'additional_questions': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'One question per line...',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
        }



class LocationFormForJob(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['address', 'city', 'state', 'country']
        widgets = {
            'address': forms.TextInput(attrs={
                'placeholder': 'Enter address',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'Enter city',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'state': forms.TextInput(attrs={
                'placeholder': 'Enter state',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
            'country': forms.TextInput(attrs={
                'placeholder': 'Enter country',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
            }),
        }