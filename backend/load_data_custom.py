import os
import django
from django.core.management import call_command
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

print("Starting to load data...")
sys.stdout.flush()

try:
    call_command("loaddata", "db_dump_utf8.json")
    print("Successfully loaded data.")
except Exception as e:
    print(f"Error loading data: {e}")
