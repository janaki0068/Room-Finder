from django import forms
from .models import Ad

class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'description', 'image', 'redirect_url', 'placement', 'start_date', 'end_date', 'is_active']
        widgets = {
            "title": forms.TextInput(attrs={"class": "ad-input"}),
            "description": forms.Textarea(attrs={"class": "ad-input", "rows": 4}),
            "image": forms.ClearableFileInput(attrs={"class": "ad-input-file"}),
            "redirect_url": forms.URLInput(attrs={"class": "ad-input"}),
            "placement": forms.Select(attrs={"class": "ad-input"}),
            "start_date": forms.DateTimeInput(attrs={"class": "ad-input", "type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"class": "ad-input", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "ad-checkbox"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')

        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned