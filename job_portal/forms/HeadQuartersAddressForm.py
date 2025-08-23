from django import forms

from job_portal.models import HeadQuartersAddress


class HeadQuartersAddressForm(forms.ModelForm):
    class Meta:
        model = HeadQuartersAddress
        fields = ['street_address', 'city', 'state', 'country']

        widgets = {
            'street_address': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
            'country': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any customizations to form fields (e.g., adding CSS classes)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'})
