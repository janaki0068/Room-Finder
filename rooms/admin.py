from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Province)
admin.site.register(District)
admin.site.register(SavedRoom)
admin.site.register(Advertisement)

class VerificationDocumentInline(admin.StackedInline):
    model = VerificationDocument
    extra = 0
    can_delete = False


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    inlines = [VerificationDocumentInline]

