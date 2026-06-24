# decorators.py — put this in the same folder as views.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.profile.role != required_role:
                messages.error(request, "You don't have access to that page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator