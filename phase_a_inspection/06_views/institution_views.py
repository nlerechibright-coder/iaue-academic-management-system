from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from .models import Faculty, Department, Programme
from .forms import FacultyForm, DepartmentForm, ProgrammeForm
from accounts.models import User
from students.models import StudentProfile
from staff.models import StaffProfile
from academics.models import AcademicSession, Semester

def management_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.is_management)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper

@management_required
def management_dashboard(request):
    context = {
        'total_students': StudentProfile.objects.count(),
        'total_staff': StaffProfile.objects.count(),
        'total_faculties': Faculty.objects.count(),
        'total_departments': Department.objects.count(),
        'total_programmes': Programme.objects.count(),
        'active_session': AcademicSession.objects.filter(is_active=True).first(),
        'active_semester': Semester.objects.filter(is_active=True).first(),
    }
    return render(request, 'management/dashboard.html', context)

# Faculty CRUD
@management_required
def faculty_list(request):
    faculties = Faculty.objects.annotate(dept_count=Count('departments'))
    return render(request, 'management/faculty_list.html', {'faculties': faculties})

@management_required
def faculty_create(request):
    if request.method == 'POST':
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty created successfully.")
            return redirect('institution:faculty_list')
    else:
        form = FacultyForm()
    return render(request, 'management/faculty_form.html', {'form': form, 'title': 'Create Faculty'})

@management_required
def faculty_edit(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == 'POST':
        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty updated successfully.")
            return redirect('institution:faculty_list')
    else:
        form = FacultyForm(instance=faculty)
    return render(request, 'management/faculty_form.html', {'form': form, 'title': 'Edit Faculty'})

@management_required
def faculty_delete(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == 'POST':
        faculty.delete()
        messages.success(request, "Faculty deleted successfully.")
        return redirect('institution:faculty_list')
    return render(request, 'management/confirm_delete.html', {'object': faculty, 'url_name': 'institution:faculty_list'})

# Department CRUD
@management_required
def department_list(request):
    departments = Department.objects.select_related('faculty').all()
    return render(request, 'management/department_list.html', {'departments': departments})

@management_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully.")
            return redirect('institution:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'management/department_form.html', {'form': form, 'title': 'Create Department'})

@management_required
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully.")
            return redirect('institution:department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'management/department_form.html', {'form': form, 'title': 'Edit Department'})

@management_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, "Department deleted successfully.")
        return redirect('institution:department_list')
    return render(request, 'management/confirm_delete.html', {'object': department, 'url_name': 'institution:department_list'})

# Programme CRUD
@management_required
def programme_list(request):
    programmes = Programme.objects.select_related('department', 'department__faculty').all()
    return render(request, 'management/programme_list.html', {'programmes': programmes})

@management_required
def programme_create(request):
    if request.method == 'POST':
        form = ProgrammeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Programme created successfully.")
            return redirect('institution:programme_list')
    else:
        form = ProgrammeForm()
    return render(request, 'management/programme_form.html', {'form': form, 'title': 'Create Programme'})

@management_required
def programme_edit(request, pk):
    programme = get_object_or_404(Programme, pk=pk)
    if request.method == 'POST':
        form = ProgrammeForm(request.POST, instance=programme)
        if form.is_valid():
            form.save()
            messages.success(request, "Programme updated successfully.")
            return redirect('institution:programme_list')
    else:
        form = ProgrammeForm(instance=programme)
    return render(request, 'management/programme_form.html', {'form': form, 'title': 'Edit Programme'})

@management_required
def programme_delete(request, pk):
    programme = get_object_or_404(Programme, pk=pk)
    if request.method == 'POST':
        programme.delete()
        messages.success(request, "Programme deleted successfully.")
        return redirect('institution:programme_list')
    return render(request, 'management/confirm_delete.html', {'object': programme, 'url_name': 'institution:programme_list'})

