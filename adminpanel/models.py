from django.db import models
from django.utils import timezone

# Create your models here.
class Ad(models.Model):
    PLACEMENT_CHOICES = [
        ("homepage_banner", "Homepage Banner"),
        ("sidebar", "Sidebar"),
        ("listing_page", "Listing Page"),
    ]
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='ads/')
    redirect_url = models.URLField(blank=True)
    placement = models.CharField(max_length=30, choices=PLACEMENT_CHOICES, default="homepage_banner")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    @property
    def is_running(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    @property
    def status_label(self):
        now = timezone.now()
        if not self.is_active:
            return "disabled"
        if now < self.start_date:
            return "scheduled" 
        if now > self.end_date:
            return "expired"
        return "running"