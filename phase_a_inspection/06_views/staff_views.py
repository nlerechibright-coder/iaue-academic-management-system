from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import User
from .models import StaffProfile
from .forms import StaffCreationForm

def management_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.is_management)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper

@management_required
def staff_create(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            
            StaffProfile.objects.create(
                user=user,
                staff_id=form.cleaned_data['staff_id'],
                department=form.cleaned_data['department']
            )
            
            messages.success(request, f"Staff account created successfully! Username: {user.username}")
            return redirect('staff:staff_list')
    else:
        form = StaffCreationForm()
    
    return render(request, 'staff/staff_create.html', {'form': form})

@management_required
def staff_list(request):
    staff = StaffProfile.objects.select_related('user', 'department').all()
    return render(request, 'staff/staff_list.html', {'staff': staff})
