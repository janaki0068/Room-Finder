from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from rooms.models import Room
from django.contrib.auth.models import User

# Create your views here.


@staff_member_required
def admin_dashboard(request):
    context = {
        "pending_count": Room.objects.filter(status="pending").count(),
        "approved_count": Room.objects.filter(status="approved").count(),
        "rejected_count": Room.objects.filter(status="rejected").count(),
        "total_users": User.objects.count(),
    }
    return render(request, "adminpanel/dashboard.html", context)


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



@staff_member_required
def user_management(request):
    role_filter = request.GET.get('role', 'all')

    users = User.objects.exclude(is_staff=True).select_related('profile') 

    if role_filter == 'tenant':
        users = users.filter(profile__is_landlord=False)
    elif role_filter == 'landlord':
        users = users.filter(profile__is_landlord=True)

    return render(request, "adminpanel/user_management.html", {
        "users": users,
        "role_filter": role_filter,
        })


@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.delete()
    return redirect("user_management")

