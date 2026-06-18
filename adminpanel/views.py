from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from rooms.models import Room

# Create your views here.


@staff_member_required
def pending_listings(request):
    listings = Room.objects.filter(status="pending")
    return render(request, "adminpanel/pending_listings.html", {"listings": listings})

@staff_member_required
def approved_listings(request):
    listings = Room.objects.filter(status="approved")
    return render(request, "adminpanel/approved_listings.html", {"listings": listings})

@staff_member_required
def rejected_listings(request):
    listings = Room.objects.filter(status="rejected")
    return render(request, "adminpanel/rejected_listings.html", {"listings": listings})

@staff_member_required
def approve_listing(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.status = "approved"
    room.rejection_reason = ""
    room.save()
    return redirect("pending_listings")


@staff_member_required
def reject_listing(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == "POST":
        reason = request.POST.get('reason', '')
        room.status = "rejected"
        room.rejection_reason = reason
        room.save()
        return redirect("pending_listings")
    
    return render(request, "adminpanel/reject_listing.html", {"room": room})