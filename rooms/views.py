from .forms import UserPreferenceForm
from django.db.models import Q
from .forms import EditProfileForm
from django.shortcuts import render, get_object_or_404
from .models import Province, Room
from .forms import RoomForm
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm, RoomForm
from .models import *
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

# Create your views here.

# HOME
def home(request):
    rooms = Room.objects.filter(status='active')

    # GET FILTER VALUES
    query = request.GET.get('q')
    province_id = request.GET.get('province')
    district_id = request.GET.get('district')
    sort = request.GET.get('sort')
    room_type = request.GET.get('room_type')

    # SEARCH FILTER
    if query:
        rooms = rooms.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(description__icontains=query)
        )

    # PROVINCE FILTER
    if province_id and province_id != "all":
        rooms = rooms.filter(province__id=province_id)

    # DISTRICT FILTER
    if district_id:
        rooms = rooms.filter(district__id=district_id)

    if room_type:
        rooms = rooms.filter(room_type=room_type)

    # SORT FILTER
    if sort == 'low-high':
        rooms = rooms.order_by('price')
    elif sort == 'high-low':
        rooms = rooms.order_by('-price')
    else:
        rooms = rooms.order_by('-created_at')  # default = latest

    provinces = Province.objects.all()
    districts = District.objects.all()

    return render(request, "index.html", {
        "rooms": rooms,
        "provinces": provinces,
        "districts": districts,
        "selected_province": province_id,
        "selected_district": district_id,
        "query": query,
        "selected_sort": sort,
        "selected_type": room_type,
    })


# LOGIN
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_staff:
                return redirect('admin_dashboard')
            elif user.profile.role == 'landlord':
                return redirect('landlord_dashboard')
            else:
                return redirect('tenant_dashboard')

        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')

    return render(request, 'login.html')


# REGISTER
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            # check duplicate email
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'register.html', {'form': form})

            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password']
            )

            user.profile.phone = form.cleaned_data['phone_number']
            user.profile.role = form.cleaned_data['role']
            user.profile.save()

            messages.success(request, 'User registered successfully.')
            return redirect('login')

        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, 'register.html', {'form': form, 'role': role})

    form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


# SEARCH_ROOMS
def search_rooms(request):
    query = request.GET.get('q', '')
    rooms = Room.objects.all()

    if query:
        rooms = Room.objects.filter(
            Q(city__icontains=query) |
            Q(district__name__icontains=query) |
            Q(province__name__icontains=query) |
            Q(title__icontains=query)
        )

    return render(request, 'search_rooms.html', {
        'rooms': rooms,
        'query': query,
    })


def get_districts(request, province_id):
    districts = District.objects.filter(province_id=province_id).values(
        'id',
        'name'
    )

    return JsonResponse({
        'districts': list(districts)
    })

# LANDLORD DASHBOARD


@login_required
def landlord_dashboard(request):

    user_listings = Room.objects.filter(owner=request.user)
    listing_count = user_listings.count()
    approved_count = user_listings.filter(status='approved').count()
    pending_count = user_listings.filter(status='pending').count()
    total_views = user_listings.aggregate(total=Sum('views'))['total'] or 0
    recent_listings = user_listings[:5]
    has_verified_property = user_listings.filter(is_verified=True).exists()

    return render(request, "landlord_dashboard.html", {
        "listing_count": listing_count,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "total_views": total_views,
        "recent_listings": recent_listings,
        "has_verified_property": has_verified_property,
    })


# My listings page
@login_required
def my_listings(request):
    listings = Room.objects.filter(owner=request.user).order_by("-created_at")

    return render(request, "my_listings.html", {
        "listings": listings
    })


# Room detail


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id, owner=request.user)

    return render(request, 'room_detail.html', {
        'room': room
    })

# Edit listings


@login_required
def edit_listing(request, room_id):

    room = get_object_or_404(
        Room,
        id=room_id,
        owner=request.user
    )

    if request.method == "POST":
        form = RoomForm(request.POST, request.FILES, instance=room)

        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully.")
            return redirect("edit_listing", room_id=room.id)
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = RoomForm(instance=room)

    return render(request, "edit_listing.html", {
        "form": form,
        "room": room
    })

# Delete listings


@login_required
def delete_listing(request, room_id):

    room = get_object_or_404(
        Room,
        id=room_id,
        owner=request.user
    )

    if request.method == "POST":
        room.delete()

    return redirect("my_listings")

# My saved rooms


@login_required
def saved_rooms(request):
    rooms = (
        Room.objects.filter(
            owner=request.user,
            saved_by__isnull=False
        )
        .prefetch_related("saved_by__user")
        .distinct()
        .order_by("-id")
    )

    return render(request, "saved_rooms.html", {
        "rooms": rooms
    })


# My edit profile


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        form = EditProfileForm(
            request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("settings")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(instance=profile, user=request.user)

    return render(request, "edit_profile.html", {"form": form})


# My upload listing
@login_required
def upload_listing(request):

    if request.method == "POST":

        form = RoomForm(request.POST, request.FILES)

        if form.is_valid():

            room = form.save(commit=False)
            room.owner = request.user
            room.status = "pending"
            room.is_verified = False

            room.save()

            VerificationDocument.objects.create(
                room=room,
                citizenship_front=request.FILES.get("citizenship_front"),
                citizenship_back=request.FILES.get("citizenship_back"),
                lalpurja=request.FILES.get("lalpurja"),
                selfie=request.FILES.get("selfie"),
            )

            messages.success(
                request,
                "Property submitted successfully and is waiting for verification."
            )

            return redirect("my_listings")

    else:
        form = RoomForm()

    return render(
        request,
        "upload_listing.html",
        {
            "form": form,
            "provinces": Province.objects.all(),
        }
    )


# My messages


@login_required
def messages_view(request):

    all_messages = Message.objects.filter(
        Q(sender=request.user) |
        Q(receiver=request.user)
    ).select_related(
        "sender",
        "receiver",
        "room"
    ).order_by("-sent_at")

    conversations = []
    seen = set()

    for msg in all_messages:

        other_user = (
            msg.receiver
            if msg.sender == request.user
            else msg.sender
        )

        key = (
            other_user.id,
            msg.room.id if msg.room else None
        )

        if key not in seen:

            seen.add(key)

            conversations.append({

                "user": other_user,
                "room": msg.room,
                "last_message": msg

            })

    return render(request, "messages.html", {

        "conversations": conversations

    })

# Chatbox


@login_required
def chat_room(request, user_id, room_id):

    other_user = get_object_or_404(User, id=user_id)
    room = get_object_or_404(Room, id=room_id)

    # Handle sending a new message
    if request.method == "POST":
        body = request.POST.get("body")

        if body:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                room=room,
                body=body
            )

        return redirect("chat_room", user_id=user_id, room_id=room_id)

    # Get current conversation
    messages = Message.objects.filter(
        room=room
    ).filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("sent_at")

    # Mark received messages as read
    messages.filter(
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    # conversation lists
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related(
        "sender",
        "receiver",
        "room"
    ).order_by("-sent_at")

    conversations = []
    seen = set()

    for msg in all_messages:

        other = msg.receiver if msg.sender == request.user else msg.sender

        key = (
            other.id,
            msg.room.id if msg.room else None
        )

        if key not in seen:
            seen.add(key)

            conversations.append({
                "user": other,
                "room": msg.room,
                "last_message": msg,
            })

    return render(request, "messages.html", {
        "conversations": conversations,
        "messages": messages,
        "room": room,
        "other_user": other_user,
    })

# My settings


@login_required
def settings_view(request):

    preferences, created = UserPreference.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = UserPreferenceForm(
            request.POST,
            instance=preferences
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Settings updated successfully."
            )

            return redirect("settings")

    else:

        form = UserPreferenceForm(
            instance=preferences
        )

    return render(
        request,
        "settings.html",
        {
            "form": form,
            "preferences": preferences,
        }
    )


# TENANT DASHBOARD


@role_required('tenant')
def tenant_dashboard(request):
    saved_rooms = SavedRoom.objects.filter(
        user=request.user).select_related('room')
    saved_count = saved_rooms.count()

    browse_rooms = Room.objects.filter(
        status='approved').order_by('-created_at')[:12]

    return render(request, 'tenant_dashboard.html', {
        'saved_rooms': saved_rooms,
        'saved_count': saved_count,
        'browse_rooms': browse_rooms,
    })


@login_required(login_url='login')
def saved_view(request):
    saved = SavedRoom.objects.filter(user=request.user).select_related('room')
    return render(request, 'tsaved_rooms.html', {
        'saved_rooms': saved})


@login_required
def unsave_room(request, room_id):
    SavedRoom.objects.filter(user=request.user, room_id=room_id).delete()
    return redirect('saved')


@login_required(login_url='login')
def tsearch_rooms(request):
    rooms = Room.objects.filter(status='approved')
    return render(request, 'tsearch_rooms.html', {'rooms': rooms})


@login_required(login_url='login')
def profile_view(request):
    profile = request.user.profile

    return render(request, 'tenant_profile.html', {
        'profile': profile
    })


@login_required
def tenant_edit_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()

        profile.phone = request.POST.get('phone', '')
        if request.FILES.get('image'):
            profile.image = request.FILES.get('image')
        profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile_view')

    return render(request, 'tenant_edit_profile.html', {
        'profile': profile
    })


@login_required
def notifications(request):
    return render(request, 'notifications.html')


@login_required
def settings_view(request):
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  
                messages.success(request, 'Your password was successfully updated!')
                return redirect('settings_view')
            else:
                messages.error(request, 'Please try again. The password was not updated.')

        elif action == 'delete_account':
            request.user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('home')
    return render(request, 'tenant_settings.html', {'password_form': password_form})

