from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RegisterForm
from .models import *
from django.db.models import Q
from django.http import JsonResponse


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
    return render(request, "login.html")

# REGISTER
def register(request):
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

            messages.success(request, 'User registered successfully.')
            return redirect('login')
    else:
        form = RegisterForm()
                   
    return render(request, 'register.html',{'form': form})

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