# Generated manually to align Doctor model state with the existing SQLite schema.

from django.db import migrations, models


def sync_doctor_schema(apps, schema_editor):
    table_name = 'hospital_doctor'
    expected_columns = {
        'basic_schedule': "ALTER TABLE hospital_doctor ADD COLUMN basic_schedule varchar(255) NOT NULL DEFAULT ''",
        'consultation_fee': "ALTER TABLE hospital_doctor ADD COLUMN consultation_fee integer unsigned NULL DEFAULT 0",
        'degree_certificate': "ALTER TABLE hospital_doctor ADD COLUMN degree_certificate text NOT NULL DEFAULT ''",
        'rating_avg': "ALTER TABLE hospital_doctor ADD COLUMN rating_avg real NULL DEFAULT 0",
        'years_experience': "ALTER TABLE hospital_doctor ADD COLUMN years_experience smallint unsigned NULL DEFAULT 0",
    }

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        for column_name, sql in expected_columns.items():
            if column_name not in existing_columns:
                cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0020_appointment_appointmenttime'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(sync_doctor_schema, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='doctor',
                    name='basic_schedule',
                    field=models.CharField(blank=True, default='', max_length=255),
                ),
                migrations.AddField(
                    model_name='doctor',
                    name='consultation_fee',
                    field=models.PositiveIntegerField(blank=True, default=0, null=True),
                ),
                migrations.AddField(
                    model_name='doctor',
                    name='degree_certificate',
                    field=models.TextField(blank=True, default=''),
                ),
                migrations.AddField(
                    model_name='doctor',
                    name='rating_avg',
                    field=models.FloatField(blank=True, default=0, null=True),
                ),
                migrations.AddField(
                    model_name='doctor',
                    name='years_experience',
                    field=models.PositiveSmallIntegerField(blank=True, default=0, null=True),
                ),
            ],
        ),
    ]
