# institution/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Faculty, Department, Programme
from academics.models import AcademicSession, Semester
from approvals.models import ApprovalAction
from courses.models import Course, CourseOffering
from results.models import ResultSheet
from students.models import StudentProfile
from staff.models import StaffProfile

def is_management(user):
    return hasattr(user, 'is_management') and user.is_management

@login_required
def management_dashboard(request):
    if not is_management(request.user):
        messages.error(request, "Access Denied.")
        return redirect('login')

    active_session = AcademicSession.objects.filter(is_active=True).first()
    active_semester = Semester.objects.filter(is_active=True).first()

    context = {
        'total_faculties': Faculty.objects.count(),
        'total_departments': Department.objects.count(),
        'total_programmes': Programme.objects.count(),
        'total_courses': Course.objects.count(),
        'total_course_offerings': CourseOffering.objects.count(),
        'total_students': StudentProfile.objects.count(),
        'total_staff': StaffProfile.objects.count(),
        'active_session': active_session,
        'active_semester': active_semester,
        'pending_result_approvals': ResultSheet.objects.filter(
            status__in=['SUBMITTED', 'RETURNED', 'APPROVED_HOD', 'APPROVED_DEAN', 'VERIFIED_ER']
        ).count(),
        'recent_activities': ApprovalAction.objects.select_related(
            'actor', 'result_sheet__offering__course'
        )[:6],
    }
    return render(request, 'management/dashboard.html', context)

# ---------------- FACULTY VIEWS ----------------

@login_required
def faculty_list(request):
    if not is_management(request.user): return redirect('login')
    faculties = Faculty.objects.annotate(dept_count=Count('departments')).all()
    return render(request, 'management/faculty_list.html', {'faculties': faculties})

@login_required
def faculty_create(request):
    if not is_management(request.user): return redirect('login')
    
    if request.method == 'POST':
        # Explicitly strip whitespace to avoid empty strings causing issues
        raw_name = request.POST.get('name', '').strip()
        raw_code = request.POST.get('code', '').strip()
        
        # Server-Side Validation
        if not raw_name:
            messages.error(request, "Faculty Name is required.")
            return render(request, 'management/faculty_form.html', {})
            
        if not raw_code:
            messages.error(request, "Faculty Code is required.")
            return render(request, 'management/faculty_form.html', {})

        # Check Uniqueness Before DB Hit
        if Faculty.objects.filter(name__iexact=raw_name).exists():
            messages.error(request, f"A Faculty with this name already exists.")
            return render(request, 'management/faculty_form.html', {})
            
        if Faculty.objects.filter(code__iexact=raw_code).exists():
            messages.error(request, f"A Faculty with this code already exists.")
            return render(request, 'management/faculty_form.html', {})

        try:
            # Create only if valid
            Faculty.objects.create(name=raw_name, code=raw_code.upper())
            messages.success(request, f"Faculty '{raw_name}' created successfully.")
            return redirect('institution:faculty_list')
        except Exception as e:
            # Catch any unexpected DB errors and show them clearly
            messages.error(request, f"Database Error: {str(e)}")
            return render(request, 'management/faculty_form.html', {})

    return render(request, 'management/faculty_form.html')

@login_required
def faculty_edit(request, pk):
    if not is_management(request.user): return redirect('login')
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        raw_name = request.POST.get('name', '').strip()
        raw_code = request.POST.get('code', '').strip()
        
        if not raw_name or not raw_code:
            messages.error(request, "Name and Code are required.")
            return render(request, 'management/faculty_form.html', {'faculty': faculty})

        # Check uniqueness excluding self
        if Faculty.objects.filter(name__iexact=raw_name).exclude(pk=pk).exists():
            messages.error(request, "Another Faculty with this name exists.")
            return render(request, 'management/faculty_form.html', {'faculty': faculty})
            
        if Faculty.objects.filter(code__iexact=raw_code).exclude(pk=pk).exists():
            messages.error(request, "Another Faculty with this code exists.")
            return render(request, 'management/faculty_form.html', {'faculty': faculty})

        faculty.name = raw_name
        faculty.code = raw_code.upper()
        faculty.save()
        messages.success(request, f"Faculty '{raw_name}' updated.")
        return redirect('institution:faculty_list')
        
    return render(request, 'management/faculty_form.html', {'faculty': faculty})

@login_required
def faculty_delete(request, pk):
    if not is_management(request.user): return redirect('login')
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        if faculty.departments.exists():
            messages.error(request, "Cannot delete Faculty. It has associated Departments.")
        else:
            faculty.delete()
            messages.success(request, "Faculty deleted successfully.")
        return redirect('institution:faculty_list')
        
    return render(request, 'management/confirm_delete.html', {
        'object': faculty, 
        'type': 'Faculty',
        'cancel_url_name': 'institution:faculty_list' 
    })

# ---------------- DEPARTMENT VIEWS ----------------

@login_required
def department_list(request):
    if not is_management(request.user): return redirect('login')
    departments = Department.objects.select_related('faculty').annotate(prog_count=Count('programmes')).all()
    return render(request, 'management/department_list.html', {'departments': departments})

@login_required
def department_create(request):
    if not is_management(request.user): return redirect('login')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        fac_id = request.POST.get('faculty')
        
        if not name or not code or not fac_id:
            messages.error(request, "All fields are required.")
            faculties = Faculty.objects.all()
            return render(request, 'management/department_form.html', {'faculties': faculties})

        try:
            fac = Faculty.objects.get(id=fac_id)
            if Department.objects.filter(code__iexact=code, faculty=fac).exists():
                messages.error(request, "Department Code exists in this Faculty.")
            else:
                Department.objects.create(name=name, code=code.upper(), faculty=fac)
                messages.success(request, f"Department '{name}' created.")
                return redirect('institution:department_list')
        except Faculty.DoesNotExist:
            messages.error(request, "Invalid Faculty selected.")
            
    faculties = Faculty.objects.all()
    return render(request, 'management/department_form.html', {'faculties': faculties})

@login_required
def department_edit(request, pk):
    if not is_management(request.user): return redirect('login')
    dept = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        fac_id = request.POST.get('faculty')
        
        if not name or not code or not fac_id:
            messages.error(request, "All fields are required.")
            faculties = Faculty.objects.all()
            return render(request, 'management/department_form.html', {'department': dept, 'faculties': faculties})

        try:
            fac = Faculty.objects.get(id=fac_id)
            if Department.objects.filter(code__iexact=code, faculty=fac).exclude(pk=pk).exists():
                messages.error(request, "Another Department with this Code exists in this Faculty.")
            else:
                dept.name = name
                dept.code = code.upper()
                dept.faculty = fac
                dept.save()
                messages.success(request, f"Department '{name}' updated.")
                return redirect('institution:department_list')
        except Faculty.DoesNotExist:
            messages.error(request, "Invalid Faculty selected.")
            
    faculties = Faculty.objects.all()
    return render(request, 'management/department_form.html', {'department': dept, 'faculties': faculties})

@login_required
def department_delete(request, pk):
    if not is_management(request.user): return redirect('login')
    dept = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        if dept.programmes.exists() or dept.courses.exists():
            messages.error(request, "Cannot delete Department. It has associated Programmes or Courses.")
        else:
            dept.delete()
            messages.success(request, "Department deleted successfully.")
        return redirect('institution:department_list')
        
    return render(request, 'management/confirm_delete.html', {
        'object': dept, 
        'type': 'Department',
        'cancel_url_name': 'institution:department_list'
    })

# ---------------- PROGRAMME VIEWS ----------------

@login_required
def programme_list(request):
    if not is_management(request.user): return redirect('login')
    programmes = Programme.objects.select_related('department__faculty').all()
    return render(request, 'management/programme_list.html', {'programmes': programmes})

@login_required
def programme_create(request):
    if not is_management(request.user): return redirect('login')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        dept_id = request.POST.get('department')
        max_level_str = request.POST.get('max_level')
        
        if not name or not code or not dept_id or not max_level_str:
            messages.error(request, "All fields are required.")
            departments = Department.objects.all()
            return render(request, 'management/programme_form.html', {'departments': departments})

        try:
            max_level = int(max_level_str)
            dept = Department.objects.get(id=dept_id)
            if Programme.objects.filter(code__iexact=code, department=dept).exists():
                messages.error(request, "Programme Code exists in this Department.")
            else:
                Programme.objects.create(name=name, code=code.upper(), department=dept, max_level=max_level)
                messages.success(request, f"Programme '{name}' created.")
                return redirect('institution:programme_list')
        except Department.DoesNotExist:
            messages.error(request, "Invalid Department selected.")
        except ValueError:
            messages.error(request, "Invalid Max Level value.")
            
    departments = Department.objects.all()
    return render(request, 'management/programme_form.html', {'departments': departments})

@login_required
def programme_edit(request, pk):
    if not is_management(request.user): return redirect('login')
    prog = get_object_or_404(Programme, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        dept_id = request.POST.get('department')
        max_level_str = request.POST.get('max_level')
        
        if not name or not code or not dept_id or not max_level_str:
            messages.error(request, "All fields are required.")
            departments = Department.objects.all()
            return render(request, 'management/programme_form.html', {'programme': prog, 'departments': departments})

        try:
            max_level = int(max_level_str)
            dept = Department.objects.get(id=dept_id)
            if Programme.objects.filter(code__iexact=code, department=dept).exclude(pk=pk).exists():
                messages.error(request, "Another Programme with this Code exists in this Department.")
            else:
                prog.name = name
                prog.code = code.upper()
                prog.department = dept
                prog.max_level = max_level
                prog.save()
                messages.success(request, f"Programme '{name}' updated.")
                return redirect('institution:programme_list')
        except Department.DoesNotExist:
            messages.error(request, "Invalid Department selected.")
        except ValueError:
            messages.error(request, "Invalid Max Level value.")
            
    departments = Department.objects.all()
    return render(request, 'management/programme_form.html', {'programme': prog, 'departments': departments})

@login_required
def programme_delete(request, pk):
    if not is_management(request.user): return redirect('login')
    prog = get_object_or_404(Programme, pk=pk)
    
    if request.method == 'POST':
        if prog.students.exists() or prog.courses.exists():
            messages.error(request, "Cannot delete Programme. It has associated Students or Courses.")
        else:
            prog.delete()
            messages.success(request, "Programme deleted successfully.")
        return redirect('institution:programme_list')
        
    return render(request, 'management/confirm_delete.html', {
        'object': prog, 
        'type': 'Programme',
        'cancel_url_name': 'institution:programme_list'
    })