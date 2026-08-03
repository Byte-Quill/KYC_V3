"""Migrate data from the local SQLite database to Postgres (Supabase).

Usage:
    # 1. Make sure DATABASE_URL points at your Supabase Postgres instance.
    # 2. Run migrations against Postgres first:
    #        python manage.py migrate
    # 3. Then run this command with the SQLite file as the source:
    #        python manage.py migrate_to_postgres --sqlite db.sqlite3

It dumps every model from the SQLite database and loads it into the configured
(default) database, preserving primary keys so relations stay intact.
"""
from pathlib import Path

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Copy all data from a SQLite file into the configured (Postgres) database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sqlite",
            default="db.sqlite3",
            help="Path to the source SQLite database file (default: db.sqlite3)",
        )

    def handle(self, *args, **options):
        sqlite_path = Path(options["sqlite"])
        if not sqlite_path.exists():
            raise CommandError(f"SQLite file not found: {sqlite_path}")

        # Register a temporary SQLite connection pointing at the source file.
        from django.conf import settings
        from django.db import connections

        settings.DATABASES["sqlite_source"] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(sqlite_path),
        }
        connections.databases["sqlite_source"] = settings.DATABASES["sqlite_source"]

        from django.apps import apps

        total = 0
        for model in apps.get_models():
            objects = list(model.objects.using("sqlite_source").all())
            if not objects:
                continue
            data = serializers.serialize("json", objects)
            # loaddata-style deserialize into the default (Postgres) connection
            for obj in serializers.deserialize("json", data):
                obj.save(using="default")
            total += len(objects)
            self.stdout.write(f"  {model._meta.label}: {len(objects)} rows")

        self.stdout.write(self.style.SUCCESS(f"Migrated {total} rows to Postgres."))
