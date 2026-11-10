from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from institution.models import Department, Faculty, Programme
from students.models import StudentProfile


class StudentDashboardAccessTests(TestCase):
    def setUp(self):
        faculty = Faculty.objects.create(name='Science', code='SCI')
        department = Department.objects.create(name='Computer Science', code='CSC', faculty=faculty)
        programme = Programme.objects.create(
            name='BSc Computer Science',
            code='BCS',
            department=department,
            max_level=400,
        )
        self.user = get_user_model().objects.create_user(
            username='student-dashboard',
            password='StudentPass123!',
        )
        StudentProfile.objects.create(
            user=self.user,
            matric_number='U/2024/00010',
            department=department,
            programme=programme,
            level=200,
        )

    def test_student_dashboard_renders_student_navigation_only(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('students:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'U/2024/00010')
        self.assertContains(response, reverse('registration:dashboard'))
        self.assertNotContains(response, reverse('institution:faculty_list'))

    def test_student_cannot_access_management_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
