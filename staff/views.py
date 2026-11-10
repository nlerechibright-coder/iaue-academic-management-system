# staff/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from institution.models import Department, Faculty
from accounts.models import User
from .models import StaffProfile, Appointment
from .forms import StaffCreationForm
from courses.models import LecturerAssignment, CourseOffering
from results.models import ResultSheet

def is_management(user):
    return hasattr(user, 'is_management') and user.is_management

@login_required
def staff_dashboard(request):
    """Landing page for authenticated staff members."""
    try:
        profile = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        messages.error(request, "No staff profile found for this account.")
        return redirect('login')

    # Get assigned courses (offerings)
    assignments = LecturerAssignment.objects.filter(lecturer=profile).select_related('offering__course', 'offering__session')
    
    # Get pending result sheets for these courses
    course_ids = [a.offering.course.id for a in assignments]
    pending_results = ResultSheet.objects.filter(
        offering__course__in=course_ids,
        status='SUBMITTED' # Adjust status based on your actual workflow
    ).distinct()

    context = {
        'profile': profile,
        'assignments': assignments,
        'pending_results_count': pending_results.count(),
    }
    return render(request, 'staff/staff_dashboard.html', context)

@login_required
def staff_list(request):
    if not is_management(request.user):
        messages.error(request, "Access Denied.")
        return redirect('login')
        
    staff_qs = StaffProfile.objects.select_related('user', 'department').all()
    
    query = request.GET.get('q')
    if query:
        staff_qs = staff_qs.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) | 
            Q(staff_id__icontains=query)
        )
        
    return render(request, 'staff/staff_list.html', {'staff': staff_qs})

@login_required
def staff_create(request):
    if not is_management(request.user):
        return redirect('login')
        
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            try:
                profile = form.save()
                messages.success(request, f"Staff account for {profile.user.get_full_name()} created successfully.")
                return redirect('staff:list')
            except Exception as e:
                messages.error(request, f"Error saving staff: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StaffCreationForm()

    return render(request, 'staff/staff_form.html', {'form': form})

@login_required
def staff_edit(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    profile = get_object_or_404(StaffProfile, pk=pk)
    user = profile.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        
        profile.staff_id = request.POST.get('staff_id', profile.staff_id).strip()
        dept_id = request.POST.get('department')
        if dept_id:
            try:
                profile.department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                pass
                
        user.save()
        profile.save()
        
        messages.success(request, f"Staff details updated for {user.get_full_name()}.")
        return redirect('staff:list')
        
    departments = Department.objects.all()
    return render(request, 'staff/staff_form.html', {
        'profile': profile,
        'user': user,
        'departments': departments,
        'editing': True
    })

@login_required
def staff_delete(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    profile = get_object_or_404(StaffProfile, pk=pk)
    
    if request.method == 'POST':
        user = profile.user
        profile.delete()
        user.delete() 
        
        messages.success(request, "Staff account deleted.")
        return redirect('staff:list')
        
    return render(request, 'management/confirm_delete.html', {
        'object': profile, 
        'type': 'Staff Member',
        'cancel_url_name': 'staff:list'
    })

# --- APPOINTMENT VIEWS ---

@login_required
def appointment_list(request, pk):
    if not is_management(request.user): return redirect('login')
    profile = get_object_or_404(StaffProfile, pk=pk)
    appointments = profile.appointments.all().order_by('-start_date')
    return render(request, 'staff/appointment_list.html', {'profile': profile, 'appointments': appointments})

@login_required
def appointment_create(request, pk):
    if not is_management(request.user): return redirect('login')
    profile = get_object_or_404(StaffProfile, pk=pk)
    
    if request.method == 'POST':
        role = request.POST.get('role')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        faculty_id = request.POST.get('faculty')
        dept_id = request.POST.get('department')
        
        if not role or not start_date or not end_date:
            messages.error(request, "Role, Start Date and End Date are required.")
            return redirect('staff:appointment_create', pk=pk)
            
        try:
            fac = None
            dept = None
            if faculty_id:
                fac = Faculty.objects.get(id=faculty_id)
            if dept_id:
                dept = Department.objects.get(id=dept_id)
                
            Appointment.objects.create(
                staff=profile,
                role=role,
                faculty=fac,
                department=dept,
                start_date=start_date,
                end_date=end_date,
                appointed_by=request.user
            )
            messages.success(request, f"Appointment ({role}) created for {profile.user.get_full_name()}.")
            return redirect('staff:appointment_list', pk=pk)
            
        except Exception as e:
            messages.error(request, f"Error creating appointment: {str(e)}")
            
    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    return render(request, 'staff/appointment_form.html', {
        'profile': profile,
        'faculties': faculties,
        'departments': departments
    })