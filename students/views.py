# students/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from institution.models import Department, Programme
from accounts.models import User
from .models import StudentProfile
from .forms import StudentCreationForm

def is_management(user):
    return hasattr(user, 'is_management') and user.is_management

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Access Denied.")
        return redirect('login')

    profile = request.user.student_profile
    context = {'profile': profile}
    return render(request, 'students/dashboard.html', context)

@login_required
def student_list(request):
    if not is_management(request.user):
        messages.error(request, "Access Denied.")
        return redirect('login')
        
    students_qs = StudentProfile.objects.select_related('user', 'department', 'programme').all()
    
    query = request.GET.get('q')
    if query:
        students_qs = students_qs.filter(
            Q(matric_number__icontains=query) | 
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query)
        )
        
    return render(request, 'students/student_list.html', {'students': students_qs})

@login_required
def student_create(request):
    if not is_management(request.user):
        return redirect('login')
        
    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            try:
                # 1. Create the Student Profile instance but don't save yet
                profile = form.save(commit=False)
                
                # 2. Generate Matric Number manually here to use as Username
                # We call the model method directly
                temp_profile_for_gen = StudentProfile()
                matric_num = temp_profile_for_gen.generate_matric_number()
                profile.matric_number = matric_num
                
                # 3. Create the User account
                # Username IS the matric number
                user = User.objects.create_user(
                    username=matric_num, 
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    is_staff=False,
                    is_management=False
                )
                
                # 4. Link User to Profile and Save
                profile.user = user
                profile.save()
                
                messages.success(request, f"Student {profile.user.get_full_name()} registered successfully. Matric No: {profile.matric_number}")
                return redirect('students:list')
                
            except Exception as e:
                messages.error(request, f"Error registering student: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentCreationForm()

    return render(request, 'students/student_form.html', {'form': form})

@login_required
def student_edit(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    profile = get_object_or_404(StudentProfile, pk=pk)
    user = profile.user
    
    if request.method == 'POST':
        # Update User Details
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        
        # Update Profile Details
        profile.level = int(request.POST.get('level', profile.level))
        profile.qualification_type = request.POST.get('qualification_type', profile.qualification_type)
        
        dept_id = request.POST.get('department')
        if dept_id:
            try:
                profile.department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                pass
                
        prog_id = request.POST.get('programme')
        if prog_id:
            try:
                profile.programme = Programme.objects.get(id=prog_id)
            except Programme.DoesNotExist:
                pass
                
        user.save()
        profile.save()
        
        messages.success(request, f"Student details updated for {user.get_full_name()}.")
        return redirect('students:list')
        
    departments = Department.objects.all()
    programmes = Programme.objects.all()
    return render(request, 'students/student_form.html', {
        'profile': profile,
        'user': user,
        'departments': departments,
        'programmes': programmes,
        'editing': True
    })

@login_required
def student_delete(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    profile = get_object_or_404(StudentProfile, pk=pk)
    
    if request.method == 'POST':
        user = profile.user
        profile.delete()
        user.delete() 
        
        messages.success(request, "Student account deleted.")
        return redirect('students:list')
        
    return render(request, 'management/confirm_delete.html', {
        'object': profile, 
        'type': 'Student',
        'cancel_url_name': 'students:list'
    })

@login_required
def student_detail(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    profile = get_object_or_404(StudentProfile, pk=pk)
    return render(request, 'students/student_detail.html', {'profile': profile})