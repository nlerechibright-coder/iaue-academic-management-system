from django.contrib.auth import get_user_model
from django.test import TestCase


class AuditAccessTests(TestCase):
    def test_management_user_can_access_audit_log(self):
        user = get_user_model().objects.create_user(
            username='audit-admin',
            password='Password123!',
            is_management=True,
        )
        self.client.force_login(user)
        response = self.client.get('/management/audit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'System activity log')

    def test_non_management_user_is_blocked_from_audit_log(self):
        user = get_user_model().objects.create_user(username='audit-user', password='Password123!')
        self.client.force_login(user)
        response = self.client.get('/management/audit/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
