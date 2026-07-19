from django.contrib import admin
from django.utils.html import format_html
from .models import *
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

# Register your models here.
admin.site.register(Province)
admin.site.register(District)
admin.site.register(SavedRoom)
admin.site.register(Advertisement)

class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 0
    fields = ['image_preview', 'image', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


class VerificationDocumentInline(admin.StackedInline):
    model = VerificationDocument
    extra = 0
    can_delete = False
    readonly_fields = ['doc_previews']
    fields = ['doc_previews', 'is_verified', 'verified_by', 'verified_at']

    def doc_previews(self, obj):
        files = [obj.citizenship_front, obj.citizenship_back, obj.lalpurja, obj.selfie]
        files = [f for f in files if f]
        if not files:
            return "-"
        return format_html_join(
            '',
            '<img src="{}" style="height:100px;margin:4px;" />',
            ((f.url,) for f in files)
        )
    doc_previews.short_description = "Documents"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'is_verified', 'created_at']
    list_filter = ['status', 'is_verified', 'room_type']
    inlines = [RoomImageInline, VerificationDocumentInline]

