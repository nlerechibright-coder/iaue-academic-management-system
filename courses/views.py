# courses/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from institution.models import Department
from academics.models import AcademicSession, Semester
from staff.models import StaffProfile
from .models import Course, CourseOffering, LecturerAssignment

def is_management(user):
    return hasattr(user, 'is_management') and user.is_management

@login_required
def course_list(request):
    if not is_management(request.user):
        messages.error(request, "Access Denied.")
        return redirect('login')
        
    courses = Course.objects.select_related('department').all()
    
    query = request.GET.get('q')
    if query:
        courses = courses.filter(
            Q(code__icontains=query) | 
            Q(title__icontains=query)
        )
        
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_create(request):
    if not is_management(request.user):
        return redirect('login')
        
    if request.method == 'POST':
        code = request.POST.get('code').strip()
        title = request.POST.get('title').strip()
        dept_id = request.POST.get('department')
        level = request.POST.get('level')
        semester = request.POST.get('semester')
        credit_units = request.POST.get('credit_units')
        is_compulsory = request.POST.get('is_compulsory') == 'on'
        
        # Basic Validation
        if not all([code, title, dept_id, level, semester]):
            messages.error(request, "All fields except Prerequisites are required.")
            return redirect('courses:course_create')
            
        try:
            dept = Department.objects.get(id=dept_id)
            Course.objects.create(
                code=code,
                title=title,
                department=dept,
                level=int(level),
                semester=semester,
                credit_units=int(credit_units),
                is_compulsory=is_compulsory
            )
            messages.success(request, f"Course {code} created successfully.")
            return redirect('courses:list')
        except Exception as e:
            messages.error(request, f"Error creating course: {str(e)}")
            
    departments = Department.objects.all()
    return render(request, 'courses/course_form.html', {'departments': departments})

@login_required
def course_edit(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.code = request.POST.get('code', course.code).strip()
        course.title = request.POST.get('title', course.title).strip()
        course.level = int(request.POST.get('level', course.level))
        course.semester = request.POST.get('semester', course.semester)
        course.credit_units = int(request.POST.get('credit_units', course.credit_units))
        course.is_compulsory = request.POST.get('is_compulsory') == 'on'
        
        dept_id = request.POST.get('department')
        if dept_id:
            try:
                course.department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                pass
                
        course.save()
        messages.success(request, f"Course {course.code} updated.")
        return redirect('courses:list')
        
    departments = Department.objects.all()
    return render(request, 'courses/course_form.html', {
        'course': course,
        'departments': departments,
        'editing': True
    })

@login_required
def course_delete(request, pk):
    if not is_management(request.user):
        return redirect('login')
        
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted.")
        return redirect('courses:list')
        
    return render(request, 'management/confirm_delete.html', {
        'object': course, 
        'type': 'Course',
        'cancel_url_name': 'courses:list'
    })

# -----------------------------------------------------------------------------
# OFFERING & ASSIGNMENT MANAGEMENT
# -----------------------------------------------------------------------------

@login_required
def offering_list(request):
    """Lists all Course Offerings for the current active session."""
    if not is_management(request.user):
        return redirect('login')
        
    session = AcademicSession.objects.filter(is_active=True).first()
    if not session:
        messages.warning(request, "No active academic session found. Please configure one in Academics.")
        return render(request, 'courses/offering_list.html', {'offerings': [], 'session': None, 'can_generate': False})

    offerings = CourseOffering.objects.filter(session=session).select_related(
        'course', 'course__department'
    ).prefetch_related('assignments__lecturer__user')
    
    # Check if we can generate offerings (if list is empty but courses exist)
    has_courses = Course.objects.exists()
    can_generate = not offerings.exists() and has_courses

    return render(request, 'courses/offering_list.html', {
        'offerings': offerings, 
        'session': session,
        'can_generate': can_generate
    })

@login_required
def generate_offerings(request):
    """Bulk creates CourseOfferings for all existing Courses in the active session."""
    if not is_management(request.user):
        return redirect('login')
        
    if request.method != 'POST':
        return redirect('courses:offering_list')

    session = AcademicSession.objects.filter(is_active=True).first()
    if not session:
        messages.error(request, "No active session found.")
        return redirect('courses:offering_list')

    courses = Course.objects.all()
    created_count = 0
    
    for course in courses:
        # Determine Semester Type based on Course definition
        sem_type = course.semester # 'FIRST' or 'SECOND'
        
        # Create or Get Offering
        _, created = CourseOffering.objects.get_or_create(
            course=course,
            session=session,
            semester_type=sem_type,
            level=course.level
        )
        if created:
            created_count += 1
            
    if created_count > 0:
        messages.success(request, f"Generated {created_count} new course offerings for {session.name}.")
    else:
        messages.info(request, "All courses already have offerings for this session.")
        
    return redirect('courses:offering_list')


@login_required
def manage_assignments(request, pk):
    """Allows admin to assign/unassign lecturers to a specific Course Offering."""
    if not is_management(request.user):
        return redirect('login')
        
    offering = get_object_or_404(CourseOffering.objects.select_related('course'), pk=pk)
    
    # Get currently assigned lecturers
    current_assignments = LecturerAssignment.objects.filter(offering=offering).select_related('lecturer__user')
    assigned_staff_ids = [a.lecturer_id for a in current_assignments]
    
    # Get available staff (exclude already assigned)
    available_staff = StaffProfile.objects.exclude(id__in=assigned_staff_ids).select_related('user', 'department')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'assign':
            staff_id = request.POST.get('staff_id')
            if staff_id:
                try:
                    staff = StaffProfile.objects.get(id=staff_id)
                    # Prevent duplicate
                    if not LecturerAssignment.objects.filter(offering=offering, lecturer=staff).exists():
                        LecturerAssignment.objects.create(offering=offering, lecturer=staff)
                        messages.success(request, f"{staff.user.get_full_name()} assigned to {offering.course.code}.")
                    else:
                        messages.info(request, "Already assigned.")
                except StaffProfile.DoesNotExist:
                    messages.error(request, "Staff member not found.")
                    
        elif action == 'unassign':
            assignment_id = request.POST.get('assignment_id')
            if assignment_id:
                try:
                    assign_obj = LecturerAssignment.objects.get(id=assignment_id, offering=offering)
                    assign_obj.delete()
                    messages.success(request, "Lecturer removed from offering.")
                except LecturerAssignment.DoesNotExist:
                    messages.error(request, "Assignment record not found.")
                    
        return redirect('courses:manage_assignments', pk=pk)

    context = {
        'offering': offering,
        'current_assignments': current_assignments,
        'available_staff': available_staff,
    }
    return render(request, 'courses/manage_assignment.html', context)