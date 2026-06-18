from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm
from .models import *
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


# Create your views here.

# HOME
def home(request):
    rooms = Room.objects.all()

    # GET FILTER VALUES
    query = request.GET.get('q')
    province_id = request.GET.get('province')
    district_id = request.GET.get('district')

    # SEARCH FILTER
    if query:
        rooms = rooms.filter(
            title__icontains=query
        ) | rooms.filter(
            city__icontains=query
        ) | rooms.filter(
            description__icontains=query
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
            return redirect('home')
        
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')
    return render(request, 'login.html')

# REGISTER
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():

            if User.objects.filter(email=form.cleaned_data['email']).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'register.html', {'form': form})
            
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password']
            )

            Profile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                role=form.cleaned_data['role']
            )

            messages.success(request, 'User registered successfully.')
            return redirect('login')
    else:
        form = RegisterForm()
                   
    return render(request, 'register.html',{'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


# SEARCH_ROOMS
def search_rooms(request):
    query = request.GET.get('q','')
    rooms = Room.objects.all()

    if query:
        rooms = Room.objects.filter(
            Q(city__icontains=query)|
            Q(district__name__icontains=query)|
            Q(province__name__icontains=query)|
            Q(title__icontains=query)
        )

    return render(request, 'home.html', {
        'rooms':rooms,
        'query':query,
    })


def get_districts(request, province_id):
    districts = District.objects.filter(province_id=province_id).values(
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
    return render(request, 'profile.html')
