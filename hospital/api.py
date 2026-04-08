"""
Hospital Management - Django REST API Views
==========================================
API endpoints cho frontend va client tich hop
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.db.models import Q
from datetime import date

from . import models, serializers


def make_response(success: bool, data=None, message: str = None, **kwargs):
    """Tạo response chuẩn."""
    response_data = {"success": success}
    if data is not None:
        response_data["data"] = data
    if message:
        response_data["message"] = message
    response_data.update(kwargs)
    return Response(response_data)


# ========== AUTH VIEWS ==========

class LoginAPIView(APIView):
    """API đăng nhập."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": "Dữ liệu không hợp lệ",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        role = serializer.validated_data['role']
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return make_response(False, message="Tên đăng nhập hoặc mật khẩu không đúng")
        
        # Check role
        if role == 'admin' and not user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Bạn không có quyền Admin")
        elif role == 'doctor' and not user.groups.filter(name='DOCTOR').exists():
            return make_response(False, message="Bạn không có quyền Doctor")
        elif role == 'patient' and not user.groups.filter(name='PATIENT').exists():
            return make_response(False, message="Bạn không có quyền Patient")
        
        # Get token (simple token - in production use JWT)
        token = f"token_{user.id}_{user.username}"
        
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        
        return make_response(True, data={
            "user_id": user.id,
            "username": user.username,
            "full_name": full_name,
            "role": role,
            "token": token
        }, message="Đăng nhập thành công!")


class LogoutAPIView(APIView):
    """API đăng xuất."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return make_response(True, message="Đăng xuất thành công!")


# ========== ADMIN VIEWS ==========

class AdminDashboardAPIView(APIView):
    """API dashboard admin."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        doctor_count = models.Doctor.objects.filter(status=True).count()
        pending_doctors = models.Doctor.objects.filter(status=False).count()
        patient_count = models.Patient.objects.filter(status=True).count()
        pending_patients = models.Patient.objects.filter(status=False).count()
        appointment_count = models.Appointment.objects.filter(status=True).count()
        pending_appointments = models.Appointment.objects.filter(status=False).count()
        
        return make_response(True, data={
            "doctor_count": doctor_count,
            "pending_doctors": pending_doctors,
            "patient_count": patient_count,
            "pending_patients": pending_patients,
            "appointment_count": appointment_count,
            "pending_appointments": pending_appointments
        })


class AdminDoctorListAPIView(APIView):
    """API list/create doctors."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        status_filter = request.query_params.get('status')
        
        if status_filter == 'true':
            doctors = models.Doctor.objects.filter(status=True).select_related('user')
        elif status_filter == 'false':
            doctors = models.Doctor.objects.filter(status=False).select_related('user')
        else:
            doctors = models.Doctor.objects.select_related('user').all()
        
        data = [{
            "id": d.id,
            "name": d.get_name,
            "department": d.department,
            "mobile": d.mobile,
            "address": d.address,
            "email": d.user.email,
            "status": d.status,
            "profile_pic": d.profile_pic.url if d.profile_pic else None
        } for d in doctors]
        
        return make_response(True, data=data)
    
    def post(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        serializer = serializers.DoctorRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return make_response(False, error="Dữ liệu không hợp lệ", details=serializer.errors)
        
        data = serializer.validated_data
        
        # Create user
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data.get('last_name', '')
        )
        
        # Create doctor
        doctor = models.Doctor.objects.create(
            user=user,
            address=data.get('address', ''),
            mobile=data['mobile'],
            department=data['department'],
            status=True,  # Admin-created = auto approved
            profile_pic=data.get('profile_pic')
        )
        
        # Add to DOCTOR group
        doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
        doctor_group.user_set.add(user)
        
        return make_response(True, data={"id": doctor.id}, message="Tạo bác sĩ thành công!")


class AdminDoctorDetailAPIView(APIView):
    """API doctor detail/update/delete."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            doctor = models.Doctor.objects.select_related('user').get(id=pk)
        except models.Doctor.DoesNotExist:
            return make_response(False, message="Không tìm thấy bác sĩ")
        
        return make_response(True, data={
            "id": doctor.id,
            "name": doctor.get_name,
            "department": doctor.department,
            "mobile": doctor.mobile,
            "address": doctor.address,
            "email": doctor.user.email,
            "status": doctor.status
        })
    
    def put(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            doctor = models.Doctor.objects.get(id=pk)
        except models.Doctor.DoesNotExist:
            return make_response(False, message="Không tìm thấy bác sĩ")
        
        # Update fields
        doctor.address = request.data.get('address', doctor.address)
        doctor.mobile = request.data.get('mobile', doctor.mobile)
        doctor.department = request.data.get('department', doctor.department)
        doctor.save()
        
        return make_response(True, message="Cập nhật thành công!")
    
    def delete(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            doctor = models.Doctor.objects.get(id=pk)
            user = doctor.user
            doctor.delete()
            user.delete()
            return make_response(True, message="Xóa bác sĩ thành công!")
        except models.Doctor.DoesNotExist:
            return make_response(False, message="Không tìm thấy bác sĩ")


class AdminApproveDoctorAPIView(APIView):
    """API approve doctor."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            doctor = models.Doctor.objects.get(id=pk)
            doctor.status = True
            doctor.save()
            return make_response(True, message="Duyệt bác sĩ thành công!")
        except models.Doctor.DoesNotExist:
            return make_response(False, message="Không tìm thấy bác sĩ")


# ========== SIMILAR PATTERN FOR PATIENTS, APPOINTMENTS, DISCHARGE ==========
# (Abbreviated for brevity - same pattern as doctors)

class AdminPatientListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        status_filter = request.query_params.get('status')
        
        if status_filter == 'true':
            patients = models.Patient.objects.filter(status=True).select_related('user')
        elif status_filter == 'false':
            patients = models.Patient.objects.filter(status=False).select_related('user')
        else:
            patients = models.Patient.objects.select_related('user').all()
        
        data = [{
            "id": p.id,
            "name": p.get_name,
            "symptoms": p.symptoms,
            "mobile": p.mobile,
            "address": p.address,
            "admit_date": p.admitDate,
            "assigned_doctor": self._get_doctor_name(p.assignedDoctorId),
            "status": p.status
        } for p in patients]
        
        return make_response(True, data=data)
    
    def _get_doctor_name(self, doctor_id):
        if doctor_id:
            try:
                user = User.objects.get(id=doctor_id)
                doctor = models.Doctor.objects.get(user=user)
                return doctor.get_name
            except:
                return "Chưa phân công"
        return "Chưa phân công"
    
    def post(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        serializer = serializers.PatientRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return make_response(False, error="Dữ liệu không hợp lệ", details=serializer.errors)
        
        data = serializer.validated_data
        
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data.get('last_name', '')
        )
        
        patient = models.Patient.objects.create(
            user=user,
            address=data.get('address', ''),
            mobile=data['mobile'],
            symptoms=data['symptoms'],
            assignedDoctorId=request.data.get('assignedDoctorId'),
            status=True
        )
        
        patient_group, _ = Group.objects.get_or_create(name='PATIENT')
        patient_group.user_set.add(user)
        
        return make_response(True, data={"id": patient.id}, message="Tạo bệnh nhân thành công!")


class AdminPatientDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.select_related('user').get(id=pk)
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy bệnh nhân")
        
        return make_response(True, data={
            "id": patient.id,
            "name": patient.get_name,
            "symptoms": patient.symptoms,
            "mobile": patient.mobile,
            "address": patient.address,
            "admit_date": patient.admitDate,
            "status": patient.status
        })
    
    def put(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.get(id=pk)
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy bệnh nhân")
        
        patient.address = request.data.get('address', patient.address)
        patient.mobile = request.data.get('mobile', patient.mobile)
        patient.symptoms = request.data.get('symptoms', patient.symptoms)
        patient.assignedDoctorId = request.data.get('assignedDoctorId', patient.assignedDoctorId)
        patient.save()
        
        return make_response(True, message="Cập nhật thành công!")
    
    def delete(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.get(id=pk)
            user = patient.user
            patient.delete()
            user.delete()
            return make_response(True, message="Xóa bệnh nhân thành công!")
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy bệnh nhân")


class AdminApprovePatientAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.get(id=pk)
            patient.status = True
            patient.save()
            return make_response(True, message="Duyệt bệnh nhân thành công!")
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy bệnh nhân")


# ========== APPOINTMENT VIEWS ==========

class AdminAppointmentListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        status_filter = request.query_params.get('status')
        
        if status_filter == 'true':
            appointments = models.Appointment.objects.filter(status=True)
        elif status_filter == 'false':
            appointments = models.Appointment.objects.filter(status=False)
        else:
            appointments = models.Appointment.objects.all()
        
        data = [{
            "id": a.id,
            "patient_name": a.patientName or "N/A",
            "doctor_name": a.doctorName or "N/A",
            "date": a.appointmentDate,
            "time": a.appointmentTime,
            "description": a.description,
            "status": a.status
        } for a in appointments]
        
        return make_response(True, data=data)
    
    def post(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        appointment = models.Appointment.objects.create(
            patientId=request.data.get('patient_id'),
            doctorId=request.data.get('doctor_id'),
            patientName=request.data.get('patient_name', ''),
            doctorName=request.data.get('doctor_name', ''),
            appointmentDate=request.data.get('date'),
            appointmentTime=request.data.get('time'),
            description=request.data.get('description', ''),
            status=request.data.get('status', True)
        )
        
        return make_response(True, data={"id": appointment.id}, message="Tạo lịch hẹn thành công!")


class AdminAppointmentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            appointment = models.Appointment.objects.get(id=pk)
            appointment.delete()
            return make_response(True, message="Xóa lịch hẹn thành công!")
        except models.Appointment.DoesNotExist:
            return make_response(False, message="Không tìm thấy lịch hẹn")


class AdminApproveAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            appointment = models.Appointment.objects.get(id=pk)
            appointment.status = True
            appointment.save()
            return make_response(True, message="Duyệt lịch hẹn thành công!")
        except models.Appointment.DoesNotExist:
            return make_response(False, message="Không tìm thấy lịch hẹn")


# ========== DISCHARGE VIEWS ==========

class AdminDischargeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        # Get admitted patients
        patients = models.Patient.objects.filter(status=True).select_related('user')
        
        data = [{
            "id": p.id,
            "name": p.get_name,
            "symptoms": p.symptoms,
            "admit_date": p.admitDate,
            "assigned_doctor": self._get_doctor_name(p.assignedDoctorId)
        } for p in patients]
        
        return make_response(True, data=data)
    
    def _get_doctor_name(self, doctor_id):
        if doctor_id:
            try:
                user = User.objects.get(id=doctor_id)
                doctor = models.Doctor.objects.get(user=user)
                return doctor.get_name
            except:
                return "Chưa phân công"
        return "Chưa phân công"
    
    def post(self, request, pk):
        if not request.user.groups.filter(name='ADMIN').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.get(id=pk)
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy bệnh nhân")
        
        serializer = serializers.DischargeSerializer(data=request.data)
        if not serializer.is_valid():
            return make_response(False, error="Dữ liệu không hợp lệ", details=serializer.errors)
        
        data = serializer.validated_data
        
        # Get doctor name
        doctor_name = "Chưa phân công"
        if patient.assignedDoctorId:
            try:
                user = User.objects.get(id=patient.assignedDoctorId)
                doctor_name = f"{user.first_name} {user.last_name}".strip()
            except:
                pass
        
        # Calculate days
        days_spent = (date.today() - patient.admitDate).days
        days_spent = max(1, days_spent)
        
        discharge = models.PatientDischargeDetails.objects.create(
            patientId=pk,
            patientName=patient.get_name,
            assignedDoctorName=doctor_name,
            address=patient.address,
            mobile=patient.mobile,
            symptoms=patient.symptoms,
            admitDate=patient.admitDate,
            releaseDate=date.today(),
            daySpent=days_spent,
            roomCharge=data['room_charge'] * days_spent,
            medicineCost=data['medicine_cost'],
            doctorFee=data['doctor_fee'],
            OtherCharge=data['other_charge'],
            total=data['total']
        )
        
        return make_response(True, data={"id": discharge.id}, message="Xuất viện thành công!")
    
    def _get_doctor_name(self, doctor_id):
        if doctor_id:
            try:
                user = User.objects.get(id=doctor_id)
                doctor = models.Doctor.objects.get(user=user)
                return doctor.get_name
            except:
                return "Chưa phân công"
        return "Chưa phân công"


# ========== DOCTOR VIEWS ==========

class DoctorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='DOCTOR').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            doctor = models.Doctor.objects.get(user=request.user)
        except models.Doctor.DoesNotExist:
            return make_response(False, message="Không tìm thấy hồ sơ bác sĩ")
        
        patients = models.Patient.objects.filter(
            status=True, assignedDoctorId=request.user.id
        )
        
        appointments = models.Appointment.objects.filter(doctorId=request.user.id)
        
        return make_response(True, data={
            "patient_count": patients.count(),
            "appointment_count": appointments.count(),
            "completed_count": appointments.filter(status=True).count()
        })


class DoctorPatientsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='DOCTOR').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        patients = models.Patient.objects.filter(
            status=True, assignedDoctorId=request.user.id
        )
        
        data = [{
            "id": p.id,
            "name": p.get_name,
            "symptoms": p.symptoms,
            "mobile": p.mobile,
            "admit_date": p.admitDate
        } for p in patients]
        
        return make_response(True, data=data)


# ========== PATIENT VIEWS ==========

class PatientDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='PATIENT').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.get(user=request.user)
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy hồ sơ bệnh nhân")
        
        appointments = models.Appointment.objects.filter(patientId=request.user.id)
        
        return make_response(True, data={
            "appointment_count": appointments.count(),
            "completed_count": appointments.filter(status=True).count(),
            "status": "active" if patient.status else "inactive"
        })


class PatientProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_patient(self, request):
        if not request.user.groups.filter(name='PATIENT').exists():
            return None, make_response(False, message="KhÃ´ng cÃ³ quyá»n truy cáº­p")

        try:
            patient = models.Patient.objects.select_related('user').get(user=request.user)
        except models.Patient.DoesNotExist:
            return None, make_response(False, message="KhÃ´ng tÃ¬m tháº¥y há»“ sÆ¡ bá»‡nh nhÃ¢n")

        return patient, None

    def get(self, request):
        patient, error_response = self.get_patient(request)
        if error_response:
            return error_response

        serializer = serializers.PatientProfileSerializer(patient)
        return make_response(True, data=serializer.data)

    def put(self, request):
        patient, error_response = self.get_patient(request)
        if error_response:
            return error_response

        serializer = serializers.PatientProfileSerializer(
            patient,
            data=request.data,
            partial=True
        )
        if not serializer.is_valid():
            return make_response(False, error="Dá»¯ liá»‡u khÃ´ng há»£p lá»‡", details=serializer.errors)

        serializer.save()
        return make_response(True, data=serializer.data, message="Cáº­p nháº­t há»“ sÆ¡ thÃ nh cÃ´ng!")


class PatientDoctorsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='PATIENT').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        doctors = models.Doctor.objects.filter(status=True)
        
        data = [{
            "id": d.id,
            "name": d.get_name,
            "department": d.department,
            "mobile": d.mobile
        } for d in doctors]
        
        return make_response(True, data=data)


class PatientBookAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.groups.filter(name='PATIENT').exists():
            return make_response(False, message="Không có quyền truy cập")
        
        try:
            patient = models.Patient.objects.get(user=request.user)
        except models.Patient.DoesNotExist:
            return make_response(False, message="Không tìm thấy hồ sơ bệnh nhân")
        
        doctor_id = request.data.get('doctor_id')
        
        try:
            doctor = models.Doctor.objects.get(id=doctor_id)
        except models.Doctor.DoesNotExist:
            return make_response(False, message="Không tìm thấy bác sĩ")
        
        appointment = models.Appointment.objects.create(
            patientId=request.user.id,
            doctorId=doctor.user.id,
            patientName=patient.get_name,
            doctorName=doctor.get_name,
            appointmentDate=request.data.get('date'),
            appointmentTime=request.data.get('time'),
            description=request.data.get('description', ''),
            status=False  # Need approval
        )
        
        return make_response(True, data={"id": appointment.id}, message="Đặt lịch hẹn thành công!")
