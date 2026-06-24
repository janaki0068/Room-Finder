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

# Create your views here.

# HOME


def home(request):
    rooms = Room.objects.filter(status='active')

    # GET FILTER VALUES
    query = request.GET.get('q')
    province_id = request.GET.get('province')
    district_id = request.GET.get('district')

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

    provinces = Province.objects.all()
    districts = District.objects.all()

    return render(request, "index.html", {
        "rooms": rooms,
        "provinces": provinces,
        "districts": districts,
        "selected_province": province_id,
        "selected_district": district_id,
        "query": query,
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
                return redirect('home')
        
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')

    return render(request, 'login.html')


# REGISTER
def register_view(request, role):
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

    return render(request, 'home.html', {
        'rooms': rooms,
        'query': query,
    })


def get_districts(request, province_id):
    districts = District.objects.filter(
        province_id=province_id
    ).values(
        'id',
        'name'
    )

    return JsonResponse({
        'districts': list(districts)
    })


@login_required(login_url='login')
def saved_view(request):
    return render(request, 'saved.html')


@login_required(login_url='login')
def list_view(request):
    return render(request, 'list.html')


@login_required(login_url='login')
def profile_view(request):
    profile = request.user.profile

    return render(request, 'profile.html', {
        'profile': profile
    })


# LANDLORD DASHBOARD
@login_required
def landlord_dashboard(request):
    user_listings = Room.objects.filter(owner=request.user)
    total_listings = user_listings.count()
    active_listings = user_listings.filter(status='active').count()
    total_views = user_listings.aggregate(
        total=Sum('views')
    )['total'] or 0

    saved_count = SavedRoom.objects.filter(
        room__owner=request.user
    ).count()

    recent_listings = user_listings[:5]

    return render(request, 'landlord_dashboard.html', {
        'total_listings': total_listings,
        'active_listings': active_listings,
        'total_views': total_views,
        'saved_count': saved_count,
        'recent_listings': recent_listings,
    })


# My listings page


@login_required
def my_listings(request):
    listings = Room.objects.filter(owner=request.user)

    return render(request, "my_listings.html", {
        "listings": listings
    })

# My saved rooms


@login_required
def saved_rooms(request):
    saved = SavedRoom.objects.filter(
        user=request.user
    ).select_related('room')

    return render(request, "saved_rooms.html", {
        "saved_rooms": saved
    })

# My edit profile


@login_required
def edit_profile(request):
    return render(request, "edit_profile.html")


# My upload listing


@login_required
def upload_listing(request):

    if request.method == "POST":

        form = RoomForm(request.POST, request.FILES)

        if form.is_valid():

            room = form.save(commit=False)
            room.owner = request.user
            room.status = "draft"
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
    messages_list = Message.objects.filter(
        receiver=request.user
    )

    return render(request, "messages.html", {
        "messages": messages_list
    })

# My settings


@login_required
def settings_view(request):
    return render(request, "settings.html")

# TENANT DASHBOARD


@role_required('tenant')
def tenant_dashboard(request):
    saved_rooms = SavedRoom.objects.filter(
        user=request.user).select_related('room')
    saved_count = saved_rooms.count()

    browse_rooms = Room.objects.filter(
        status='active').order_by('-created_at')[:12]

    return render(request, 'tenant_dashboard.html', {
        'saved_rooms': saved_rooms,
        'saved_count': saved_count,
        'browse_rooms': browse_rooms,
    })
