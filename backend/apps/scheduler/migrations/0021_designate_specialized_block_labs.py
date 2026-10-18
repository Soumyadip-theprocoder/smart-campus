from django.db import migrations

def designate_specialized_labs(apps, schema_editor):
    Room = apps.get_model('scheduler', 'Room')

    # Block F - Pharmacy & Pharmaceutical Sciences Block
    pharm_labs = [
        'F-201', 'F-202', 'F-203', 'F-204',
        'F-205', 'F-206', 'F-207', 'F-208',
        'F-301', 'F-302', 'F-303', 'F-304',
    ]
    Room.objects.filter(
        building__icontains='Block F',
        room_number__in=pharm_labs
    ).update(room_type='lab')

    # Block I - Hospitality, Tourism & General Studies Block
    hosp_labs = [
        'I-201', 'I-202', 'I-203', 'I-204', 'I-205', 'I-206'
    ]
    Room.objects.filter(
        building__icontains='Block I',
        room_number__in=hosp_labs
    ).update(room_type='lab')

    # Block H - Humanities & Social Sciences Block (Language & Digital Media Labs)
    hum_labs = [
        'H-201', 'H-202', 'H-203', 'H-204'
    ]
    Room.objects.filter(
        building__icontains='Block H',
        room_number__in=hum_labs
    ).update(room_type='lab')

def rollback_labs(apps, schema_editor):
    Room = apps.get_model('scheduler', 'Room')
    Room.objects.filter(
        building__icontains='Block F',
        room_number__in=[
            'F-201', 'F-202', 'F-203', 'F-204',
            'F-205', 'F-206', 'F-207', 'F-208',
            'F-301', 'F-302', 'F-303', 'F-304',
        ]
    ).update(room_type='lecture')


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0020_rebalance_faculty_workload'),
    ]

    operations = [
        migrations.RunPython(designate_specialized_labs, rollback_labs),
    ]
