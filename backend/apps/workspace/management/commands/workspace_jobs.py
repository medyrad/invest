import time

from django.core.management.base import BaseCommand

from apps.workspace.files import check_one, purge


class Command(BaseCommand):
    help = "Process bounded private-file checks and scheduled D30 cleanup."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        last_purge = 0
        while True:
            checked = check_one()
            if options["once"] or time.monotonic() - last_purge >= 60:
                n = purge()
                last_purge = time.monotonic()
                self.stdout.write(f"workspace_jobs checked={int(checked)} purged={n}")
            if options["once"]:
                break
            if not checked:
                time.sleep(5)
