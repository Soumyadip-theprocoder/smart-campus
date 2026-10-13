import os
import django
from django.db.models import Count, Min

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Student, Faculty
from django.contrib.auth import get_user_model

User = get_user_model()

def clean_duplicates(model_class, prefix):
    # Find duplicate (first_name, last_name) pairs
    duplicates = model_class.objects.values(
        'user__first_name', 'user__last_name'
    ).annotate(
        c=Count('id'),
        min_id=Min('id')
    ).filter(c__gt=1)
    
    total_deleted = 0
    
    for dup in duplicates:
        first_name = dup['user__first_name']
        last_name = dup['user__last_name']
        min_id = dup['min_id']
        
        # Get all records for this name EXCEPT the one with min_id
        to_delete = model_class.objects.filter(
            user__first_name=first_name,
            user__last_name=last_name
        ).exclude(id=min_id)
        
        # We need to delete the Users associated with these profiles
        user_ids = list(to_delete.values_list('user_id', flat=True))
        
        if user_ids:
            # Delete Users (this will cascade and delete the profiles)
            deleted_count, _ = User.objects.filter(id__in=user_ids).delete()
            total_deleted += deleted_count
            print(f"Deleted {len(user_ids)} duplicate(s) for {first_name} {last_name}")

    print(f"Total {prefix} users deleted: {total_deleted}")

if __name__ == "__main__":
    print("Cleaning duplicate students...")
    clean_duplicates(Student, "Student")
    
    print("Cleaning duplicate faculty...")
    clean_duplicates(Faculty, "Faculty")
    
    print("Done.")
