from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from reconciler.services.importer import import_all


class Command(BaseCommand):
    help = "Import locations.csv, system_a.csv and system_b.csv."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-clear",
            action="store_true",
            help="Do not clear existing imported records first.",
        )

    def handle(self, *args, **options):
        try:
            result = import_all(
                settings.DATA_DIR,
                clear_existing=not options["no_clear"],
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Import completed successfully."
            )
        )

        self.stdout.write(
            f"Locations: {result['locations']}"
        )
        self.stdout.write(
            f"System A records: {result['system_a']}"
        )
        self.stdout.write(
            f"System B entries: {result['system_b']}"
        )
        self.stdout.write(
            f"Import issues: {result['issues']}"
        )
