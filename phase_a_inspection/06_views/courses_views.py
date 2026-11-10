from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Course, CourseOffering, Section, LecturerAssignment
from .forms import CourseForm, CourseOfferingForm, SectionForm, LecturerAssignmentForm

def management_required(view_func):
    @login_required
    @user_passes_test(lambda u: u.is_management)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper

# Course Catalogue CRUD
@management_required
def course_list(request):
    courses = Course.objects.select_related('department', 'programme').all()
    return render(request, 'courses/course_list.html', {'courses': courses})

@management_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course created successfully.")
            return redirect('courses:course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Create Course'})

@management_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('courses:course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Edit Course'})

@management_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully.")
        return redirect('courses:course_list')
    return render(request, 'management/confirm_delete.html', {'object': course, 'url_name': 'courses:course_list'})

# Course Offering CRUD
@management_required
def offering_list(request):
    offerings = CourseOffering.objects.select_related('course', 'session').all()
    return render(request, 'courses/offering_list.html', {'offerings': offerings})

@management_required
def offering_create(request):
    if request.method == 'POST':
        form = CourseOfferingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course offering created successfully.")
            return redirect('courses:offering_list')
    else:
        form = CourseOfferingForm()
    return render(request, 'courses/offering_form.html', {'form': form, 'title': 'Create Course Offering'})

@management_required
def offering_edit(request, pk):
    offering = get_object_or_404(CourseOffering, pk=pk)
    if request.method == 'POST':
        form = CourseOfferingForm(request.POST, instance=offering)
        if form.is_valid():
            form.save()
            messages.success(request, "Course offering updated successfully.")
            return redirect('courses:offering_list')
    else:
        form = CourseOfferingForm(instance=offering)
    return render(request, 'courses/offering_form.html', {'form': form, 'title': 'Edit Course Offering'})

@management_required
def offering_delete(request, pk):
    offering = get_object_or_404(CourseOffering, pk=pk)
    if request.method == 'POST':
        offering.delete()
        messages.success(request, "Course offering deleted successfully.")
        return redirect('courses:offering_list')
    return render(request, 'management/confirm_delete.html', {'object': offering, 'url_name': 'courses:offering_list'})

# Section CRUD
@management_required
def section_list(request):
    sections = Section.objects.select_related('offering__course').all()
    return render(request, 'courses/section_list.html', {'sections': sections})

@management_required
def section_create(request):
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Section created successfully.")
            return redirect('courses:section_list')
    else:
        form = SectionForm()
    return render(request, 'courses/section_form.html', {'form': form, 'title': 'Create Section'})

@management_required
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, "Section updated successfully.")
            return redirect('courses:section_list')
    else:
        form = SectionForm(instance=section)
    return render(request, 'courses/section_form.html', {'form': form, 'title': 'Edit Section'})

@management_required
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        section.delete()
        messages.success(request, "Section deleted successfully.")
        return redirect('courses:section_list')
    return render(request, 'management/confirm_delete.html', {'object': section, 'url_name': 'courses:section_list'})

# Lecturer Assignment CRUD
@management_required
def assignment_list(request):
    assignments = LecturerAssignment.objects.select_related('offering__course', 'section', 'lecturer__user').all()
    return render(request, 'courses/assignment_list.html', {'assignments': assignments})

@management_required
def assignment_create(request):
    if request.method == 'POST':
        form = LecturerAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lecturer assigned successfully.")
            return redirect('courses:assignment_list')
    else:
        form = LecturerAssignmentForm()
    return render(request, 'courses/assignment_form.html', {'form': form, 'title': 'Assign Lecturer'})

@management_required
def assignment_edit(request, pk):
    assignment = get_object_or_404(LecturerAssignment, pk=pk)
    if request.method == 'POST':
        form = LecturerAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, "Lecturer assignment updated successfully.")
            return redirect('courses:assignment_list')
    else:
        form = LecturerAssignmentForm(instance=assignment)
    return render(request, 'courses/assignment_form.html', {'form': form, 'title': 'Edit Lecturer Assignment'})

@management_required
def assignment_delete(request, pk):
    assignment = get_object_or_404(LecturerAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, "Lecturer assignment removed successfully.")
        return redirect('courses:assignment_list')
    return render(request, 'management/confirm_delete.html', {'object': assignment, 'url_name': 'courses:assignment_list'})
