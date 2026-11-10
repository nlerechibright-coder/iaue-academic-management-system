from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm

def login_view(request):
    if request.user.is_authenticated:
        return route_user(request.user)
        
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return route_user(user)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def route_user(user):
    """Routes users to their specific dashboards based on their roles."""
    if user.is_management:
        return redirect('institution:dashboard')
    if hasattr(user, 'student_profile'):
        # We will build this in Phase 5, for now redirect to a safe place
        return redirect('accounts:generic_dashboard')
    return redirect('accounts:generic_dashboard')

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def generic_dashboard_view(request):
    """Fallback dashboard for users without specific roles."""
    return render(request, 'accounts/dashboard.html')
