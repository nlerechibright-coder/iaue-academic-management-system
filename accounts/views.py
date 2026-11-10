# accounts/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render


def user_login(request):
    """Authenticate a user and redirect based on role/profile."""
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                messages.error(request, 'This account is disabled.')
                return render(request, 'accounts/login.html', {'form': form})

            auth_login(request, user)

            # 1. Check for Management Role first
            if getattr(user, 'is_management', False):
                return redirect('dashboard')
            
            # 2. Check for Student Profile
            if hasattr(user, 'student_profile'):
                return redirect('students:dashboard')
            
            # 3. Check for Staff Profile
            if hasattr(user, 'staff_profile'):
                return redirect('staff:dashboard')
            
            # 4. Fallback for Superusers/Staff flag holders who aren't linked to profiles yet
            # (e.g., pure admins)
            if user.is_superuser or user.is_staff:
                return redirect('/admin/')
                
            # Default fallback
            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('login')

    return redirect('login')