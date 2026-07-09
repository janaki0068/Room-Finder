from django import forms
from django.contrib.auth.forms import User
from .models import *

# Register
class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=10)
    role = forms.ChoiceField(
        choices=[
            ('landlord', 'Landlord'),
            ('tenant', 'Tenant')
        ]
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
    
# Room
class RoomForm(forms.ModelForm):

    class Meta:
        model = Room

        fields = [
            # Basic Info
            'title',
            'description',
            'room_type',

            # Location
            'province',
            'district',
            'city',
            'area',
            'address',
            'ward_number',
            'latitude',
            'longitude',

            # Pricing
            'price',
            'security_deposit',

            # Bills
            'bill_water',
            'bill_electricity',
            'bill_internet',

            # Facilities
            'wifi',
            'attached_bathroom',
            'furnished_status',
            'parking',
            'has_bike_parking',
            'has_drinking_water',
            'has_water_24_7',
            'has_balcony',
            'has_security_guard',
            'has_cctv',
            'pet_allowed',
            'has_laundry',
            'has_kitchen',
        ]

class UserPreferenceForm(forms.ModelForm):

    class Meta:
        model = UserPreference
        fields = [
            "notify_booking",
            "notify_messages",
            "notify_listing_status",
            "show_phone",
            "show_email",
        ]

class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = ['phone', 'image']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
            profile.save()
        return profile
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }