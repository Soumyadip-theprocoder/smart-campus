import os
import django
import sys
from django.core.serializers import deserialize
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def load_data_in_chunks(filename, chunk_size=50):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    
    print("Deserializing JSON...")
    sys.stdout.flush()
    objects = list(deserialize('json', data))
    total = len(objects)
    print(f"Found {total} objects. Starting to save...")
    sys.stdout.flush()

    for i in range(0, total, chunk_size):
        chunk = objects[i:i + chunk_size]
        try:
            with transaction.atomic():
                for obj in chunk:
                    obj.save()
            print(f"Saved {min(i + chunk_size, total)} / {total} objects.")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error saving chunk {i} to {i + chunk_size}: {e}")
            sys.stdout.flush()
            raise

if __name__ == "__main__":
    load_data_in_chunks('db_dump_utf8.json', 50)
