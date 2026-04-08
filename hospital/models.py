from django.db import models
from django.contrib.auth.models import User



departments=[('Cardiologist','Cardiologist'),
('Dermatologists','Dermatologists'),
('Emergency Medicine Specialists','Emergency Medicine Specialists'),
('Allergists/Immunologists','Allergists/Immunologists'),
('Anesthesiologists','Anesthesiologists'),
('Colon and Rectal Surgeons','Colon and Rectal Surgeons')
]

appointment_time_slots = [
('08:00', '08:00'),
('09:00', '09:00'),
('10:00', '10:00'),
('11:00', '11:00'),
('13:00', '13:00'),
('14:00', '14:00'),
('15:00', '15:00'),
('16:00', '16:00'),
]

patient_treatment_statuses = [
('under_treatment', 'Đang điều trị'),
('treated', 'Đã điều trị'),
]

class Doctor(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/DoctorProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    department= models.CharField(max_length=50,choices=departments,default='Cardiologist')
    basic_schedule = models.CharField(max_length=255, default='', blank=True)
    consultation_fee = models.PositiveIntegerField(null=True, blank=True, default=0)
    degree_certificate = models.TextField(default='', blank=True)
    rating_avg = models.FloatField(null=True, blank=True, default=0)
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True, default=0)
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return "{} ({})".format(self.user.first_name,self.department)



class Patient(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/PatientProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    symptoms = models.CharField(max_length=100,null=False)
    assignedDoctorId = models.PositiveIntegerField(null=True)
    admitDate=models.DateField(auto_now=True)
    status=models.BooleanField(default=False)
    treatment_status = models.CharField(
        max_length=20,
        choices=patient_treatment_statuses,
        default='under_treatment',
    )
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    @property
    def is_under_treatment(self):
        return self.treatment_status == 'under_treatment'
    @property
    def assigned_doctor_name(self):
        if not self.assignedDoctorId:
            return 'Chưa phân công'
        doctor = Doctor.objects.select_related('user').filter(user_id=self.assignedDoctorId).first()
        return doctor.get_name if doctor else 'Chưa phân công'
    def __str__(self):
        return self.user.first_name+" ("+self.symptoms+")"


class Appointment(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    doctorId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40,null=True)
    doctorName=models.CharField(max_length=40,null=True)
    appointmentDate=models.DateField(null=True, blank=True)
    appointmentTime=models.CharField(max_length=5, choices=appointment_time_slots, null=True, blank=True)
    description=models.TextField(max_length=500)
    status=models.BooleanField(default=False)



class PatientDischargeDetails(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40)
    assignedDoctorName=models.CharField(max_length=40)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    symptoms = models.CharField(max_length=100,null=True)

    admitDate=models.DateField(null=False)
    releaseDate=models.DateField(null=False)
    daySpent=models.PositiveIntegerField(null=False)

    roomCharge=models.PositiveIntegerField(null=False)
    medicineCost=models.PositiveIntegerField(null=False)
    doctorFee=models.PositiveIntegerField(null=False)
    OtherCharge=models.PositiveIntegerField(null=False)
    total=models.PositiveIntegerField(null=False)


#Developed By : sumit kumar
#facebook : fb.com/sumit.luv
#Youtube :youtube.com/AT05s
