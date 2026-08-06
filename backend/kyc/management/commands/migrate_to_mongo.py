"""Load a dumpdata JSON backup (from the old Postgres/SQLite DB) into MongoDB.

Usage:
    python manage.py migrate_to_mongo backup_pre_mongo.json
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load a dumpdata JSON fixture into the configured MongoDB database."

    def add_arguments(self, parser):
        parser.add_argument("fixture", help="Path to dumpdata JSON file")

    def handle(self, *args, **options):
        fixture = options["fixture"]
        self.stdout.write(f"Loading {fixture} into MongoDB...")
        call_command("loaddata", fixture, verbosity=1)
        self.stdout.write(self.style.SUCCESS("Data loaded."))
