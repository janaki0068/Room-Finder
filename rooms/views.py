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
    room_types = request.GET.getlist('room_type')       # multi-select
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    furnished_status = request.GET.get('furnished_status')
    parking_car = request.GET.get('parking_car')
    parking_bike = request.GET.get('parking_bike')
    attached_bathroom = request.GET.get('attached_bathroom')
    wifi = request.GET.get('wifi')
    water_247 = request.GET.get('water_247')
    drinking_water = request.GET.get('drinking_water')
    kitchen = request.GET.get('kitchen')
    pet_allowed = request.GET.get('pet_allowed')

    # TEXT SEARCH (city / area / address / district / province / title / description)
    if query:
        rooms = rooms.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(description__icontains=query) |
            Q(area__icontains=query) |
            Q(address__icontains=query) |
            Q(district__name__icontains=query) |
            Q(province__name__icontains=query)
        ).distinct()

    # PROVINCE
    if province_id:
        rooms = rooms.filter(province__id=province_id)

    # DISTRICT
    if district_id:
        rooms = rooms.filter(district__id=district_id)

    # PROPERTY TYPE (multi-select)
    if room_types:
        rooms = rooms.filter(room_type__in=room_types)

    # PRICE RANGE
    if min_price:
        rooms = rooms.filter(price__gte=min_price)
    if max_price:
        rooms = rooms.filter(price__lte=max_price)

    # FURNISHED STATUS 
    if furnished_status:
        rooms = rooms.filter(furnished_status=furnished_status)

    # PARKING 
    if parking_car and parking_bike:
        rooms = rooms.filter(Q(parking=True) | Q(has_bike_parking=True))
    elif parking_car:
        rooms = rooms.filter(parking=True)
    elif parking_bike:
        rooms = rooms.filter(has_bike_parking=True)

    # ATTACHED BATHROOM
    if attached_bathroom:
        rooms = rooms.filter(attached_bathroom=True)

    # WIFI
    if wifi:
        rooms = rooms.filter(wifi=True)

    # WATER FACILITY (checkboxes - 24/7 / drinking, independent, OR logic if both checked)
    if water_247 and drinking_water:
        rooms = rooms.filter(Q(has_water_24_7=True) |
                             Q(has_drinking_water=True))
    elif water_247:
        rooms = rooms.filter(has_water_24_7=True)
    elif drinking_water:
        rooms = rooms.filter(has_drinking_water=True)

    # KITCHEN
    if kitchen:
        rooms = rooms.filter(has_kitchen=True)

    # PET ALLOWED
    if pet_allowed:
        rooms = rooms.filter(pet_allowed=True)

    # SORT
    if sort == 'low-high':
        rooms = rooms.order_by('price')
    elif sort == 'high-low':
        rooms = rooms.order_by('-price')
    else:
        rooms = rooms.order_by('-created_at')

    context = {
        "rooms": rooms,
        "provinces": Province.objects.all(),
        "room_type_choices": Room.ROOM_TYPES,
        "furnished_choices": Room.FURNISHED_CHOICES,
        "selected_province": province_id,
        "selected_district": district_id,
        "query": query,
        "selected_sort": sort,
        "selected_types": room_types,
        "min_price": min_price,
        "max_price": max_price,
        "selected_furnished": furnished_status,
        "parking_car": parking_car,
        "parking_bike": parking_bike,
        "attached_bathroom": attached_bathroom,
        "wifi": wifi,
        "water_247": water_247,
        "drinking_water": drinking_water,
        "kitchen": kitchen,
        "pet_allowed": pet_allowed,
    }
    return render(request, "index.html", context)


# LOGIN
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        elif request.user.profile.role == 'landlord':
            return redirect('landlord_dashboard')
        else:
            return redirect('tenant_dashboard')

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
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        elif request.user.profile.role == 'landlord':
            return redirect('landlord_dashboard')
        else:
            return redirect('tenant_dashboard')

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

    return render(request, 'tsearch_rooms.html', {
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

# My profile
from .forms import ProfileForm

@login_required
def landlord_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('landlord_profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'landlord_profile.html', {'form': form})


# My listings page
@login_required
def my_listings(request):
    listings = Room.objects.filter(owner=request.user).order_by("-created_at")

    return render(request, "my_listings.html", {
        "listings": listings
    })


# Room detail
@login_required
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
            request.POST, request.FILES, instance=profile, user=request.user)
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

            return redirect("settings.html")

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
    return redirect('saved_view')


@login_required(login_url='login')
def tsearch_rooms(request):
    rooms = Room.objects.filter(status='approved')

    query = request.GET.get('q', '')
    if query:
        rooms = rooms.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(description__icontains=query) |
            Q(district__name__icontains=query) |
            Q(province__name__icontains=query)
        )

    room_type = request.GET.get('room_type', '')
    province_id = request.GET.get('province', '')
    district_id = request.GET.get('district', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    wifi = request.GET.get('wifi', '')
    furnished = request.GET.get('furnished', '')
    parking = request.GET.get('parking', '')
    attached_bathroom = request.GET.get('attached_bathroom', '')

    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if province_id:
        rooms = rooms.filter(province_id=province_id)
    if district_id:
        rooms = rooms.filter(district_id=district_id)
    if min_price:
        rooms = rooms.filter(price__gte=min_price)
    if max_price:
        rooms = rooms.filter(price__lte=max_price)
    if wifi:
        rooms = rooms.filter(wifi=True)
    if furnished:
        rooms = rooms.filter(furnished=True)
    if parking:
        rooms = rooms.filter(parking=True)
    if attached_bathroom:
        rooms = rooms.filter(attached_bathroom=True)

    provinces = Province.objects.all()
    districts = District.objects.filter(
        province_id=province_id) if province_id else District.objects.all()

    return render(request, 'tsearch_rooms.html', {
        'rooms': rooms,
        'query': query,
        'provinces': provinces,
        'districts': districts,
        'room_type': room_type,
        'province_id': province_id,
        'district_id': district_id,
        'min_price': min_price,
        'max_price': max_price,
        'wifi': wifi,
        'furnished': furnished,
        'parking': parking,
        'attached_bathroom': attached_bathroom
    })


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
def tenant_settings(request):
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(
                    request, 'Your password was successfully updated!')
                return redirect('tenant_settings')
            else:
                messages.error(
                    request, 'Please try again. The password was not updated.')

        elif action == 'delete_account':
            request.user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('home')
    return render(request, 'tenant_settings.html', {'password_form': password_form})


@login_required
def tenant_messages(request):
    received = Message.objects.filter(
        receiver=request.user
    ).order_by('-sent_at')

    sent = Message.objects.filter(
        sender=request.user
    ).order_by('-sent_at')

    return render(request, 'tenant_messages.html', {
        'received': received,
        'sent': sent,
    })


@login_required
def notifications(request):
    unread_count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return render(request, 'notifications.html', {
        'unread_count': unread_count,
    })


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id, status='approved')
    images = room.images.all()

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedRoom.objects.filter(
            user=request.user, room=room).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        if is_saved:
            SavedRoom.objects.filter(user=request.user, room=room).delete()
            is_saved = False
        else:
            SavedRoom.objects.create(user=request.user, room=room)
            is_saved = True

    room.increment_views()

    return render(request, 'troom_details.html', {
        'room': room,
        'images': images,
        'is_saved': is_saved
    })
