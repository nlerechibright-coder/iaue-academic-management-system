import csv
from io import StringIO
from decimal import Decimal
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from approvals.models import ApprovalAction
from courses.models import LecturerAssignment, CourseOffering
from registration.models import CourseRegistration, RegisteredCourseItem
from results.models import ResultSheet, StudentGrade
from staff.models import Appointment, StaffProfile
from students.models import StudentProfile


def _get_staff_profile(user):
    return getattr(user, 'staff_profile', None) or StaffProfile.objects.filter(user=user).first()


def _get_active_appointment(user, role):
    staff_profile = _get_staff_profile(user)
    if not staff_profile:
        return None
    today = timezone.now().date()
    return Appointment.objects.filter(
        staff=staff_profile,
        role=role,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
    ).order_by('-start_date').first()


def _can_manage_lecturer_sheet(user, sheet):
    staff_profile = _get_staff_profile(user)
    if not staff_profile:
        return False

    return (
        sheet.lecturer_id == staff_profile.pk
        or sheet.offering.assignments.filter(lecturer=staff_profile).exists()
    )


def _can_access_result_sheet(user, sheet):
    if user.is_superuser:
        return True

    if _can_manage_lecturer_sheet(user, sheet):
        return True

    hod_appointment = _get_active_appointment(user, 'HOD')
    if (
        hod_appointment
        and hod_appointment.department_id == sheet.offering.course.department_id
        and sheet.status in ['SUBMITTED', 'RETURNED', 'APPROVED_HOD', 'APPROVED_DEAN', 'VERIFIED_ER', 'PUBLISHED']
    ):
        return True

    dean_appointment = _get_active_appointment(user, 'DEAN')
    if (
        dean_appointment
        and dean_appointment.faculty_id == sheet.offering.course.department.faculty_id
        and sheet.status in ['APPROVED_HOD', 'APPROVED_DEAN', 'VERIFIED_ER', 'PUBLISHED']
    ):
        return True

    er_appointment = _get_active_appointment(user, 'EXAMS_RECORDS')
    if er_appointment and sheet.status in ['APPROVED_DEAN', 'VERIFIED_ER', 'PUBLISHED']:
        return True

    return False


def _can_action_result_sheet(user, sheet, role):
    if user.is_superuser:
        return True

    if role == 'LECTURER':
        return _can_manage_lecturer_sheet(user, sheet)

    if role == 'HOD':
        appointment = _get_active_appointment(user, 'HOD')
        if not appointment or not appointment.department_id:
            return False
        return sheet.offering.course.department_id == appointment.department_id

    if role == 'DEAN':
        appointment = _get_active_appointment(user, 'DEAN')
        if not appointment or not appointment.faculty_id:
            return False
        return sheet.offering.course.department.faculty_id == appointment.faculty_id

    if role == 'EXAMS_RECORDS':
        return _get_active_appointment(user, 'EXAMS_RECORDS') is not None

    return False


def _handle_result_transition(request, pk, role, allowed_statuses, next_status, action_type, success_message):
    if request.method != 'POST':
        messages.error(request, 'This action is only available via POST.')
        return redirect('results:sheet_detail', pk=pk)

    sheet = get_object_or_404(ResultSheet, pk=pk)
    if not _can_action_result_sheet(request.user, sheet, role):
        messages.error(request, f'You do not have permission to act as {role}.')
        return redirect('results:sheet_detail', pk=pk)

    if sheet.status not in allowed_statuses:
        messages.error(request, f'This result sheet cannot be {role.lower()} reviewed in its current status ({sheet.get_status_display()}).')
        return redirect('results:sheet_detail', pk=pk)

    comments = request.POST.get('comments', '').strip()
    
    # Update Status
    sheet.status = next_status
    sheet.submission_date = sheet.submission_date or timezone.now()
    sheet.save(update_fields=['status', 'submission_date', 'last_modified'])

    # Log Action
    ApprovalAction.objects.create(
        result_sheet=sheet,
        actor=request.user,
        role_performed=role,
        action_type=action_type,
        comments=comments,
    )

    messages.success(request, success_message)
    return redirect('results:sheet_detail', pk=sheet.pk)


@login_required
def result_dashboard(request):
    staff_profile = _get_staff_profile(request.user)
    if not staff_profile:
        messages.error(request, 'Access denied. Staff profile required.')
        return redirect('login')
    
    # Determine Roles
    is_lecturer = LecturerAssignment.objects.filter(lecturer=staff_profile).exists()
    is_hod = _get_active_appointment(request.user, 'HOD') is not None
    is_dean = _get_active_appointment(request.user, 'DEAN') is not None
    is_er = _get_active_appointment(request.user, 'EXAMS_RECORDS') is not None
    
    if not (request.user.is_superuser or is_lecturer or is_hod or is_dean or is_er):
        messages.error(request, 'Access denied. No academic role assigned.')
        return redirect('login')

    base_query = ResultSheet.objects.select_related(
        'offering__course',
        'offering__session',
        'lecturer__user',
    ).order_by('-submission_date', '-last_modified')

    # *** CRITICAL FIX START ***
    # We must construct separate queries for Ownership vs Supervision to prevent Draft leakage.
    
    final_conditions = Q()

    # 1. LECTURER SCOPE: Sees ALL their own sheets (Draft, Submitted, Returned, etc.)
    if is_lecturer:
        # Matches sheets where this user is the assigned lecturer
        lecturer_cond = Q(lecturer=staff_profile) | Q(offering__assignments__lecturer=staff_profile)
        final_conditions |= lecturer_cond

    # 2. SUPERVISORY SCOPES (HOD, DEAN, ER): See ONLY non-Draft sheets within their scope
    # If a user is BOTH Lecturer and HOD, they see their own drafts (via rule 1) 
    # AND other people's submitted results (via rule 2). They do NOT see other people's drafts.
    
    if is_hod:
        dept_appt = _get_active_appointment(request.user, 'HOD')
        if dept_appt and dept_appt.department_id:
            # Only show sheets in this department that are NOT DRAFT
            hod_cond = Q(offering__course__department=dept_appt.department) & ~Q(status='DRAFT')
            final_conditions |= hod_cond

    if is_dean:
        fac_appt = _get_active_appointment(request.user, 'DEAN')
        if fac_appt and fac_appt.faculty_id:
            # Only show sheets in this faculty that are NOT DRAFT
            dean_cond = Q(offering__course__department__faculty=fac_appt.faculty) & ~Q(status='DRAFT')
            final_conditions |= dean_cond

    if is_er:
        # Exams typically sees APPROVED_DEAN or VERIFIED_ER, but let's keep it broad minus Draft
        # Actually, ER usually shouldn't see SUBMITTED yet, but for safety we just exclude DRAFT
        # and rely on their specific dashboard view for granular control. 
        # However, for the main list, excluding DRAFT is key.
        er_cond = ~Q(status='DRAFT') 
        # Note: We might want to restrict ER further here if needed, e.g., status__in=[...], 
        # but excluding DRAFT solves the immediate leak.
        final_conditions |= er_cond

    # Apply Superuser override if applicable
    if request.user.is_superuser:
        final_conditions = Q() # Empty Q means all
        
    if final_conditions:
        sheets = base_query.filter(final_conditions).distinct()
    else:
        sheets = base_query.none() # Should not happen given checks above
            
    return render(request, 'results/dashboard.html', {'sheets': sheets, 'staff_profile': staff_profile})
    # *** CRITICAL FIX END ***


@login_required
def init_result_sheet(request, offering_id):
    try:
        profile = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        return redirect('login')

    offering = get_object_or_404(CourseOffering, pk=offering_id)
    
    is_assigned = LecturerAssignment.objects.filter(offering=offering, lecturer=profile).exists()
    is_admin = request.user.is_superuser or getattr(request.user, 'is_management', False)
    
    if not (is_assigned or is_admin):
        messages.error(request, "You are not authorized to initialize results for this course.")
        return redirect('staff:dashboard')

    sheet, created = ResultSheet.objects.get_or_create(
        offering=offering,
        defaults={
            'lecturer': profile,
            'status': 'DRAFT',
            'submission_date': None,
        }
    )

    if created:
        messages.success(request, f"Result sheet initialized for {offering.course.code}.")
    else:
        messages.info(request, f"Result sheet already exists for {offering.course.code}.")

    return redirect('results:sheet_detail', pk=sheet.pk)


@login_required
def save_manual_scores(request, pk):
    if request.method != 'POST':
        return redirect('results:sheet_detail', pk=pk)

    sheet = get_object_or_404(ResultSheet, pk=pk)
    
    if not _can_action_result_sheet(request.user, sheet, 'LECTURER'):
        messages.error(request, "You do not have permission to edit this sheet.")
        return redirect('results:sheet_detail', pk=pk)
        
    if sheet.status != 'DRAFT':
        messages.error(request, "Cannot edit submitted/published results.")
        return redirect('results:sheet_detail', pk=pk)

    updated_count = 0
    grades = StudentGrade.objects.filter(result_sheet=sheet)
    
    for grade in grades:
        ca_key = f'ca_{grade.id}'
        exam_key = f'exam_{grade.id}'
        remark_key = f'remark_{grade.id}'
        
        if ca_key in request.POST or exam_key in request.POST:
            try:
                ca_val = request.POST.get(ca_key)
                exam_val = request.POST.get(exam_key)
                
                if ca_val is not None and ca_val.strip() != '':
                    grade.ca_score = Decimal(ca_val)
                if exam_val is not None and exam_val.strip() != '':
                    grade.exam_score = Decimal(exam_val)
                    
                if remark_key in request.POST:
                    grade.remarks = request.POST.get(remark_key, '')
                
                grade.save()
                updated_count += 1
                
            except Exception as e:
                print(f"Error updating grade {grade.id}: {e}")

    messages.success(request, f"Saved {updated_count} student records successfully.")
    return redirect('results:sheet_detail', pk=pk)


@login_required
def hod_dashboard(request):
    appointment = _get_active_appointment(request.user, 'HOD')
    if not appointment or not appointment.department_id:
        messages.error(request, 'HOD access requires an active department appointment.')
        return redirect('login')

    # Explicitly filter out DRAFTs here as well for double safety
    sheets = ResultSheet.objects.select_related(
        'offering__course__department',
        'offering__session',
        'lecturer__user',
    ).filter(
        offering__course__department=appointment.department,
        status__in=['SUBMITTED', 'RETURNED'],
    ).exclude(status='DRAFT').order_by('-last_modified')

    return render(request, 'results/hod_dashboard.html', {'sheets': sheets, 'appointment': appointment})


@login_required
def dean_dashboard(request):
    appointment = _get_active_appointment(request.user, 'DEAN')
    if not appointment or not appointment.faculty_id:
        messages.error(request, 'Dean access requires an active faculty appointment.')
        return redirect('login')

    sheets = ResultSheet.objects.select_related(
        'offering__course__department__faculty',
        'offering__session',
        'lecturer__user',
    ).filter(
        offering__course__department__faculty=appointment.faculty,
        status='APPROVED_HOD',
    ).exclude(status='DRAFT').order_by('-last_modified')

    return render(request, 'results/dean_dashboard.html', {'sheets': sheets, 'appointment': appointment})


@login_required
def exams_dashboard(request):
    appointment = _get_active_appointment(request.user, 'EXAMS_RECORDS')
    if not appointment:
        messages.error(request, 'Exams and Records access requires an active appointment.')
        return redirect('login')

    sheets = ResultSheet.objects.select_related(
        'offering__course__department',
        'offering__session',
        'lecturer__user',
    ).filter(
        status='APPROVED_DEAN',
    ).exclude(status='DRAFT').order_by('-last_modified')

    return render(request, 'results/exams_dashboard.html', {'sheets': sheets, 'appointment': appointment})


@login_required
def result_sheet_detail(request, pk):
    sheet = get_object_or_404(
        ResultSheet.objects.select_related(
            'offering__course',
            'offering__session',
            'lecturer__user',
        ),
        pk=pk,
    )

    if not _can_access_result_sheet(request.user, sheet):
        messages.error(request, 'You do not have access to this result sheet.')
        return redirect('results:dashboard')

    registered_items = RegisteredCourseItem.objects.filter(
        offering=sheet.offering
    ).select_related('registration__student')

    existing_student_ids = set(sheet.grades.values_list('student_id', flat=True))

    new_grades_to_create = []
    for item in registered_items:
        student = item.registration.student
        if student.id not in existing_student_ids:
            new_grades_to_create.append(StudentGrade(
                result_sheet=sheet,
                student=student,
                ca_score=Decimal('0'),
                exam_score=Decimal('0'),
                remarks=''
            ))
    
    if new_grades_to_create:
        for grade_obj in new_grades_to_create:
            grade_obj.save()
        
    grades = sheet.grades.select_related('student__user').order_by('student__matric_number')

    context = {
        'sheet': sheet,
        'grades': grades,
        'can_hod_approve': _can_action_result_sheet(request.user, sheet, 'HOD') and sheet.status in ['SUBMITTED', 'RETURNED'],
        'can_dean_approve': _can_action_result_sheet(request.user, sheet, 'DEAN') and sheet.status == 'APPROVED_HOD',
        'can_verify_er': _can_action_result_sheet(request.user, sheet, 'EXAMS_RECORDS') and sheet.status == 'APPROVED_DEAN',
        'can_publish_result': _can_action_result_sheet(request.user, sheet, 'EXAMS_RECORDS') and sheet.status == 'VERIFIED_ER',
    }
    return render(request, 'results/result_sheet_detail.html', context)


@login_required
def hod_approve_result_sheet(request, pk):
    return _handle_result_transition(
        request,
        pk,
        'HOD',
        ['SUBMITTED', 'RETURNED'],
        'APPROVED_HOD',
        'APPROVE',
        'Result sheet approved by the Head of Department.',
    )

@login_required
def hod_return_result_sheet(request, pk):
    """HOD Returns results to Lecturer"""
    return _handle_result_transition(
        request,
        pk,
        'HOD',
        ['SUBMITTED', 'RETURNED'],
        'RETURNED',
        'RETURN',
        'Result sheet returned to lecturer for correction.',
    )

@login_required
def dean_approve_result_sheet(request, pk):
    return _handle_result_transition(
        request,
        pk,
        'DEAN',
        ['APPROVED_HOD'],
        'APPROVED_DEAN',
        'APPROVE',
        'Result sheet approved by the Dean.',
    )

@login_required
def dean_return_result_sheet(request, pk):
    """Dean Returns results to HOD/Lecturer"""
    return _handle_result_transition(
        request,
        pk,
        'DEAN',
        ['APPROVED_HOD'],
        'RETURNED',
        'RETURN',
        'Result sheet returned for correction.',
    )

@login_required
def exams_verify_result_sheet(request, pk):
    return _handle_result_transition(
        request,
        pk,
        'EXAMS_RECORDS',
        ['APPROVED_DEAN'],
        'VERIFIED_ER',
        'VERIFY',
        'Result sheet verified by Exams and Records.',
    )

@login_required
def er_return_result_sheet(request, pk):
    """Exams Returns results to Dean/HOD"""
    return _handle_result_transition(
        request,
        pk,
        'EXAMS_RECORDS',
        ['APPROVED_DEAN', 'VERIFIED_ER'],
        'RETURNED',
        'RETURN',
        'Result sheet returned for correction.',
    )

@login_required
def publish_result_sheet(request, pk):
    return _handle_result_transition(
        request,
        pk,
        'EXAMS_RECORDS',
        ['VERIFIED_ER'],
        'PUBLISHED',
        'PUBLISH',
        'Result sheet published to students.',
    )


@login_required
def download_result_template(request, pk=None):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['matric_number', 'full_name', 'ca_score', 'exam_score', 'remarks'])

    target_students = []
    filename_suffix = "generic"
    
    try:
        if pk and int(pk) > 0:
            sheet = ResultSheet.objects.select_related('offering__course').get(pk=pk)
            
            registrations = RegisteredCourseItem.objects.filter(
                offering=sheet.offering
            ).select_related('registration__student__user')
            
            seen_matrics = set()
            for reg_item in registrations:
                if reg_item.registration and reg_item.registration.student:
                    stu = reg_item.registration.student
                    if stu.matric_number not in seen_matrics:
                        seen_matrics.add(stu.matric_number)
                        target_students.append({
                            'matric': stu.matric_number,
                            'name': stu.user.get_full_name(),
                        })
            
            filename_suffix = f"{sheet.offering.course.code}_{sheet.offering.session.name.replace('/', '_')}"
        
    except (ValueError, TypeError, ResultSheet.DoesNotExist):
        pass

    if target_students:
        for s in target_students:
            writer.writerow([s['matric'], s['name'], '', '', ''])
    else:
        writer.writerow(['U/2026/00001', 'Sample Student', '15', '45', 'Example'])

    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="result_template_{filename_suffix}.csv"'
    return response


@login_required
def upload_result_csv(request, pk):
    sheet = get_object_or_404(ResultSheet, pk=pk)
    if not _can_action_result_sheet(request.user, sheet, 'LECTURER'):
        messages.error(request, 'You do not have access to this result sheet.')
        return redirect('results:dashboard')

    if request.method == 'POST':
        uploaded_file = request.FILES.get('csv_file')
        if not uploaded_file:
            messages.error(request, 'Please upload a CSV file.')
            return redirect('results:sheet_detail', pk=sheet.pk)

        try:
            content = uploaded_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(request, 'The uploaded file is not valid UTF-8 text.')
            return redirect('results:sheet_detail', pk=sheet.pk)

        reader = csv.DictReader(StringIO(content))
        if not reader.fieldnames or not {'matric_number', 'ca_score', 'exam_score'} <= set(reader.fieldnames):
            messages.error(request, 'CSV must contain matric_number, ca_score and exam_score columns.')
            return redirect('results:sheet_detail', pk=sheet.pk)

        entries = 0
        errors = []
        
        for row in reader:
            matric_number = (row.get('matric_number') or '').strip()
            if not matric_number:
                continue

            student = StudentProfile.objects.filter(matric_number__iexact=matric_number).first()
            if not student:
                errors.append(f"No student found for {matric_number}")
                continue

            grade, created = StudentGrade.objects.get_or_create(result_sheet=sheet, student=student)
            try:
                grade.ca_score = Decimal(str(row.get('ca_score') or 0))
                grade.exam_score = Decimal(str(row.get('exam_score') or 0))
            except Exception:
                errors.append(f"Invalid score format for {matric_number}")
                continue
                
            grade.remarks = row.get('remarks') or ''
            grade.save()
            entries += 1

        if errors:
            messages.warning(request, f"Some rows skipped: {'; '.join(errors[:3])}...")

        sheet.status = 'SUBMITTED'
        sheet.submission_date = timezone.now()
        sheet.save(update_fields=['status', 'submission_date', 'last_modified'])
        
        ApprovalAction.objects.create(
            result_sheet=sheet,
            actor=request.user,
            role_performed='LECTURER',
            action_type='SUBMIT',
            comments=f'CSV results uploaded ({entries} records).',
        )
        messages.success(request, f'Successfully processed {entries} student results.')
        return redirect('results:sheet_detail', pk=sheet.pk)

    return render(request, 'results/upload_csv.html', {'sheet': sheet})


@login_required
def submit_result_sheet(request, pk):
    sheet = get_object_or_404(ResultSheet, pk=pk)
    if not _can_action_result_sheet(request.user, sheet, 'LECTURER'):
        messages.error(request, 'You do not have access to this result sheet.')
        return redirect('results:dashboard')

    sheet.status = 'SUBMITTED'
    sheet.submission_date = timezone.now()
    sheet.save(update_fields=['status', 'submission_date', 'last_modified'])
    ApprovalAction.objects.create(
        result_sheet=sheet,
        actor=request.user,
        role_performed='LECTURER',
        action_type='SUBMIT',
        comments='Lecturer submitted result sheet for review.',
    )
    messages.success(request, f'Result sheet for {sheet.offering.course.code} was submitted for review.')
    return redirect('results:sheet_detail', pk=sheet.pk)


@login_required
def student_view_results(request):
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "No student profile found.")
        return redirect('students:dashboard')

    all_published_grades = StudentGrade.objects.filter(
        student=profile,
        result_sheet__status='PUBLISHED'
    ).select_related(
        'result_sheet__offering__course',
        'result_sheet__offering__session'
    ).order_by('result_sheet__offering__course__level', 'result_sheet__offering__session__name')

    grouped_published = {}
    global_total_units = 0
    global_total_points = 0
    
    for grade in all_published_grades:
        course = grade.result_sheet.offering.course
        session = grade.result_sheet.offering.session
        level = course.level
        semester_key = course.semester if hasattr(course, 'semester') else 'General'
        
        if level not in grouped_published:
            grouped_published[level] = {}
            
        if semester_key not in grouped_published[level]:
            grouped_published[level][semester_key] = {
                'grades': [],
                'total_units': 0,
                'total_points': 0,
                'gpa': 0.0
            }
            
        grouped_published[level][semester_key]['grades'].append(grade)
        
        units = int(course.credit_units)
        points = float(grade.grade_point) * units
        
        grouped_published[level][semester_key]['total_units'] += units
        grouped_published[level][semester_key]['total_points'] += points
        
        global_total_units += units
        global_total_points += points

    for level in grouped_published:
        for sem_key in grouped_published[level]:
            data = grouped_published[level][sem_key]
            if data['total_units'] > 0:
                data['gpa'] = round(data['total_points'] / data['total_units'], 2)
                
    sorted_levels = sorted(grouped_published.keys())
    
    published_structure = []
    for level in sorted_levels:
        semesters = grouped_published[level]
        sorted_sems = sorted(semesters.items(), key=lambda x: x[0])
        published_structure.append({
            'level': level,
            'semesters': [
                {'name': sem_name, 'data': sem_data} for sem_name, sem_data in sorted_sems
            ]
        })

    failed_courses_list = [g for g in all_published_grades if g.grade_letter == 'F']

    registered_offerings_ids = RegisteredCourseItem.objects.filter(
        registration__student=profile,
    ).values_list('offering_id', flat=True) 
    
    registered_offerings_ids = list(set(registered_offerings_ids))

    registered_offerings = CourseOffering.objects.filter(
        id__in=registered_offerings_ids
    ).select_related('course', 'session')
    
    missing_results = []
    for off in registered_offerings:
        sheet = ResultSheet.objects.filter(offering=off).first()
        
        if not sheet:
            missing_results.append({
                'offering': off,
                'reason': 'Not Uploaded'
            })
        elif sheet.status != 'PUBLISHED':
            missing_results.append({
                'offering': off,
                'reason': sheet.get_status_display()
            })
            
    missing_results.sort(key=lambda x: (x['offering'].course.level, x['offering'].session.name))

    global_gpa = round(global_total_points / global_total_units, 2) if global_total_units > 0 else 0.0

    context = {
        'published_structure': published_structure,
        'failed_courses': failed_courses_list,
        'missing_results': missing_results,
        'profile': profile,
        'cumulative_gpa': global_gpa,
        'total_units': global_total_units,
        'has_published': bool(published_structure),
        'has_failures': len(failed_courses_list) > 0,
        'has_missing': len(missing_results) > 0
    }
    
    return render(request, 'results/student_results.html', context)
