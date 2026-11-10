from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from academics.models import AcademicSession
from courses.models import Course, CourseOffering
from institution.models import Department, Faculty, Programme
from registration.models import CourseRegistration
from students.models import StudentProfile


class StudentRegistrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='student-1001',
            password='Student123!',
            is_active=True,
        )

        faculty = Faculty.objects.create(name='Faculty of Science', code='FSC')
        department = Department.objects.create(name='Computer Science', code='CSC', faculty=faculty)
        programme = Programme.objects.create(name='B.Sc. Computer Science', code='CSC', department=department, max_level=500)
        self.session = AcademicSession.objects.create(name='2025/2026', is_active=True)

        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            matric_number='u/2025/00001',
            department=department,
            programme=programme,
            level=200,
        )

        self.current_course = Course.objects.create(
            code='CSC201',
            title='Data Structures',
            department=department,
            programme=programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        self.carryover_course = Course.objects.create(
            code='CSC101',
            title='Introduction to Computing',
            department=department,
            programme=programme,
            level=100,
            semester='FIRST',
            credit_units=4,
            is_compulsory=True,
        )

        self.current_offering = CourseOffering.objects.create(
            course=self.current_course,
            session=self.session,
            semester_type='FIRST',
            level=200,
        )
        self.carryover_offering = CourseOffering.objects.create(
            course=self.carryover_course,
            session=self.session,
            semester_type='FIRST',
            level=100,
        )

        self.client = Client()
        self.client.login(username='student-1001', password='Student123!')

    def test_current_level_courses_are_loaded_for_student(self):
        response = self.client.get('/student/registration/', {'session': str(self.session.id), 'semester': 'FIRST'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.current_course.code)
        self.assertContains(response, self.current_course.title)

    def test_current_level_allocation_cannot_exceed_19_credit_units(self):
        extra_offerings = []
        for idx in range(7):
            course = Course.objects.create(
                code=f'CSC{400 + idx}',
                title=f'Current Level Course {idx}',
                department=self.student_profile.department,
                programme=self.student_profile.programme,
                level=200,
                semester='FIRST',
                credit_units=3,
                is_compulsory=True,
            )
            offering = CourseOffering.objects.create(
                course=course,
                session=self.session,
                semester_type='FIRST',
                level=200,
            )
            extra_offerings.append(str(offering.id))

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': extra_offerings,
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Current-level allocation cannot exceed 19 credit units')

    def test_eligible_carryover_selection_uses_remaining_capacity(self):
        current_course_one = Course.objects.create(
            code='CSC210',
            title='Algorithms',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_two = Course.objects.create(
            code='CSC220',
            title='Operating Systems',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_three = Course.objects.create(
            code='CSC230',
            title='Computer Architecture',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_four = Course.objects.create(
            code='CSC240',
            title='Networks',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_five = Course.objects.create(
            code='CSC250',
            title='Logic Design',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_offering_one = CourseOffering.objects.create(course=current_course_one, session=self.session, semester_type='FIRST', level=200)
        current_offering_two = CourseOffering.objects.create(course=current_course_two, session=self.session, semester_type='FIRST', level=200)
        current_offering_three = CourseOffering.objects.create(course=current_course_three, session=self.session, semester_type='FIRST', level=200)
        current_offering_four = CourseOffering.objects.create(course=current_course_four, session=self.session, semester_type='FIRST', level=200)
        current_offering_five = CourseOffering.objects.create(course=current_course_five, session=self.session, semester_type='FIRST', level=200)

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': [
                    str(current_offering_one.id),
                    str(current_offering_two.id),
                    str(current_offering_three.id),
                    str(current_offering_four.id),
                    str(current_offering_five.id),
                    str(self.carryover_offering.id),
                ],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 302)
        registration = CourseRegistration.objects.get(student=self.student_profile, session=self.session, semester='FIRST')
        self.assertEqual(registration.total_credit_units, Decimal('19'))

    def test_combined_current_and_carryover_registration_stays_within_23_credit_limit(self):
        current_course_one = Course.objects.create(
            code='CSC260',
            title='Systems Programming',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_two = Course.objects.create(
            code='CSC270',
            title='Artificial Intelligence',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_three = Course.objects.create(
            code='CSC280',
            title='Web Technology',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_course_four = Course.objects.create(
            code='CSC290',
            title='Mobile Computing',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        current_offering_one = CourseOffering.objects.create(course=current_course_one, session=self.session, semester_type='FIRST', level=200)
        current_offering_two = CourseOffering.objects.create(course=current_course_two, session=self.session, semester_type='FIRST', level=200)
        current_offering_three = CourseOffering.objects.create(course=current_course_three, session=self.session, semester_type='FIRST', level=200)
        current_offering_four = CourseOffering.objects.create(course=current_course_four, session=self.session, semester_type='FIRST', level=200)

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': [
                    str(current_offering_one.id),
                    str(current_offering_two.id),
                    str(current_offering_three.id),
                    str(current_offering_four.id),
                    str(self.carryover_offering.id),
                ],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 302)
        registration = CourseRegistration.objects.get(student=self.student_profile, session=self.session, semester='FIRST')
        self.assertEqual(registration.total_credit_units, Decimal('16'))

    def test_registration_rejects_selection_over_23_credit_units(self):
        current_offerings_for_limit = []
        for idx in range(5):
            course = Course.objects.create(
                code=f'CSC{300 + idx}',
                title=f'Current Course {idx}',
                department=self.student_profile.department,
                programme=self.student_profile.programme,
                level=200,
                semester='FIRST',
                credit_units=3,
                is_compulsory=True,
            )
            offering = CourseOffering.objects.create(
                course=course,
                session=self.session,
                semester_type='FIRST',
                level=200,
            )
            current_offerings_for_limit.append(str(offering.id))

        carryover_offerings_for_limit = []
        for idx in range(3):
            carryover_course = Course.objects.create(
                code=f'CSC{500 + idx}',
                title=f'Carryover Course {idx}',
                department=self.student_profile.department,
                programme=self.student_profile.programme,
                level=100,
                semester='FIRST',
                credit_units=4,
                is_compulsory=True,
            )
            carryover_offering = CourseOffering.objects.create(
                course=carryover_course,
                session=self.session,
                semester_type='FIRST',
                level=100,
            )
            carryover_offerings_for_limit.append(str(carryover_offering.id))

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': current_offerings_for_limit + carryover_offerings_for_limit,
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cannot exceed the maximum registration limit of 23.00 credit units')

    def test_400_level_student_can_register_four_regular_courses_plus_project(self):
        self.student_profile.level = 400
        self.student_profile.save()

        regular_offerings = []
        for idx in range(4):
            course = Course.objects.create(
                code=f'CSC{500 + idx}',
                title=f'Level 400 Course {idx}',
                department=self.student_profile.department,
                programme=self.student_profile.programme,
                level=400,
                semester='FIRST',
                credit_units=3,
                is_compulsory=True,
            )
            offering = CourseOffering.objects.create(course=course, session=self.session, semester_type='FIRST', level=400)
            regular_offerings.append(str(offering.id))

        project_course = Course.objects.create(
            code='CSC499',
            title='Final Year Project',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=400,
            semester='FIRST',
            credit_units=6,
            is_compulsory=False,
        )
        project_offering = CourseOffering.objects.create(course=project_course, session=self.session, semester_type='FIRST', level=400)

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': regular_offerings + [str(project_offering.id)],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 302)
        registration = CourseRegistration.objects.get(student=self.student_profile, session=self.session, semester='FIRST')
        self.assertEqual(registration.total_credit_units, Decimal('18'))

    def test_duplicate_course_selection_is_rejected(self):
        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': [str(self.current_offering.id), str(self.current_offering.id)],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Duplicate course selections are not allowed')

    def test_duplicate_registration_for_same_session_and_semester_is_rejected(self):
        CourseRegistration.objects.create(
            student=self.student_profile,
            session=self.session,
            semester='FIRST',
            status='CONFIRMED',
            total_credit_units=Decimal('3'),
        )

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': [str(self.current_offering.id)],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A registration already exists for this session and semester')

    def test_registration_rejects_unavailable_or_ineligible_course_offering(self):
        other_session = AcademicSession.objects.create(name='2026/2027', is_active=False)
        other_course = Course.objects.create(
            code='CSC700',
            title='Unavailable Course',
            department=self.student_profile.department,
            programme=self.student_profile.programme,
            level=200,
            semester='FIRST',
            credit_units=3,
            is_compulsory=True,
        )
        other_offering = CourseOffering.objects.create(course=other_course, session=other_session, semester_type='FIRST', level=200)

        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': [str(other_offering.id)],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not eligible for your current academic profile')

    def test_unauthorized_registration_access_is_denied(self):
        self.client.logout()
        response = self.client.get('/student/registration/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_confirmed_registration_persists_and_is_loaded_on_revisit(self):
        response = self.client.post(
            '/student/registration/',
            {
                'session': str(self.session.id),
                'semester': 'FIRST',
                'course_ids': [str(self.current_offering.id), str(self.carryover_offering.id)],
                'action': 'confirm',
            }
        )

        self.assertEqual(response.status_code, 302)
        registration = CourseRegistration.objects.get(student=self.student_profile, session=self.session, semester='FIRST')
        self.assertEqual(registration.total_credit_units, Decimal('7'))

        revisit = self.client.get('/student/registration/', {'session': str(self.session.id), 'semester': 'FIRST'})
        self.assertEqual(revisit.status_code, 200)
        self.assertContains(revisit, self.current_course.code)
        self.assertContains(revisit, self.carryover_course.code)
