from .models import Message
from .models import RentRequest


def unread_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
    else:
        count = 0
    return {'unread_count': count}


def landlord_notifications(request):
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'landlord':
        pending_rent_count = RentRequest.objects.filter(
            room__owner=request.user, status='pending'
        ).count()
    else:
        pending_rent_count = 0
    return {'pending_rent_count': pending_rent_count}