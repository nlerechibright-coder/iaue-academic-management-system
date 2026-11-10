from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase


class AuthenticationFlowTests(TestCase):
    def test_management_account_command_hashes_password_without_printing_it(self):
        password = 'Tidewood!Cobalt47-Vector'
        output = StringIO()

        with patch(
            'accounts.management.commands.create_management_account.getpass.getpass',
            side_effect=[password, password],
        ):
            call_command('create_management_account', 'provisioned-manager', stdout=output)

        user = get_user_model().objects.get(username='provisioned-manager')
        self.assertTrue(user.is_management)
        self.assertTrue(user.check_password(password))
        self.assertNotIn(password, output.getvalue())

    def test_management_account_command_refuses_existing_users(self):
        get_user_model().objects.create_user(username='existing-user', password='Password123!')

        with self.assertRaises(CommandError):
            call_command('create_management_account', 'existing-user')

    def test_login_page_does_not_disclose_default_management_credentials(self):
        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Default Admin Credentials')
        self.assertNotContains(response, 'Management123!')
        self.assertNotContains(response, 'e.g., management')

    def test_management_login_redirects_to_dashboard(self):
        user = get_user_model().objects.create_user(
            username='management',
            password='Management123!',
            is_management=True,
        )

        response = self.client.post('/login/', {'username': 'management', 'password': 'Management123!'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.pk, user.pk)

    def test_invalid_login_is_rejected(self):
        get_user_model().objects.create_user(
            username='management',
            password='Management123!',
            is_management=True,
        )

        response = self.client.post('/login/', {'username': 'management', 'password': 'wrong-password'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_inactive_user_cannot_log_in(self):
        get_user_model().objects.create_user(
            username='inactive-user',
            password='Password123!',
            is_active=False,
        )

        response = self.client.post('/login/', {'username': 'inactive-user', 'password': 'Password123!'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_unauthenticated_user_cannot_access_dashboard(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
