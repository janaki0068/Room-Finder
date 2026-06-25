from django import forms
from django.contrib.auth.forms import User
from .models import Room

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
            'furnished',
            'parking',
            'has_bike_parking',
            'has_drinking_water',
            'has_water_24_7',
            'has_balcony',
            'has_security_guard',
            'has_cctv',
            'pet_allowed',
            'has_laundry',
        ]