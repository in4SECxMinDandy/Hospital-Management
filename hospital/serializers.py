"""
Hospital Management - Django REST API Serializers
=================================================
Serializers cho Django REST Framework
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from . import models


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer cho Doctor model."""
    user = UserSerializer(read_only=True)
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Doctor
        fields = [
            'id', 'user', 'name', 'profile_pic', 'address',
            'mobile', 'department', 'status'
        ]
        read_only_fields = ['id']
    
    def get_name(self, obj):
        return obj.get_name


class PatientSerializer(serializers.ModelSerializer):
    """Serializer cho Patient model."""
    user = UserSerializer(read_only=True)
    name = serializers.SerializerMethodField()
    assigned_doctor = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Patient
        fields = [
            'id', 'user', 'name', 'profile_pic', 'address',
            'mobile', 'symptoms', 'assignedDoctorId', 'assigned_doctor',
            'admitDate', 'status'
        ]
        read_only_fields = ['id']
    
    def get_name(self, obj):
        return obj.get_name
    
    def get_assigned_doctor(self, obj):
        if obj.assignedDoctorId:
            try:
                user = User.objects.get(id=obj.assignedDoctorId)
                doctor = models.Doctor.objects.get(user=user)
                return doctor.get_name
            except (User.DoesNotExist, models.Doctor.DoesNotExist):
                return "Chưa phân công"
        return "Chưa phân công"


class PatientProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    name = serializers.SerializerMethodField(read_only=True)
    assigned_doctor = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Patient
        fields = [
            'id', 'first_name', 'last_name', 'name', 'profile_pic', 'address',
            'mobile', 'symptoms', 'assignedDoctorId', 'assigned_doctor',
            'admitDate', 'status'
        ]
        read_only_fields = ['id', 'assignedDoctorId', 'admitDate', 'status']

    def get_name(self, obj):
        return obj.get_name

    def get_assigned_doctor(self, obj):
        if obj.assignedDoctorId:
            try:
                doctor = models.Doctor.objects.select_related('user').get(user_id=obj.assignedDoctorId)
                return {
                    'id': doctor.id,
                    'name': doctor.get_name,
                    'department': doctor.department,
                    'mobile': doctor.mobile,
                    'address': doctor.address,
                }
            except models.Doctor.DoesNotExist:
                return None
        return None

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()

        return super().update(instance, validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer cho Appointment model."""
    patient_name = serializers.CharField(required=False)
    doctor_name = serializers.CharField(required=False)
    
    class Meta:
        model = models.Appointment
        fields = [
            'id', 'patientId', 'doctorId', 'patientName',
            'doctorName', 'appointmentDate', 'appointmentTime', 'description', 'status'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        return models.Appointment.objects.create(**validated_data)


class PatientDischargeDetailsSerializer(serializers.ModelSerializer):
    """Serializer cho PatientDischargeDetails model."""
    
    class Meta:
        model = models.PatientDischargeDetails
        fields = [
            'id', 'patientId', 'patientName', 'assignedDoctorName',
            'address', 'mobile', 'symptoms', 'admitDate', 'releaseDate',
            'daySpent', 'roomCharge', 'medicineCost', 'doctorFee',
            'OtherCharge', 'total'
        ]
        read_only_fields = ['id']


class LoginSerializer(serializers.Serializer):
    """Serializer cho login request."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    role = serializers.ChoiceField(
        choices=['admin', 'doctor', 'patient'],
        required=True
    )


class DoctorRegistrationSerializer(serializers.Serializer):
    """Serializer cho doctor registration."""
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    department = serializers.ChoiceField(choices=models.departments, required=True)
    mobile = serializers.CharField(required=True, max_length=20)
    address = serializers.CharField(required=False, allow_blank=True)
    profile_pic = serializers.ImageField(required=False)


class PatientRegistrationSerializer(serializers.Serializer):
    """Serializer cho patient registration."""
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    mobile = serializers.CharField(required=True, max_length=20)
    symptoms = serializers.CharField(required=True, max_length=100)
    address = serializers.CharField(required=False, allow_blank=True)
    profile_pic = serializers.ImageField(required=False)


class DischargeSerializer(serializers.Serializer):
    """Serializer cho discharge request."""
    room_charge = serializers.IntegerField(required=True, min_value=0)
    medicine_cost = serializers.IntegerField(required=True, min_value=0)
    doctor_fee = serializers.IntegerField(required=True, min_value=0)
    other_charge = serializers.IntegerField(required=False, default=0)
    total = serializers.IntegerField(required=True, min_value=0)
