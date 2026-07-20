from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from .decorators import role_required
from .models import *
from .forms import ProfileForm, UserPreferenceForm, EditProfileForm, RegisterForm, RoomForm




# Create your views here.

# HOME
def home(request):
    rooms = Room.objects.filter(status='active').prefetch_related('images')
    ads = list(Advertisement.objects.filter(is_active=True))

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

    # FURNISHED STATUS (radio - single value)
    if furnished_status:
        rooms = rooms.filter(furnished_status=furnished_status)

    # PARKING (checkboxes - car / bike, independent, OR logic if both checked)
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
        rooms = rooms.filter(Q(has_water_24_7=True) | Q(has_drinking_water=True))
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
        rooms = rooms.order_by('-created_at')  # default = latest

    # BUILD INTERLEAVED LIST (rooms + ads) — used by the template
    rooms = list(rooms)
    interleaved = []
    ad_index = 0

    ad_inserted = False

    for i, room in enumerate(rooms):
        interleaved.append(("room", room))
        # drop in an ad after every 2 rooms (i.e. after every full row, since the
        # grid is 2 columns) — .listing-ad spans the full width (grid-column: 1/-1)
        if ads and (i + 1) % 3 == 0:
            interleaved.append(("ad", ads[ad_index % len(ads)]))
            ad_index += 1
            # add a "More listings" section divider right after the first ad only,
            # matching the design mock
            if not ad_inserted:
                interleaved.append(("heading", "More listings"))
                ad_inserted = True

    context = {
        "interleaved": interleaved,
        "rooms": rooms,
        "ads": ads,

        "provinces": Province.objects.all(),
        "districts": District.objects.all(),

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
        
        if not user_obj.is_active and user_obj.check_password(password):
            messages.error(request, 'Please verify your email before logging in.')
            request.session['otp_user_id'] = user_obj.id
            return redirect('verify_otp')

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
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP

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

            # check duplicate email — but allow retry if the old one was never verified
            existing = User.objects.filter(email=email).first()
            if existing:
                if existing.profile.is_verified:
                    messages.error(request, 'Email already exists.')
                    return render(request, 'register.html', {'form': form})
                existing.delete()

            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password']
            )
            user.is_active = False
            user.save()

            user.profile.phone = form.cleaned_data['phone_number']
            user.profile.role = form.cleaned_data['role']
            user.profile.is_verified = False
            user.profile.save()

            send_otp_email(user)
            request.session['otp_user_id'] = user.id

            messages.success(request, 'We sent a 6-digit OTP to your email.')
            return redirect('verify_otp')

        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, 'register.html', {'form': form})

    form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def send_otp_email(user):
    otp_obj = EmailOTP.objects.create(user=user, otp=EmailOTP.generate_otp())
    send_mail(
        subject="Room Finder - Email Verification OTP",
        message=(f"Hi {user.first_name},\n\nYour OTP is: {otp_obj.otp}\n"
                 f"It expires in 5 minutes.\n\nIf you didn't request this, ignore this email."),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp_obj


def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please register or login again.")
        return redirect('register')

    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "User not found. Please register again.")
        return redirect('register')

    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        otp_obj = EmailOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, "No OTP found. Please request a new one.")
        elif otp_obj.is_expired():
            messages.error(request, "OTP expired. Please request a new one.")
        elif otp_obj.otp != entered:
            messages.error(request, "Invalid OTP. Please try again.")
        else:
            otp_obj.is_used = True
            otp_obj.save()
            user.is_active = True
            user.save()
            user.profile.is_verified = True
            user.profile.save()
            del request.session['otp_user_id']
            messages.success(request, "Email verified successfully! You can now log in.")
            return redirect('login')

        return redirect('verify_otp')

    return render(request, 'verify_otp.html', {'email': user.email})


def resend_otp_view(request):
    user_id = request.session.get('otp_user_id')
    user = User.objects.filter(id=user_id).first() if user_id else None
    if not user:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)
    send_otp_email(user)
    messages.success(request, "A new OTP has been sent to your email.")
    return redirect('verify_otp')


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
    active_count = user_listings.filter(status='active').count()
    pending_count = user_listings.filter(status='pending').count()
    total_views = user_listings.aggregate(total=Sum('views'))['total'] or 0
    recent_listings = user_listings[:5]
    has_verified_property = user_listings.filter(is_verified=True).exists()

    return render(request, "landlord_dashboard.html", {
        "listing_count": listing_count,
        "active_count": active_count,
        "pending_count": pending_count,
        "total_views": total_views,
        "recent_listings": recent_listings,
        "has_verified_property": has_verified_property,
    })


# My profile
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
    listings = Room.objects.filter(owner=request.user)

    status = request.GET.get('status')
    if status:
        listings = listings.filter(status=status)

    context = {
        'listings': listings,
        'listing_count': Room.objects.filter(owner=request.user).count(),
        'active_count': Room.objects.filter(owner=request.user, status='active').count(),
        'pending_count': Room.objects.filter(owner=request.user, status='pending').count(),
        'rejected_count': Room.objects.filter(owner=request.user, status='rejected').count(),
    }
    return render(request, 'my_listings.html', context)


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

            for index, img in enumerate(request.FILES.getlist("images")):
                RoomImage.objects.create(room=room, image=img, order=index)

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
def landlord_chatroom(request, user_id, room_id):

    other_user = get_object_or_404(User, id=user_id)
    room = get_object_or_404(Room, id=room_id)

    if request.method == "POST":
        body = request.POST.get("body")

        if body:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                room=room,
                body=body
            )

        return redirect("landlord_chatroom", user_id=user_id, room_id=room_id)

    chat_messages = Message.objects.filter(
        room=room
    ).filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("sent_at")

    chat_messages.filter(
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related(
        "sender", "receiver", "room"
    ).order_by("-sent_at")

    conversations = []
    seen = set()

    for msg in all_messages:
        other = msg.receiver if msg.sender == request.user else msg.sender
        key = (other.id, msg.room.id if msg.room else None)

        if key not in seen:
            seen.add(key)
            conversations.append({
                "user": other,
                "room": msg.room,
                "last_message": msg,
            })

    return render(request, "landlord_chatroom.html", {
        "conversations": conversations,
        "chat_messages": chat_messages,
        "room": room,
        "other_user": other_user,
    })

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)

    room_id = message.room.id
    other_user_id = (
        message.receiver.id
        if message.sender == request.user
        else message.sender.id
    )

    if request.method == "POST":
        message.delete()

    return redirect("landlord_chatroom", user_id=other_user_id, room_id=room_id)


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

    rooms = list(Room.objects.filter(
        status='active').order_by('-created_at')[:12])
    ads = list(Advertisement.objects.filter(is_active=True))
    interleaved = []
    ad_index = 0

    for i, room in enumerate(rooms):
        interleaved.append(("room", room))

        if (i + 1) % 3 == 0 and ads:
            interleaved.append(("ad", ads[ad_index % len(ads)]))
            ad_index += 1

    return render(request, 'tenant_dashboard.html', {
        'saved_rooms': saved_rooms,
        'saved_count': saved_count,
        'browse_rooms': rooms,
        'interleaved': interleaved,
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
    ads = list(Advertisement.objects.filter(is_active=True))
    rooms = Room.objects.filter(status="active").exclude(owner=request.user)

    query = request.GET.get("q", "")
    room_type = request.GET.get('room_type', '')
    province_id = request.GET.get('province', '')
    district_id = request.GET.get('district', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    wifi = request.GET.get('wifi', '')
    furnished = request.GET.get('furnished', '')
    parking = request.GET.get('parking', '')
    attached_bathroom = request.GET.get('attached_bathroom', '')

    if query:
        rooms = rooms.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(description__icontains=query) |
            Q(district__name__icontains=query) |
            Q(province__name__icontains=query)
        )

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
        rooms = rooms.filter(furnished_status='furnished')
    if parking:
        rooms = rooms.filter(parking=True)
    if attached_bathroom:
        rooms = rooms.filter(attached_bathroom=True)

    rooms = list(rooms)

    interleaved = []
    ad_index = 0
    for i, room in enumerate(rooms):
        interleaved.append(("room", room))
        if (i + 1) % 3 == 0 and ads:
            interleaved.append(("ad", ads[ad_index % len(ads)]))
            ad_index += 1

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
        'attached_bathroom': attached_bathroom,
        'interleaved': interleaved
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
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        key = other_user.id

        if key not in seen:
            seen.add(key)
            unread = Message.objects.filter(
                sender=other_user,
                receiver=request.user,
                is_read=False
            ).count()
            conversations.append({
                'user': other_user,
                'room': msg.room,
                'last_message': msg,
                'unread': unread
            })

    return render(request, 'tenant_messages.html', {
        'conversations': conversations
    })


@login_required
def start_conversation(request):

    query = request.GET.get("q", "").strip()
    rooms = Room.objects.none()

    if query:
        rooms = Room.objects.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(owner__first_name__icontains=query) |
            Q(owner__last_name__icontains=query)
        ).filter(
            status='active'
        ).exclude(
            owner=request.user
        ).select_related(
            "owner", "province", "district"
        ).distinct()

    return render(request, "start_convo.html", {
        'rooms': rooms,
        'query': query,
    })


@login_required
def chat_room(request, user_id, room_id):

    other_user = get_object_or_404(User, id=user_id)
    room = get_object_or_404(Room, id=room_id)

    messages = Message.objects.filter(
        room=room
    ).filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("sent_at")

    Message.objects.filter(
        room=room,
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    if request.method == "POST":
        body = request.POST.get("message", "").strip()

        if body:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                room=room,
                body=body,
            )

        return redirect("chat_room", user_id=user_id, room_id=room_id)

    return render(request, "chat_room.html", {
        "room": room,
        "other_user": other_user,
        "messages": messages,
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


def troom_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id, status='active')
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
