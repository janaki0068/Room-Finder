from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# PROVINCE
class Province(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# DISTRICTS
class District(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# ROOMS
class Room(models.Model):
    ROOM_TYPES = [
        ("flat","Flat"),
        ("single","Single Room"),
        ("2 rooms","2 Rooms"),
        ("apartment","Apartment"),
        ("house","House"),
        ("hostel","Hostel"),
        ("office space","Office Spaces"),
        ("shutter","Shutter"),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    title = models.CharField(max_length=200)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default="flat")
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_verified = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False) 
    attached_bathroom = models.BooleanField(default=False) 
    furnished = models.BooleanField(default=False) 
    parking = models.BooleanField(default=False) 
    address = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
# SAVED ROOMS
class SavedRoom(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user","room")

    def __str__(self):
        return f"{self.user.username} - {self.room.title}"
    
