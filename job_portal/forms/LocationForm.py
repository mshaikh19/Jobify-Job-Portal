from django import forms
from job_portal.models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['address', 'city', 'state', 'country']  # Do not include 'id'

        widgets = {
            'address': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'country': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally, you can add any additional customization to form fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'})

# Formset for Location (no need to manually include 'id' in the form)
LocationFormSet = forms.modelformset_factory(Location, form=LocationForm, extra=0, can_delete=True)
