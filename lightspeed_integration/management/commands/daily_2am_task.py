from django.core.management.base import BaseCommand
from tasks import daily_2am_task

class Command(BaseCommand):
    help = "Runs daily task at 2 AM"

    def handle(self, *args, **kwargs):
        daily_2am_task()
        self.stdout.write(self.style.SUCCESS('Successfully executed daily 2 AM task'))
        