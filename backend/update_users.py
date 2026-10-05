from django.contrib.auth import get_user_model

User = get_user_model()
updated = 0
for u in User.objects.all():
    if u.username != u.email:
        u.username = u.email
        u.save()
        updated += 1

print(f"Successfully updated {updated} user usernames to match their email addresses.")
