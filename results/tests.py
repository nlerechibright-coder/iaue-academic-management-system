from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from academics.models import AcademicSession
from courses.models import Course, CourseOffering, LecturerAssignment
from institution.models import Department, Faculty, Programme
from results.models import ResultSheet, StudentGrade
from staff.models import StaffProfile
from students.models import StudentProfile


class ResultWorkflowTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name='Science', code='SCI')
        self.department = Department.objects.create(name='Computer Science', code='CSC', faculty=self.faculty)
        self.programme = Programme.objects.create(name='BSc Computer Science', code='BCS', department=self.department, max_level=400)
        self.session = AcademicSession.objects.create(name='2024/2025', is_active=True)

        self.lecturer_user = get_user_model().objects.create_user(username='lecturer1', password='Password123!')
        self.lecturer_profile = StaffProfile.objects.create(user=self.lecturer_user, staff_id='STAFF-001', department=self.department)

        self.course = Course.objects.create(
            code='CSC401',
            title='Software Engineering',
            department=self.department,
            programme=self.programme,
            level=400,
            semester='FIRST',
            credit_units=3,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            session=self.session,
            semester_type='FIRST',
            level=400,
        )
        LecturerAssignment.objects.create(offering=self.offering, lecturer=self.lecturer_profile)

        self.student_user = get_user_model().objects.create_user(username='student1', password='Password123!')
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            matric_number='u/2024/00001',
            department=self.department,
            programme=self.programme,
            level=400,
        )

        self.sheet = ResultSheet.objects.create(offering=self.offering, lecturer=self.lecturer_profile)

    def test_lecturer_can_access_assigned_result_sheet(self):
        self.client.force_login(self.lecturer_user)
        response = self.client.get(f'/results/{self.sheet.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.code)

    def test_result_sheet_submission_changes_status(self):
        self.client.force_login(self.lecturer_user)
        response = self.client.post(f'/results/{self.sheet.pk}/submit/')
        self.assertEqual(response.status_code, 302)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, 'SUBMITTED')

    def test_csv_upload_creates_result_records(self):
        self.client.force_login(self.lecturer_user)
        csv_data = 'matric_number,ca_score,exam_score,remarks\nu/2024/00001,18,60,Good\n'
        response = self.client.post(
            f'/results/{self.sheet.pk}/upload/',
            {'csv_file': SimpleUploadedFile('results.csv', csv_data.encode('utf-8'), content_type='text/csv')},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StudentGrade.objects.filter(result_sheet=self.sheet, student=self.student).exists())

        grade = StudentGrade.objects.get(result_sheet=self.sheet, student=self.student)
        self.assertEqual(float(grade.total_score), 78.0)
        self.assertEqual(grade.grade_letter, 'A')

    def test_staff_flag_does_not_grant_access_to_unassigned_result_sheets(self):
        staff_user = get_user_model().objects.create_user(
            username='unassigned-staff',
            password='Password123!',
            is_staff=True,
        )
        StaffProfile.objects.create(
            user=staff_user,
            staff_id='STAFF-002',
            department=self.department,
        )
        self.client.force_login(staff_user)

        dashboard = self.client.get(reverse('results:dashboard'))
        self.assertEqual(dashboard.status_code, 302)

        detail = self.client.get(reverse('results:sheet_detail', args=[self.sheet.pk]))
        self.assertEqual(detail.status_code, 302)

        submit = self.client.post(reverse('results:submit_sheet', args=[self.sheet.pk]))
        self.assertEqual(submit.status_code, 302)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, 'DRAFT')

        upload = self.client.post(
            reverse('results:upload_csv', args=[self.sheet.pk]),
            {'csv_file': SimpleUploadedFile('results.csv', b'matric_number,ca_score,exam_score\n')},
        )
        self.assertEqual(upload.status_code, 302)
        self.assertFalse(StudentGrade.objects.filter(result_sheet=self.sheet).exists())

    def test_staff_user_only_sees_results_for_assigned_offerings(self):
        staff_user = get_user_model().objects.create_user(
            username='assigned-staff',
            password='Password123!',
            is_staff=True,
        )
        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            staff_id='STAFF-003',
            department=self.department,
        )
        assigned_course = Course.objects.create(
            code='CSC402',
            title='Database Systems',
            department=self.department,
            programme=self.programme,
            level=400,
            semester='FIRST',
            credit_units=3,
        )
        assigned_offering = CourseOffering.objects.create(
            course=assigned_course,
            session=self.session,
            semester_type='FIRST',
            level=400,
        )
        LecturerAssignment.objects.create(offering=assigned_offering, lecturer=staff_profile)
        assigned_sheet = ResultSheet.objects.create(offering=assigned_offering, lecturer=staff_profile)
        self.client.force_login(staff_user)

        dashboard = self.client.get(reverse('results:dashboard'))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, assigned_course.code)
        self.assertNotContains(dashboard, self.course.code)
        self.assertEqual(
            self.client.get(reverse('results:sheet_detail', args=[assigned_sheet.pk])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse('results:sheet_detail', args=[self.sheet.pk])).status_code,
            302,
        )


class ResultApprovalWorkflowTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name='Engineering', code='ENG')
        self.department = Department.objects.create(name='Electrical Engineering', code='EEE', faculty=self.faculty)
        self.programme = Programme.objects.create(name='B.Eng Electrical', code='BEE', department=self.department, max_level=400)
        self.session = AcademicSession.objects.create(name='2024/2025', is_active=True)

        self.lecturer_user = get_user_model().objects.create_user(username='lecturer-hod', password='Password123!')
        self.lecturer_profile = StaffProfile.objects.create(user=self.lecturer_user, staff_id='STAFF-100', department=self.department)

        self.hod_user = get_user_model().objects.create_user(username='hod-user', password='Password123!')
        self.hod_profile = StaffProfile.objects.create(user=self.hod_user, staff_id='STAFF-101', department=self.department)

        self.dean_user = get_user_model().objects.create_user(username='dean-user', password='Password123!')
        self.dean_profile = StaffProfile.objects.create(user=self.dean_user, staff_id='STAFF-102', department=self.department)

        self.er_user = get_user_model().objects.create_user(username='er-user', password='Password123!')
        self.er_profile = StaffProfile.objects.create(user=self.er_user, staff_id='STAFF-103', department=self.department)

        self.course = Course.objects.create(
            code='EEE401',
            title='Power Systems',
            department=self.department,
            programme=self.programme,
            level=400,
            semester='FIRST',
            credit_units=3,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            session=self.session,
            semester_type='FIRST',
            level=400,
        )
        LecturerAssignment.objects.create(offering=self.offering, lecturer=self.lecturer_profile)

        self.student_user = get_user_model().objects.create_user(username='student-result', password='Password123!')
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            matric_number='u/2024/00002',
            department=self.department,
            programme=self.programme,
            level=400,
        )

        self.sheet = ResultSheet.objects.create(offering=self.offering, lecturer=self.lecturer_profile, status='SUBMITTED')
        self.sheet.grades.create(student=self.student, ca_score=20, exam_score=60)

        self.hod_appointment = self.hod_profile.appointments.create(
            role='HOD',
            department=self.department,
            start_date='2024-01-01',
            end_date='2030-12-31',
            is_active=True,
            appointed_by=self.lecturer_user,
        )
        self.dean_appointment = self.dean_profile.appointments.create(
            role='DEAN',
            faculty=self.faculty,
            start_date='2024-01-01',
            end_date='2030-12-31',
            is_active=True,
            appointed_by=self.lecturer_user,
        )
        self.er_appointment = self.er_profile.appointments.create(
            role='EXAMS_RECORDS',
            start_date='2024-01-01',
            end_date='2030-12-31',
            is_active=True,
            appointed_by=self.lecturer_user,
        )

    def test_hod_dashboard_and_approval_flow(self):
        self.client.force_login(self.hod_user)
        response = self.client.get('/management/hod/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.code)
        detail = self.client.get(reverse('results:sheet_detail', args=[self.sheet.pk]))
        self.assertEqual(detail.status_code, 200)

        approve = self.client.post(f'/results/{self.sheet.pk}/hod-approve/')
        self.assertEqual(approve.status_code, 302)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, 'APPROVED_HOD')

    def test_dean_dashboard_and_approval_flow(self):
        self.sheet.status = 'APPROVED_HOD'
        self.sheet.save(update_fields=['status'])

        self.client.force_login(self.dean_user)
        response = self.client.get('/management/dean/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.code)
        detail = self.client.get(reverse('results:sheet_detail', args=[self.sheet.pk]))
        self.assertEqual(detail.status_code, 200)

        approve = self.client.post(f'/results/{self.sheet.pk}/dean-approve/')
        self.assertEqual(approve.status_code, 302)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, 'APPROVED_DEAN')

    def test_exams_records_dashboard_and_publication_flow(self):
        self.sheet.status = 'APPROVED_DEAN'
        self.sheet.save(update_fields=['status'])

        self.client.force_login(self.er_user)
        response = self.client.get('/management/exams-records/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.code)
        detail = self.client.get(reverse('results:sheet_detail', args=[self.sheet.pk]))
        self.assertEqual(detail.status_code, 200)

        verify = self.client.post(f'/results/{self.sheet.pk}/exams-verify/')
        self.assertEqual(verify.status_code, 302)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, 'VERIFIED_ER')

        publish = self.client.post(f'/results/{self.sheet.pk}/publish/')
        self.assertEqual(publish.status_code, 302)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, 'PUBLISHED')

        self.assertTrue(self.sheet.approval_history.exists())
