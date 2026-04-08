from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0021_sync_doctor_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='treatment_status',
            field=models.CharField(
                choices=[
                    ('under_treatment', 'Đang điều trị'),
                    ('treated', 'Đã điều trị'),
                ],
                default='under_treatment',
                max_length=20,
            ),
        ),
    ]
