#!/usr/bin/env python3
"""
Django management command to create test users for E2E testing.
Run: python manage.py create_test_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hospital.models import Doctor, Patient


class Command(BaseCommand):
    help = 'Create test users for E2E testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users...')

        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        patient_group, _ = Group.objects.get_or_create(name='PATIENT')

        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            admin_group.user_set.add(admin_user)
            self.stdout.write(self.style.SUCCESS('Created admin user: admin/admin123'))
        else:
            self.stdout.write(f'Admin user already exists: admin')

        # Create doctor user
        doctor_user, created = User.objects.get_or_create(
            username='doctor',
            defaults={
                'first_name': 'Test',
                'last_name': 'Doctor',
            }
        )
        if created:
            doctor_user.set_password('doctor123')
            doctor_user.save()
            doctor_group.user_set.add(doctor_user)
            doctor, _ = Doctor.objects.get_or_create(
                user=doctor_user,
                defaults={
                    'address': '123 Test St',
                    'mobile': '0123456789',
                    'department': 'Cardiologist',
                    'status': True,
                }
            )
            self.stdout.write(self.style.SUCCESS('Created doctor user: doctor/doctor123'))
        else:
            self.stdout.write(f'Doctor user already exists: doctor')

        # Create patient user
        patient_user, created = User.objects.get_or_create(
            username='patient',
            defaults={
                'first_name': 'Test',
                'last_name': 'Patient',
            }
        )
        if created:
            patient_user.set_password('patient123')
            patient_user.save()
            patient_group.user_set.add(patient_user)
            patient, _ = Patient.objects.get_or_create(
                user=patient_user,
                defaults={
                    'address': '456 Test St',
                    'mobile': '0987654321',
                    'symptoms': 'Headache',
                    'assignedDoctorId': doctor_user.id,
                    'status': True,
                }
            )
            self.stdout.write(self.style.SUCCESS('Created patient user: patient/patient123'))
        else:
            self.stdout.write(f'Patient user already exists: patient')

        self.stdout.write(self.style.SUCCESS('Test users created successfully!'))
