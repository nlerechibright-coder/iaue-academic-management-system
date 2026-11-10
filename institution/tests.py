from django.contrib.auth import get_user_model
from django.test import TestCase


class ManagementDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='management-admin',
            password='Management123!',
            is_management=True,
        )

    def test_management_user_can_access_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Management Overview')
        self.assertContains(response, 'Registered students')

    def test_non_management_user_is_redirected_from_dashboard(self):
        user = get_user_model().objects.create_user(username='plain-user', password='Password123!')
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
