import getpass

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create a management account using an interactive password prompt.'

    def add_arguments(self, parser):
        parser.add_argument('username', help='Username for the new management account.')

    def handle(self, *args, **options):
        username = options['username'].strip()
        if not username:
            raise CommandError('A non-empty username is required.')

        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise CommandError('An account with that username already exists.')

        password = getpass.getpass('Password: ')
        confirmation = getpass.getpass('Confirm password: ')
        if not password or password != confirmation:
            raise CommandError('The passwords are empty or do not match.')

        user = User(username=username)
        try:
            password_validation.validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError('; '.join(error.messages)) from error

        User.objects.create_user(
            username=username,
            password=password,
            is_management=True,
        )
        self.stdout.write(self.style.SUCCESS('Management account created. Password was not displayed.'))
