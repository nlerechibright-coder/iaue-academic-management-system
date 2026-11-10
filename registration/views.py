# registration/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone

from students.models import StudentProfile
from academics.models import AcademicSession
from courses.models import CourseOffering
from .models import CourseRegistration, RegisteredCourseItem

@login_required
def registration_dashboard(request):
    """
    Displays available courses filtered by student's department and level.
    Separates Selected vs Available for better UX.
    """
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "No student profile found.")
        return redirect('login')

    # Get Active Session
    session = AcademicSession.objects.filter(is_active=True).first()
    
    if not session:
        context = {
            'error_message': "No active academic session configured.",
            'offerings': [],
            'profile': profile,
            'current_registration': None,
            'query': '',
        }
        return render(request, 'registration/register_courses.html', context)

    # Determine Current Semester Type
    current_semester_type = request.GET.get('sem', 'FIRST') 

    # GET OR CREATE CURRENT REGISTRATION HEADER
    current_reg, created = CourseRegistration.objects.get_or_create(
        student=profile,
        session=session,
        semester_type=current_semester_type,
        defaults={'status': 'DRAFT'}
    )

    # FETCH SELECTED ITEMS (For the top section)
    registered_items_qs = RegisteredCourseItem.objects.filter(
        registration=current_reg,
        status='ACTIVE'
    ).select_related('offering__course').order_by('offering__course__code')
    
    # Convert to list for easier iteration in template if needed, though QuerySet works fine
    registered_items_list = list(registered_items_qs)
    
    # Calculate Stats based on selected items
    total_registered_count = len(registered_items_list)
    total_credits = sum(item.offering.course.credit_units for item in registered_items_list)

    # FILTER LOGIC: Available Courses (Exclude already selected)
    base_queryset = CourseOffering.objects.filter(
        session=session,
        semester_type=current_semester_type,
        course__department=profile.department,
        level=profile.level
    ).select_related('course', 'course__department', 'session')

    # SEARCH FUNCTIONALITY
    query = request.GET.get('q')
    if query:
        base_queryset = base_queryset.filter(
            Q(course__code__icontains=query) | 
            Q(course__title__icontains=query)
        )

    # EXCLUDE ALREADY REGISTERED COURSES
    registered_offering_ids = [item.offering_id for item in registered_items_list]
    available_offerings = base_queryset.exclude(id__in=registered_offering_ids)

    context = {
        'profile': profile,
        'offerings': available_offerings,       # Bottom List
        'registered_items': registered_items_list, # Top List
        'session': session,
        'semester_type': current_semester_type,
        'query': query,
        'current_registration': current_reg,
        'total_registered_count': total_registered_count,
        'total_credits': total_credits,
    }
    
    return render(request, 'registration/register_courses.html', context)


@login_required
def register_course(request, offering_id):
    """
    Adds a specific course offering to the student's registration list.
    Blocked if registration is not DRAFT.
    """
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return redirect('login')

    offering = get_object_or_404(CourseOffering, pk=offering_id)
    
    # SECURITY CHECK: Eligibility
    if offering.course.department != profile.department or offering.level != profile.level:
        messages.error(request, "You are not eligible to register for this course.")
        return redirect('registration:dashboard')

    session = offering.session
    semester_type = offering.semester_type
    
    if not session:
        messages.error(request, "Invalid course offering data.")
        return redirect('registration:dashboard')

    # GET CURRENT REGISTRATION
    reg, created = CourseRegistration.objects.get_or_create(
        student=profile,
        session=session,
        semester_type=semester_type,
        defaults={'status': 'DRAFT'}
    )

    # BUSINESS RULE: Cannot modify if not DRAFT
    if reg.status != 'DRAFT':
        messages.error(request, "Your registration has been submitted. You cannot add new courses now.")
        return redirect('registration:dashboard')

    # CHECK DUPLICATE
    if RegisteredCourseItem.objects.filter(registration=reg, offering=offering).exists():
        messages.info(request, "You have already registered for this course.")
        return redirect('registration:dashboard')

    # CREATE THE LINK
    try:
        RegisteredCourseItem.objects.create(
            registration=reg,
            offering=offering,
            status='ACTIVE'
        )
        messages.success(request, f"Added {offering.course.code} to your schedule.")
    except Exception as e:
        messages.error(request, f"Error registering course: {str(e)}")

    return redirect('registration:dashboard')


@login_required
def unregister_course(request, offering_id):
    """
    Removes a course from the student's schedule.
    Blocked if registration is not DRAFT.
    """
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return redirect('login')

    offering = get_object_or_404(CourseOffering, pk=offering_id)
    session = offering.session
    semester_type = offering.semester_type

    reg = CourseRegistration.objects.filter(
        student=profile,
        session=session,
        semester_type=semester_type
    ).first()

    if reg:
        # BUSINESS RULE: Cannot modify if not DRAFT
        if reg.status != 'DRAFT':
            messages.error(request, "Your registration has been submitted. You cannot remove courses now.")
            return redirect('registration:dashboard')

        item = RegisteredCourseItem.objects.filter(
            registration=reg, 
            offering=offering,
            status='ACTIVE'
        ).first()
        
        if item:
            item.status = 'WITHDRAWN'
            item.save() # Triggers parent update
            messages.success(request, f"Withdrew from {offering.course.code}.")
        else:
            messages.warning(request, "Course not found in your active selection.")
    else:
        messages.error(request, "No active registration found.")

    return redirect('registration:dashboard')


@login_required
def confirm_registration(request):
    """
    Finalizes the registration process. Changes status from DRAFT to PENDING.
    Once confirmed, editing is locked.
    """
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return redirect('login')

    session = AcademicSession.objects.filter(is_active=True).first()
    if not session:
        return redirect('registration:dashboard')

    # Assume user wants to confirm the current semester view
    current_semester_type = request.GET.get('sem', 'FIRST') 
    
    reg = CourseRegistration.objects.filter(
        student=profile,
        session=session,
        semester_type=current_semester_type
    ).first()

    if not reg:
        messages.error(request, "No draft registration found to confirm.")
        return redirect('registration:dashboard')

    if reg.status != 'DRAFT':
        messages.info(request, "This registration has already been processed.")
        return redirect('registration:dashboard')

    # Validate Minimum Requirements (Example: At least 1 course)
    active_items_count = RegisteredCourseItem.objects.filter(registration=reg, status='ACTIVE').count()
    if active_items_count == 0:
        messages.error(request, "Please select at least one course before confirming.")
        return redirect('registration:dashboard')

    # Check Credit Limit
    if reg.total_credit_units > reg.max_allowed_units:
        messages.error(request, f"You exceed the maximum credit limit ({reg.max_allowed_units}). Please remove some courses.")
        return redirect('registration:dashboard')

    # UPDATE STATUS
    reg.status = 'PENDING'
    reg.save()
    
    messages.success(request, "Registration submitted successfully! Waiting for approval.")
    return redirect('registration:dashboard')