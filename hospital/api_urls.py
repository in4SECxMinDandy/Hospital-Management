"""
Hospital Management - API URL Configuration
==========================================
URL patterns cho Django REST API
"""

from django.urls import path
from . import api

urlpatterns = [
    # ========== AUTH ENDPOINTS ==========
    path('auth/login/', api.LoginAPIView.as_view(), name='api-login'),
    path('auth/logout/', api.LogoutAPIView.as_view(), name='api-logout'),
    
    # ========== ADMIN ENDPOINTS ==========
    # Dashboard
    path('admin/dashboard/', api.AdminDashboardAPIView.as_view(), name='api-admin-dashboard'),
    
    # Doctors
    path('admin/doctors/', api.AdminDoctorListAPIView.as_view(), name='api-admin-doctors'),
    path('admin/doctors/<int:pk>/', api.AdminDoctorDetailAPIView.as_view(), name='api-admin-doctor-detail'),
    path('admin/doctors/<int:pk>/approve/', api.AdminApproveDoctorAPIView.as_view(), name='api-approve-doctor'),
    
    # Patients
    path('admin/patients/', api.AdminPatientListAPIView.as_view(), name='api-admin-patients'),
    path('admin/patients/<int:pk>/', api.AdminPatientDetailAPIView.as_view(), name='api-admin-patient-detail'),
    path('admin/patients/<int:pk>/approve/', api.AdminApprovePatientAPIView.as_view(), name='api-approve-patient'),
    
    # Appointments
    path('admin/appointments/', api.AdminAppointmentListAPIView.as_view(), name='api-admin-appointments'),
    path('admin/appointments/<int:pk>/', api.AdminAppointmentDetailAPIView.as_view(), name='api-admin-appointment-detail'),
    path('admin/appointments/<int:pk>/approve/', api.AdminApproveAppointmentAPIView.as_view(), name='api-approve-appointment'),
    
    # Discharge
    path('admin/discharge/', api.AdminDischargeAPIView.as_view(), name='api-admin-discharge'),
    path('admin/discharge/<int:pk>/', api.AdminDischargeAPIView.as_view(), name='api-admin-discharge-patient'),
    
    # ========== DOCTOR ENDPOINTS ==========
    path('doctor/dashboard/', api.DoctorDashboardAPIView.as_view(), name='api-doctor-dashboard'),
    path('doctor/patients/', api.DoctorPatientsAPIView.as_view(), name='api-doctor-patients'),
    
    # ========== PATIENT ENDPOINTS ==========
    path('patient/dashboard/', api.PatientDashboardAPIView.as_view(), name='api-patient-dashboard'),
    path('patient/profile/', api.PatientProfileAPIView.as_view(), name='api-patient-profile'),
    path('patient/doctors/', api.PatientDoctorsAPIView.as_view(), name='api-patient-doctors'),
    path('patient/book-appointment/', api.PatientBookAppointmentAPIView.as_view(), name='api-patient-book-appointment'),
]
