from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import User
from .models import StudentProfile
from .forms import StudentClearanceForm

def management_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.is_management)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper

@management_required
def student_clearance(request):
    if request.method == 'POST':
        form = StudentClearanceForm(request.POST)
        if form.is_valid():
            # Generate matric number
            admission_year = form.cleaned_data['admission_session'].split('/')[0]
            matric_number = StudentProfile.generate_matric_number(admission_year)
            
            # Create user account
            username = matric_number.replace('/', '_').lower()
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            
            # Create student profile
            StudentProfile.objects.create(
                user=user,
                matric_number=matric_number,
                department=form.cleaned_data['department'],
                programme=form.cleaned_data['programme'],
                current_level=form.cleaned_data['current_level'],
                admission_session=form.cleaned_data['admission_session'],
                phone=form.cleaned_data['phone']
            )
            
            messages.success(request, f"Student cleared successfully! Matric Number: {matric_number}, Username: {username}")
            return redirect('students:student_list')
    else:
        form = StudentClearanceForm()
    
    return render(request, 'students/student_clearance.html', {'form': form})

@management_required
def student_list(request):
    students = StudentProfile.objects.select_related('user', 'department', 'programme').all()
    return render(request, 'students/student_list.html', {'students': students})
