from django import forms
from django.contrib.auth.forms import User
from .models import *
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator

# Register
class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone_number = forms.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^9\d{9}$',
                message="Enter a valid 10-digit phone number (e.g. 98XXXXXXXX)."
            )
        ]
    )
    role = forms.ChoiceField(
        choices=[
            ('landlord', 'Landlord'),
            ('tenant', 'Tenant')
        ]
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

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
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ['image', 'phone']  # keep whatever fields you already have
        widgets = {
            'image': forms.FileInput(attrs={
                'id': 'id_image',
                'class': 'hidden-file-input',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone', 'bio']  # keep your existing fields
        widgets = {
            'image': forms.FileInput(attrs={
                'id': 'id_image',
                'class': 'hidden-file-input',
            }),
        }