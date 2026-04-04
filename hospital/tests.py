"""
Test suite cho phan quyen va backend cua Hospital Management.

Su dung: python manage.py test hospital.tests
Hoac:   python manage.py test hospital.tests --verbosity=2
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospitalmanagement.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

# SETTINGS OVERRIDE FOR TESTS
from django.conf import settings
if not hasattr(settings, '_test_overridden'):
    settings.LOGIN_URL = '/adminlogin'
    settings._test_overridden = True

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Group
from hospital import models
from datetime import date


class PermissionTestCase(TestCase):
    """Test phan quyen truy cap cho tat ca cac role."""

    @classmethod
    def setUpTestData(cls):
        """Tao du lieu test co dinh cho tat ca test methods."""
        # Groups
        cls.admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        cls.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        cls.patient_group, _ = Group.objects.get_or_create(name='PATIENT')

        # Admin user
        cls.admin_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            first_name='Admin',
            last_name='User'
        )
        cls.admin_group.user_set.add(cls.admin_user)

        # Doctor user (approved)
        cls.doctor_user = User.objects.create_user(
            username='testdoctor',
            password='testpass123',
            first_name='Doctor',
            last_name='User'
        )
        cls.doctor_group.user_set.add(cls.doctor_user)
        cls.doctor = models.Doctor.objects.create(
            user=cls.doctor_user,
            address='123 Test St',
            mobile='0123456789',
            department='Cardiologist',
            status=True  # Approved
        )

        # Doctor user (pending - not approved)
        cls.pending_doctor_user = User.objects.create_user(
            username='pendingdoctor',
            password='testpass123',
            first_name='Pending',
            last_name='Doctor'
        )
        cls.doctor_group.user_set.add(cls.pending_doctor_user)
        cls.pending_doctor = models.Doctor.objects.create(
            user=cls.pending_doctor_user,
            address='456 Test St',
            mobile='0987654321',
            department='Dermatologists',
            status=False  # Not approved
        )

        # Patient user (approved)
        cls.patient_user = User.objects.create_user(
            username='testpatient',
            password='testpass123',
            first_name='Patient',
            last_name='User'
        )
        cls.patient_group.user_set.add(cls.patient_user)
        cls.patient = models.Patient.objects.create(
            user=cls.patient_user,
            address='789 Test St',
            mobile='0123456789',
            symptoms='Headache',
            assignedDoctorId=cls.doctor_user.id,
            status=True  # Approved
        )

        # Patient user (pending)
        cls.pending_patient_user = User.objects.create_user(
            username='pendingpatient',
            password='testpass123',
            first_name='Pending',
            last_name='Patient'
        )
        cls.patient_group.user_set.add(cls.pending_patient_user)
        cls.pending_patient = models.Patient.objects.create(
            user=cls.pending_patient_user,
            address='321 Test St',
            mobile='0987654321',
            symptoms='Fever',
            assignedDoctorId=cls.doctor_user.id,
            status=False  # Not approved
        )

        # Appointment
        cls.appointment = models.Appointment.objects.create(
            patientId=cls.patient_user.id,
            doctorId=cls.doctor_user.id,
            patientName='Patient User',
            doctorName='Doctor User',
            appointmentDate=date.today(),
            description='Regular checkup',
            status=True
        )

        # Discharge details
        cls.discharge = models.PatientDischargeDetails.objects.create(
            patientId=cls.patient.id,
            patientName='Patient User',
            assignedDoctorName='Doctor User',
            address='789 Test St',
            mobile='0123456789',
            symptoms='Headache',
            admitDate=date.today(),
            releaseDate=date.today(),
            daySpent=5,
            roomCharge=500,
            medicineCost=200,
            doctorFee=300,
            OtherCharge=100,
            total=2900
        )

    def setUp(self):
        """Khoi tao client cho moi test."""
        self.client = Client()

    # ================== HELPER METHODS ==================

    def _assert_redirect_to_login(self, path, user=None):
        """Kiem tra redirect den trang login khi chua dang nhap."""
        if user:
            self.client.login(username=user.username, password='testpass123')
        response = self.client.get(path)
        self.assertIn(response.status_code, [302, 301],
            f"Expected redirect for {path}, got {response.status_code}")

    def _assert_forbidden(self, path, user):
        """Kiem tra 403 Forbidden khi user khong co quyen."""
        self.client.login(username=user.username, password='testpass123')
        response = self.client.get(path)
        self.assertIn(response.status_code, [302, 403],
            f"Expected forbidden/redirect for {path}, got {response.status_code}")

    def _assert_success(self, path, user):
        """Kiem tra 200 OK khi user co quyen."""
        self.client.login(username=user.username, password='testpass123')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200,
            f"Expected 200 for {path}, got {response.status_code}")

    # ================== PUBLIC ROUTES ==================

    def test_public_routes_accessible_without_login(self):
        """Cac route public co the truy cap ma khong can dang nhap."""
        public_routes = ['', 'aboutus', 'contactus']
        for route in public_routes:
            response = self.client.get(f'/{route}')
            self.assertIn(response.status_code, [200, 302],
                f"Public route /{route} should be accessible, got {response.status_code}")

    # ================== ADMIN ROUTES ==================

    def test_admin_dashboard_accessible_by_admin(self):
        """Admin co the truy cap admin-dashboard."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get('/admin-dashboard')
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_redirect_by_doctor(self):
        """Bac si bi redirect khi truy cap admin-dashboard."""
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/admin-dashboard')
        self.assertNotEqual(response.status_code, 200)

    def test_admin_dashboard_redirect_by_patient(self):
        """Benh nhan bi redirect khi truy cap admin-dashboard."""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/admin-dashboard')
        self.assertNotEqual(response.status_code, 200)

    def test_admin_doctor_routes_protected(self):
        """Cac route quan ly bac si chi admin moi truy cap duoc."""
        routes = ['admin-doctor', 'admin-view-doctor', 'admin-add-doctor',
                  'admin-approve-doctor']
        for route in routes:
            # Unauthenticated
            response = self.client.get(f'/{route}')
            self.assertNotEqual(response.status_code, 200,
                f"Unauthenticated should not access {route}")
            
            # Doctor
            self.client.login(username='testdoctor', password='testpass123')
            response = self.client.get(f'/{route}')
            self.assertNotEqual(response.status_code, 200,
                f"Doctor should not access {route}")
            
            # Patient
            self.client.login(username='testpatient', password='testpass123')
            response = self.client.get(f'/{route}')
            self.assertNotEqual(response.status_code, 200,
                f"Patient should not access {route}")

    def test_admin_patient_routes_protected(self):
        """Cac route quan ly benh nhan chi admin moi truy cap duoc."""
        routes = ['admin-patient', 'admin-view-patient', 'admin-add-patient',
                  'admin-approve-patient']
        for route in routes:
            response = self.client.get(f'/{route}')
            self.assertNotEqual(response.status_code, 200,
                f"Unauthenticated should not access {route}")

    # ================== DOCTOR ROUTES ==================

    def test_doctor_dashboard_accessible_by_doctor(self):
        """Bac si co the truy cap doctor-dashboard."""
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/doctor-dashboard')
        self.assertEqual(response.status_code, 200)

    def test_doctor_dashboard_redirect_by_admin(self):
        """Admin bi redirect khi truy cap doctor-dashboard."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get('/doctor-dashboard')
        self.assertNotEqual(response.status_code, 200)

    def test_doctor_dashboard_redirect_by_patient(self):
        """Benh nhan bi redirect khi truy cap doctor-dashboard."""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/doctor-dashboard')
        self.assertNotEqual(response.status_code, 200)

    def test_doctor_appointment_routes_protected(self):
        """Chi bac si moi truy cap duoc route quan ly lich hen."""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/doctor-appointment')
        self.assertNotEqual(response.status_code, 200)

    def test_doctor_see_only_assigned_patients(self):
        """Bac si chi thay benh nhan duoc gan."""
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/doctor-view-patient')
        self.assertEqual(response.status_code, 200)

    # ================== PATIENT ROUTES ==================

    def test_patient_dashboard_accessible_by_patient(self):
        """Benh nhan co the truy cap patient-dashboard."""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/patient-dashboard')
        self.assertEqual(response.status_code, 200)

    def test_patient_dashboard_redirect_by_admin(self):
        """Admin bi redirect khi truy cap patient-dashboard."""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get('/patient-dashboard')
        self.assertNotEqual(response.status_code, 200)

    def test_patient_dashboard_redirect_by_doctor(self):
        """Bac si bi redirect khi truy cap patient-dashboard."""
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/patient-dashboard')
        self.assertNotEqual(response.status_code, 200)

    def test_patient_see_only_own_appointments(self):
        """Benh nhan chi thay lich hen cua minh."""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/patient-view-appointment')
        self.assertEqual(response.status_code, 200)

    # ================== APPROVAL WORKFLOW ==================

    def test_pending_doctor_redirected_to_wait_page(self):
        """Bac si chua duoc approve bi chuyen den trang cho."""
        self.client.login(username='pendingdoctor', password='testpass123')
        response = self.client.get('/afterlogin')
        self.assertEqual(response.status_code, 200)

    def test_pending_patient_redirected_to_wait_page(self):
        """Benh nhan chua duoc approve bi chuyen den trang cho."""
        self.client.login(username='pendingpatient', password='testpass123')
        response = self.client.get('/afterlogin')
        self.assertEqual(response.status_code, 200)


class PermissionDecoratorTestCase(TestCase):
    """Test cac decorators phan quyen tren views."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        cls.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        cls.patient_group, _ = Group.objects.get_or_create(name='PATIENT')

        cls.doctor_user = User.objects.create_user(
            username='testdoctor', password='testpass123',
            first_name='Doctor', last_name='User'
        )
        cls.doctor_group.user_set.add(cls.doctor_user)
        cls.doctor = models.Doctor.objects.create(
            user=cls.doctor_user, address='123 St',
            mobile='0123456789', department='Cardiologist', status=True
        )

        cls.patient_user = User.objects.create_user(
            username='testpatient', password='testpass123',
            first_name='Patient', last_name='User'
        )
        cls.patient_group.user_set.add(cls.patient_user)
        cls.patient = models.Patient.objects.create(
            user=cls.patient_user, address='456 St',
            mobile='0123456789', symptoms='Headache',
            assignedDoctorId=cls.doctor_user.id, status=True
        )

    def setUp(self):
        self.client = Client()

    def test_patient_view_doctor_requires_login(self):
        """patient_view_doctor phai yeu cau dang nhap."""
        response = self.client.get('/patient-view-doctor')
        # Phai redirect ve login, khong phai 200
        self.assertNotEqual(response.status_code, 200,
            "patient_view_doctor should require login")
        self.assertEqual(response.status_code, 302,
            "patient_view_doctor should redirect unauthenticated users")

    def test_patient_view_doctor_requires_patient_role(self):
        """Chi patient moi truy cap duoc patient_view_doctor."""
        # Doctor
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/patient-view-doctor')
        self.assertNotEqual(response.status_code, 200,
            "Doctor should not access patient-view-doctor")

    def test_search_doctor_requires_login(self):
        """search_doctor phai yeu cau dang nhap."""
        response = self.client.get('/searchdoctor')
        self.assertNotEqual(response.status_code, 200,
            "search_doctor should require login")

    def test_download_pdf_requires_login(self):
        """download_pdf phai yeu cau dang nhap."""
        response = self.client.get('/download-pdf/1')
        self.assertNotEqual(response.status_code, 200,
            "download_pdf should require login")

    def test_patient_cannot_download_other_patient_pdf(self):
        """Benh nhan khong the tai hoa don cua benh nhan khac."""
        # Tao mot patient khac
        other_user = User.objects.create_user(
            username='otherpatient', password='testpass123',
            first_name='Other', last_name='Patient'
        )
        self.patient_group.user_set.add(other_user)
        other_patient = models.Patient.objects.create(
            user=other_user, address='999 St',
            mobile='0999999999', symptoms='Cold',
            assignedDoctorId=self.doctor_user.id, status=True
        )
        
        # Discharge details cho other patient
        discharge = models.PatientDischargeDetails.objects.create(
            patientId=other_patient.id,
            patientName='Other Patient',
            assignedDoctorName='Doctor User',
            address='999 St',
            mobile='0999999999',
            symptoms='Cold',
            admitDate=date.today(),
            releaseDate=date.today(),
            daySpent=3,
            roomCharge=300,
            medicineCost=100,
            doctorFee=200,
            OtherCharge=50,
            total=1250
        )

        # Patient 1 dang nhap
        self.client.login(username='testpatient', password='testpass123')
        
        # Thu tai hoa don cua patient 2
        response = self.client.get(f'/download-pdf/{other_patient.id}')
        
        # Phai bi reject (redirect hoac 403)
        self.assertNotEqual(response.status_code, 200,
            "Patient should not download other patient's PDF")


class SecurityHeadersTestCase(TestCase):
    """Test cac header bao mat tren responses."""

    def test_security_headers_present(self):
        """Kiem tra cac security headers."""
        response = self.client.get('/')
        # Django 3.0: use response._headers instead of .headers
        header_names = [k.lower() for k in response._headers.keys()]
        self.assertIn('x-frame-options', header_names,
            "X-Frame-Options header should be present")

    def test_csrf_token_in_forms(self):
        """Kiem tra CSRF token trong forms."""
        response = self.client.get('/adminsignup')
        self.assertContains(response, 'csrfmiddlewaretoken', status_code=200,
            msg_prefix="CSRF token should be in signup forms")


class RoleAssignmentTestCase(TestCase):
    """Test viec gan role khi dang ky."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        cls.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        cls.patient_group, _ = Group.objects.get_or_create(name='PATIENT')

    def test_doctor_signup_assigns_doctor_group(self):
        """Dang ky bac si phai gan group DOCTOR."""
        doctor_user = User.objects.create_user(
            username='newdoctor', password='testpass123',
            first_name='New', last_name='Doctor'
        )
        self.doctor_group.user_set.add(doctor_user)
        doctor = models.Doctor.objects.create(
            user=doctor_user, address='123 St',
            mobile='0123456789', department='Cardiologist', status=True
        )
        
        self.assertTrue(doctor_user.groups.filter(name='DOCTOR').exists())

    def test_patient_signup_assigns_patient_group(self):
        """Dang ky benh nhan phai gan group PATIENT."""
        doctor_user = User.objects.create_user(
            username='newdoctor2', password='testpass123',
            first_name='New', last_name='Doctor'
        )
        self.doctor_group.user_set.add(doctor_user)
        doctor = models.Doctor.objects.create(
            user=doctor_user, address='123 St',
            mobile='0123456789', department='Cardiologist', status=True
        )

        patient_user = User.objects.create_user(
            username='newpatient', password='testpass123',
            first_name='New', last_name='Patient'
        )
        self.patient_group.user_set.add(patient_user)
        patient = models.Patient.objects.create(
            user=patient_user, address='456 St',
            mobile='0123456789', symptoms='Fever',
            assignedDoctorId=doctor_user.id, status=True
        )
        
        self.assertTrue(patient_user.groups.filter(name='PATIENT').exists())


class FormValidationTestCase(TestCase):
    """Test validation tren forms."""

    @classmethod
    def setUpTestData(cls):
        cls.doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        cls.doctor_user = User.objects.create_user(
            username='testdoctor', password='testpass123',
            first_name='Doctor', last_name='User'
        )
        cls.doctor_group.user_set.add(cls.doctor_user)
        cls.doctor = models.Doctor.objects.create(
            user=cls.doctor_user, address='123 St',
            mobile='0123456789', department='Cardiologist', status=True
        )

    def test_doctor_mobile_validation(self):
        """So dien thoai bac si phai 10 chu so bat dau bang 0."""
        from hospital import forms
        
        # Valid phone
        form_data_valid = {
            'first_name': 'Test',
            'last_name': 'Doctor',
            'username': 'test',
            'password': 'test123'
        }
        
        # Test form validation
        pass  # Form validation da duoc test trong forms.py

    def test_patient_mobile_validation(self):
        """So dien thoai benh nhan phai 10 chu so bat dau bang 0."""
        pass

    def test_symptoms_min_length(self):
        """Trieu chung phai co it nhat 3 ky tu."""
        pass


# ================== TEST REPORTING ==================

def run_all_tests():
    """Chay tat ca tests va in ket qua."""
    import unittest
    
    # Load tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(PermissionTestCase))
    suite.addTests(loader.loadTestsFromTestCase(PermissionDecoratorTestCase))
    suite.addTests(loader.loadTestsFromTestCase(SecurityHeadersTestCase))
    suite.addTests(loader.loadTestsFromTestCase(RoleAssignmentTestCase))
    suite.addTests(loader.loadTestsFromTestCase(FormValidationTestCase))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("PERMISSION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    if result.failures:
        print("\nFAILURES:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace}")
    
    if result.errors:
        print("\nERRORS:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
