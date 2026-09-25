from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"

    def ready(self):
        try:
            from django_q.models import Schedule
            # Create a daily schedule for flagging attendance shortages if it doesn't exist
            Schedule.objects.get_or_create(
                func="apps.analytics.tasks.flag_attendance_shortages",
                defaults={
                    "schedule_type": Schedule.DAILY,
                    "repeats": -1,
                }
            )
        except Exception:
            # Tables might not be created yet during migrations
            pass
