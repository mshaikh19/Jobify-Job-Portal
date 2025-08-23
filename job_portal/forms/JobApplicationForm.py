from django import forms

from job_portal.models import Application


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'custom_answers']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
            'custom_answers': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'custom_answers':  # This is hidden, don't style it
                field.widget.attrs.update({
                    'class': 'w-full mt-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-dark-blue focus:outline-none'
                })
