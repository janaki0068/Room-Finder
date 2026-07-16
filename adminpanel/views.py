from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from rooms.models import Room
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import Ad
from .forms import AdForm
from django.contrib import messages

# Create your views here.


@staff_member_required
def admin_dashboard(request):
    context = {
        "pending_count": Room.objects.filter(status="pending").count(),
        "active_count": Room.objects.filter(status="active").count(),
        "rented_count": Room.objects.filter(status="rented").count(),
        "rejected_count": Room.objects.filter(status="rejected").count(),
        "total_users": User.objects.count(),
        "active_ads_count": Ad.objects.filter(is_active=True).count(),
    }
    return render(request, "adminpanel/dashboard.html", context)


@staff_member_required
def pending_listings(request):
    listings = Room.objects.filter(status="pending")
    return render(request, "adminpanel/pending_listings.html", {"listings": listings})


@staff_member_required
def active_listings(request):
    listings = Room.objects.filter(status="active")
    return render(request, "adminpanel/active_listings.html", {"listings": listings})


@staff_member_required
def rented_listings(request):
    listings = Room.objects.filter(status="rented")
    return render(request, "adminpanel/rented_listings.html", {"listings": listings})


@staff_member_required
def rejected_listings(request):
    listings = Room.objects.filter(status="rejected")
    return render(request, "adminpanel/rejected_listings.html", {"listings": listings})


@staff_member_required
def approve_listing(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.status = "active"
    room.is_verified = True
    room.rejection_reason = ""
    room.save()
    return redirect("pending_listings")


@staff_member_required
def reject_listing(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == "POST":
        reason = request.POST.get('reason', '')
        room.status = "rejected"
        room.is_verified = False
        room.rejection_reason = reason
        room.save()
        return redirect("pending_listings")

    return render(request, "adminpanel/reject_listing.html", {"room": room})


@staff_member_required
def user_management(request):
    role_filter = request.GET.get('role', 'all')

    users = User.objects.exclude(is_staff=True).select_related('profile')

    if role_filter == 'tenant':
        users = users.filter(profile__role='tenant')
    elif role_filter == 'landlord':
        users = users.filter(profile__role='landlord')

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


def custom_logout(request):
    logout(request)
    return redirect('login')

@staff_member_required
def ad_list(request):
    status_filter = request.GET.get('status', 'all')
    ads = Ad.objects.all()

    if status_filter != 'all':
        ads = [ad for ad in ads if ad.status_label == status_filter]

    return render(request, "adminpanel/ad_list.html", {
        "ads": ads,
        "status_filter": status_filter,
    })

@staff_member_required
def ad_create(request):
    if request.method == "POST":
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Ad created successfully.")
            return redirect("ad_list")
    else:
        form = AdForm()
    return render(request, "adminpanel/ad_form.html", {"form": form, "editing": False})


@staff_member_required
def ad_edit(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if request.method == "POST":
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, "Ad updated successfully.")
            return redirect("ad_list")
    else:
        form = AdForm(instance=ad)
    return render(request, "adminpanel/ad_form.html", {"form": form, "editing": True})


@staff_member_required
def ad_toggle(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if request.method == "POST":
        ad.is_active = not ad.is_active
        ad.save()
    return redirect("ad_list")


@staff_member_required
def ad_delete(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if request.method == "POST":
        ad.delete()
        messages.success(request, "Ad deleted.")
    return redirect("ad_list")
