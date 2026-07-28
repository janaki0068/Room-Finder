from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import random
from django.conf import settings


# Create your models here.

# PROVINCE
class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# DISTRICTS
class District(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('province', 'name')

    def __str__(self):
        return self.name


# PROFILE
class Profile(models.Model):
    ROLE_CHOICES = [
        ('tenant', 'Tenant'),
        ('landlord', 'Landlord'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tenant')
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# EMAIL VERIFICATION
class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))


# ROOMS
class Room(models.Model):
    ROOM_TYPES = [
        ("flat", "Flat"),
        ("single", "Single Room"),
        ("2 rooms", "2 Rooms"),
        ("apartment", "Apartment"),
        ("house", "House"),
        ("hostel", "Hostel"),
        ("office space", "Office Spaces"),
        ("shutter", "Shutter"),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('rented', 'Rented'),
    ]

    FURNISHED_CHOICES = [
        ('furnished', 'Furnished'),
        ('unfurnished', 'Unfurnished'),
        ('semi', 'Semi-Furnished'),
    ]

    # ownership
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rooms")

    # basic info
    title = models.CharField(max_length=200)
    description = models.TextField(help_text='Minimum 100 characters')
    room_type = models.CharField(
        max_length=20, choices=ROOM_TYPES, default="flat")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    is_verified = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)

    # location
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, help_text='City or VDC')
    area = models.CharField(max_length=100, blank=True,
                            help_text='Area / Tole')
    address = models.CharField(max_length=255)
    ward_number = models.PositiveSmallIntegerField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    # pricing
    price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text='Monthly rent in NPR')
    security_deposit = models.PositiveIntegerField(
        default=0, help_text='Security deposit in NPR')

    # bills
    bill_water = models.BooleanField(default=False)
    bill_electricity = models.BooleanField(default=False)
    bill_internet = models.BooleanField(default=False)

    # facilities
    wifi = models.BooleanField(default=False)
    attached_bathroom = models.BooleanField(default=False)
    furnished_status = models.CharField(
        max_length=15, choices=FURNISHED_CHOICES, default='unfurnished')
    parking = models.BooleanField(default=False)
    has_bike_parking = models.BooleanField(default=False)
    has_drinking_water = models.BooleanField(default=False)
    has_water_24_7 = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    has_security_guard = models.BooleanField(default=False)
    has_cctv = models.BooleanField(default=False)
    pet_allowed = models.BooleanField(default=False)
    has_laundry = models.BooleanField(default=False)
    has_kitchen = models.BooleanField(default=False)

    # stats
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    rented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rented_rooms')
    rented_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        if self.district.province != self.province:
            raise ValidationError(
                "District does not belong to selected province."
            )

    @property
    def saved_count(self):
        return self.saved_by.count()

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

        

class RoomImage(models.Model):
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rooms/gallery/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.room.title}"


# SAVED ROOMS
class SavedRoom(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_rooms')
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "room")
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} - {self.room.title}"


# IDENTITY VERIFICATION
class VerificationDocument(models.Model):
    room = models.OneToOneField(
        Room, on_delete=models.CASCADE, related_name="documents")
    citizenship_front = models.ImageField(upload_to="documents/")
    citizenship_back = models.ImageField(upload_to="documents/")
    lalpurja = models.ImageField(upload_to="documents/")
    selfie = models.ImageField(upload_to="documents/")

    # Verification fields
    is_verified = models.BooleanField(default=False)

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents"
    )

    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Documents for {self.room.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.is_verified:
            self.room.is_verified = True
            self.room.status = "active"
        else:
            self.room.is_verified = False
            self.room.status = "pending"

        self.room.save()



class SavedRoom(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_rooms')
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)   # NEW

    class Meta:
        unique_together = ("user", "room")
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} - {self.room.title}"

# MESSAGES
class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages')
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"From{self.sender.username} → {self.receiver.username}"


# SETTINGS
class UserPreference(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    notify_booking = models.BooleanField(default=True)
    notify_messages = models.BooleanField(default=True)
    notify_listing_status = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=True)
    show_email = models.BooleanField(default=False)

    def __str__(self):
        return f"Preferences for {self.user}"


class Advertisement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='ads/', blank=True, null=True)
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title