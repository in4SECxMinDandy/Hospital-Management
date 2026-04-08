from django import forms
from django.contrib.auth.models import User
from . import models



#for admin signup
class AdminSigupForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }


#for student related form
class DoctorUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }
class DoctorForm(forms.ModelForm):
    class Meta:
        model=models.Doctor
        # LOAI BO: status, address, mobile, profile_pic - chi admin moi set duoc
        fields=['address','mobile','department','profile_pic']
        # status luon dat trong view (True = auto approve khi admin tao)
        # de tranh loi form/thieu field tren template khi dung boi admin

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            import re
            # Vietnamese phone number validation (10 digits starting with 0)
            if not re.match(r'^0\d{9}$', mobile):
                raise forms.ValidationError('Số điện thoại phải có 10 chữ số và bắt đầu bằng số 0')
        return mobile



#for teacher related form
class PatientUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }
class PatientForm(forms.ModelForm):
    #this is the extrafield for linking patient and their assigend doctor
    #this will show dropdown __str__ method doctor model is shown on html so override it
    #to_field_name this will fetch corresponding value  user_id present in Doctor model and return it
    assignedDoctorId=forms.ModelChoiceField(
        queryset=models.Doctor.objects.all().filter(status=True),
        empty_label="Chưa chọn bác sĩ",
        to_field_name="user_id",
        required=False,
    )
    treatment_status = forms.ChoiceField(
        choices=models.patient_treatment_statuses,
        required=False,
        initial='under_treatment',
    )
    class Meta:
        model=models.Patient
        # LOAI BO: status - chi admin moi set duoc thong qua view
        fields=['address','mobile','symptoms','profile_pic','treatment_status']
        # status luon dat trong view (True = auto approve khi admin tao)

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            import re
            # Vietnamese phone number validation (10 digits starting with 0)
            if not re.match(r'^0\d{9}$', mobile):
                raise forms.ValidationError('Số điện thoại phải có 10 chữ số và bắt đầu bằng số 0')
        return mobile

    def clean_symptoms(self):
        symptoms = self.cleaned_data.get('symptoms')
        if symptoms and len(symptoms) < 3:
            raise forms.ValidationError('Mô tả triệu chứng phải có ít nhất 3 ký tự')
        return symptoms



class PatientProfileUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = models.Patient
        fields = ['mobile', 'address', 'symptoms', 'profile_pic']

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            import re
            if not re.match(r'^0\d{9}$', mobile):
                raise forms.ValidationError('Sá»‘ Ä‘iá»‡n thoáº¡i pháº£i cÃ³ 10 chá»¯ sá»‘ vÃ  báº¯t Ä‘áº§u báº±ng sá»‘ 0')
        return mobile

    def clean_symptoms(self):
        symptoms = self.cleaned_data.get('symptoms')
        if symptoms and len(symptoms) < 3:
            raise forms.ValidationError('MÃ´ táº£ triá»‡u chá»©ng pháº£i cÃ³ Ã­t nháº¥t 3 kÃ½ tá»±')
        return symptoms


class AppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Tên bác sĩ và Khoa", to_field_name="user_id")
    patientId=forms.ModelChoiceField(queryset=models.Patient.objects.all().filter(status=True),empty_label="Tên bệnh nhân và Triệu chứng", to_field_name="user_id")
    appointmentDate=forms.DateField(widget=forms.DateInput(attrs={'type':'date'}),required=False)
    appointmentTime=forms.ChoiceField(choices=models.appointment_time_slots, required=True)
    class Meta:
        model=models.Appointment
        fields=['description','status','appointmentDate','appointmentTime']


class PatientAppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Tên bác sĩ và Khoa", to_field_name="user_id")
    appointmentDate=forms.DateField(widget=forms.DateInput(attrs={'type':'date'}),required=False)
    appointmentTime=forms.ChoiceField(choices=models.appointment_time_slots, required=True)
    class Meta:
        model=models.Appointment
        # status luon dat trong view (False = cho duyet) de tranh loi form / thieu field tren template
        fields=['description','appointmentDate','appointmentTime']


#for contact us page
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))



#Developed By : sumit kumar
#facebook : fb.com/sumit.luv
#Youtube :youtube.com/AT05s
