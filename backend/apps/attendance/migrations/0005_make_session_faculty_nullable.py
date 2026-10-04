from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0004_attendance_confidence_attendance_marked_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="attendancesession",
            name="faculty",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attendance_sessions",
                to="accounts.faculty",
            ),
        ),
    ]
