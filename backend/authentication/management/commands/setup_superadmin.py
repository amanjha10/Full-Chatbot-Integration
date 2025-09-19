from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = 'Set superuser role to SUPERADMIN'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the superuser')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username, is_superuser=True)
            user.role = User.Role.SUPERADMIN
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set {username} role to SUPERADMIN')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Superuser {username} not found')
            )
