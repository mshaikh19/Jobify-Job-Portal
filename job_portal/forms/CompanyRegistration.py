from django import forms

from job_portal.models import Company, Location


class CompanyFormStep1(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "description", "website", "industry", "founded", "company_size"]

class CompanyFormStep2(forms.ModelForm):
    class Meta:
        model = Company
        fields = []

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = []
        
