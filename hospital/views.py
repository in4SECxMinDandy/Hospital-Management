from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse, HttpResponse
from . import forms, models
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime, date
from django.conf import settings
from django.db.models import Q
import io
from xhtml2pdf import pisa
from django.template.loader import get_template


def is_ajax(request):
    """Kiem tra neu request la AJAX."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def home_view(request):
    """Trang chu - chuyen huong neu da dang nhap."""
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/index.html')


def adminclick_view(request):
    """Trang lua chon admin."""
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/adminclick.html')


def doctorclick_view(request):
    """Trang lua chon bac si."""
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/doctorclick.html')


def patientclick_view(request):
    """Trang lua chon benh nhan."""
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/patientclick.html')


def admin_signup_view(request):
    """Dang ky tai khoan admin."""
    form = forms.AdminSigupForm()
    if request.method == 'POST':
        form = forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group, _ = Group.objects.get_or_create(name='ADMIN')
            my_admin_group.user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request, 'hospital/adminsignup.html', {'form': form})


def doctor_signup_view(request):
    """Dang ky tai khoan bac si."""
    userForm = forms.DoctorUserForm()
    doctorForm = forms.DoctorForm()
    context = {'userForm': userForm, 'doctorForm': doctorForm}
    
    if request.method == 'POST':
        userForm = forms.DoctorUserForm(request.POST)
        doctorForm = forms.DoctorForm(request.POST, request.FILES)
        
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            doctor = doctorForm.save(commit=False)
            doctor.user = user
            doctor.save()
            
            my_doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group.user_set.add(user)
            
            return HttpResponseRedirect('doctorlogin')
    
    return render(request, 'hospital/doctorsignup.html', context=context)


def patient_signup_view(request):
    """Dang ky tai khoan benh nhan."""
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    context = {'userForm': userForm, 'patientForm': patientForm}
    
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            patient = patientForm.save(commit=False)
            patient.user = user
            patient.assignedDoctorId = request.POST.get('assignedDoctorId')
            patient.save()
            
            my_patient_group, _ = Group.objects.get_or_create(name='PATIENT')
            my_patient_group.user_set.add(user)
            
            return HttpResponseRedirect('patientlogin')
    
    return render(request, 'hospital/patientsignup.html', context=context)


def is_admin(user):
    """Kiem tra user co thuoc nhom ADMIN."""
    return user.groups.filter(name='ADMIN').exists()


def is_doctor(user):
    """Kiem tra user co thuoc nhom DOCTOR."""
    return user.groups.filter(name='DOCTOR').exists()


def is_patient(user):
    """Kiem tra user co thuoc nhom PATIENT."""
    return user.groups.filter(name='PATIENT').exists()


def afterlogin_view(request):
    """Chuyen huong sau khi dang nhap thanh cong."""
    if is_admin(request.user):
        return redirect('admin-dashboard')
    
    elif is_doctor(request.user):
        doctor = models.Doctor.objects.filter(user_id=request.user.id, status=True).first()
        if doctor:
            return redirect('doctor-dashboard')
        return render(request, 'hospital/doctor_wait_for_approval.html')
    
    elif is_patient(request.user):
        patient = models.Patient.objects.filter(user_id=request.user.id, status=True).first()
        if patient:
            return redirect('patient-dashboard')
        return render(request, 'hospital/patient_wait_for_approval.html')
    
    return redirect('logout')


# ================== ADMIN VIEWS ==================

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    """Trang dashboard cua admin."""
    doctors = models.Doctor.objects.all().order_by('-id')[:10]
    patients = models.Patient.objects.all().order_by('-id')[:10]
    
    doctorcount = models.Doctor.objects.filter(status=True).count()
    pendingdoctorcount = models.Doctor.objects.filter(status=False).count()
    patientcount = models.Patient.objects.filter(status=True).count()
    pendingpatientcount = models.Patient.objects.filter(status=False).count()
    appointmentcount = models.Appointment.objects.filter(status=True).count()
    pendingappointmentcount = models.Appointment.objects.filter(status=False).count()
    
    context = {
        'doctors': doctors,
        'patients': patients,
        'doctorcount': doctorcount,
        'pendingdoctorcount': pendingdoctorcount,
        'patientcount': patientcount,
        'pendingpatientcount': pendingpatientcount,
        'appointmentcount': appointmentcount,
        'pendingappointmentcount': pendingappointmentcount,
    }
    return render(request, 'hospital/admin_dashboard.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    """Trang quan ly bac si."""
    return render(request, 'hospital/admin_doctor.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    """Xem danh sach bac si da duoc approve."""
    doctors = models.Doctor.objects.filter(status=True).select_related('user')
    return render(request, 'hospital/admin_view_doctor.html', {'doctors': doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request, pk):
    """Xoa bac si khoi he thong."""
    doctor = get_object_or_404(models.Doctor, id=pk)
    user = doctor.user
    doctor.delete()
    user.delete()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Bác sĩ đã được xóa thành công!'
        })
    
    return redirect('admin-view-doctor')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request, pk):
    """Cap nhat thong tin bac si."""
    doctor = get_object_or_404(models.Doctor, id=pk)
    user = doctor.user
    
    userForm = forms.DoctorUserForm(instance=user)
    doctorForm = forms.DoctorForm(request.FILES, instance=doctor)
    context = {'userForm': userForm, 'doctorForm': doctorForm}
    
    if request.method == 'POST':
        userForm = forms.DoctorUserForm(request.POST, instance=user)
        doctorForm = forms.DoctorForm(request.POST, request.FILES, instance=doctor)
        
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            doctor = doctorForm.save(commit=False)
            doctor.status = True
            doctor.save()
            
            return redirect('admin-view-doctor')
    
    return render(request, 'hospital/admin_update_doctor.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    """Them bac si moi boi admin."""
    userForm = forms.DoctorUserForm()
    doctorForm = forms.DoctorForm()
    context = {'userForm': userForm, 'doctorForm': doctorForm}
    
    if request.method == 'POST':
        userForm = forms.DoctorUserForm(request.POST)
        doctorForm = forms.DoctorForm(request.POST, request.FILES)
        
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            doctor = doctorForm.save(commit=False)
            doctor.user = user
            doctor.status = True
            doctor.save()
            
            my_doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group.user_set.add(user)
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Bác sĩ đã được thêm thành công!',
                    'redirect': '/admin-view-doctor'
                })
            
            return HttpResponseRedirect('admin-view-doctor')
    
    return render(request, 'hospital/admin_add_doctor.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    """Xem danh sach bac si cho duyet."""
    doctors = models.Doctor.objects.filter(status=False).select_related('user')
    return render(request, 'hospital/admin_approve_doctor.html', {'doctors': doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request, pk):
    """Chap nhan dang ky bac si."""
    doctor = get_object_or_404(models.Doctor, id=pk)
    doctor.status = True
    doctor.save()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Đã chấp nhận đăng ký bác sĩ!'
        })
    
    return redirect('admin-approve-doctor')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request, pk):
    """Tu choi dang ky bac si va xoa tai khoan."""
    doctor = get_object_or_404(models.Doctor, id=pk)
    user = doctor.user
    doctor.delete()
    user.delete()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Đã từ chối và xóa đăng ký bác sĩ!'
        })
    
    return redirect('admin-approve-doctor')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    """Xem bac si theo chuyen khoa."""
    doctors = models.Doctor.objects.filter(status=True).select_related('user')
    return render(request, 'hospital/admin_view_doctor_specialisation.html', {'doctors': doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    """Trang quan ly benh nhan."""
    return render(request, 'hospital/admin_patient.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    """Xem danh sach benh nhan da duoc approve."""
    patients = models.Patient.objects.filter(status=True).select_related('user')
    return render(request, 'hospital/admin_view_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request, pk):
    """Xoa benh nhan khoi he thong."""
    patient = get_object_or_404(models.Patient, id=pk)
    user = patient.user
    patient.delete()
    user.delete()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Bệnh nhân đã được xóa thành công!'
        })
    
    return redirect('admin-view-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request, pk):
    """Cap nhat thong tin benh nhan."""
    patient = get_object_or_404(models.Patient, id=pk)
    user = patient.user
    
    userForm = forms.PatientUserForm(instance=user)
    patientForm = forms.PatientForm(request.FILES, instance=patient)
    context = {'userForm': userForm, 'patientForm': patientForm}
    
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST, instance=user)
        patientForm = forms.PatientForm(request.POST, request.FILES, instance=patient)
        
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            patient = patientForm.save(commit=False)
            patient.status = True
            patient.assignedDoctorId = request.POST.get('assignedDoctorId')
            patient.save()
            
            return redirect('admin-view-patient')
    
    return render(request, 'hospital/admin_update_patient.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    """Them benh nhan moi boi admin."""
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    context = {'userForm': userForm, 'patientForm': patientForm}
    
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            patient = patientForm.save(commit=False)
            patient.user = user
            patient.status = True
            patient.assignedDoctorId = request.POST.get('assignedDoctorId')
            patient.save()
            
            my_patient_group, _ = Group.objects.get_or_create(name='PATIENT')
            my_patient_group.user_set.add(user)
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Bệnh nhân đã được thêm thành công!',
                    'redirect': '/admin-view-patient'
                })
            
            return HttpResponseRedirect('admin-view-patient')
    
    return render(request, 'hospital/admin_add_patient.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    """Xem danh sach benh nhan cho duyet."""
    patients = models.Patient.objects.filter(status=False).select_related('user')
    return render(request, 'hospital/admin_approve_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request, pk):
    """Chap nhan dang ky benh nhan."""
    patient = get_object_or_404(models.Patient, id=pk)
    patient.status = True
    patient.save()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Đã chấp nhận đăng ký bệnh nhân!'
        })
    
    return redirect('admin-approve-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request, pk):
    """Tu choi dang ky benh nhan va xoa tai khoan."""
    patient = get_object_or_404(models.Patient, id=pk)
    user = patient.user
    patient.delete()
    user.delete()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Đã từ chối và xóa đăng ký bệnh nhân!'
        })
    
    return redirect('admin-approve-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    """Trang xuat vien benh nhan."""
    patients = models.Patient.objects.filter(status=True).select_related('user')
    return render(request, 'hospital/admin_discharge_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request, pk):
    """Xu ly xuat vien va tao hoa don."""
    patient = get_object_or_404(models.Patient, id=pk)
    
    admit_datetime = datetime.combine(patient.admitDate, datetime.min.time())
    days_diff = (datetime.now() - admit_datetime).days
    days_spent = max(1, days_diff)
    
    doctor = models.User.objects.filter(id=patient.assignedDoctorId).first()
    doctor_name = doctor.first_name if doctor else 'Chua phan cong'
    
    patient_context = {
        'patientId': pk,
        'name': patient.get_name,
        'mobile': patient.mobile,
        'address': patient.address,
        'symptoms': patient.symptoms,
        'admitDate': patient.admitDate,
        'todayDate': date.today(),
        'day': days_spent,
        'assignedDoctorName': doctor_name,
    }
    
    if request.method == 'POST':
        room_charge = int(request.POST.get('roomCharge', 0))
        medicine_cost = int(request.POST.get('medicineCost', 0))
        doctor_fee = int(request.POST.get('doctorFee', 0))
        other_charge = int(request.POST.get('OtherCharge', 0))
        total = (room_charge * days_spent) + medicine_cost + doctor_fee + other_charge
        
        fee_context = {
            'roomCharge': room_charge * days_spent,
            'doctorFee': doctor_fee,
            'medicineCost': medicine_cost,
            'OtherCharge': other_charge,
            'total': total,
        }
        patient_context.update(fee_context)
        
        discharge_details = models.PatientDischargeDetails.objects.create(
            patientId=pk,
            patientName=patient.get_name,
            assignedDoctorName=doctor_name,
            address=patient.address,
            mobile=patient.mobile,
            symptoms=patient.symptoms,
            admitDate=patient.admitDate,
            releaseDate=date.today(),
            daySpent=days_spent,
            medicineCost=medicine_cost,
            roomCharge=room_charge * days_spent,
            doctorFee=doctor_fee,
            OtherCharge=other_charge,
            total=total,
        )
        
        return render(request, 'hospital/patient_final_bill.html', context=patient_context)
    
    return render(request, 'hospital/patient_generate_bill.html', context=patient_context)


def render_to_pdf(template_src, context_dict):
    """Chuyen doi HTML template sang PDF."""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    
    try:
        pdf = pisa.pisaDocument(io.BytesIO(html.encode('UTF-8')), result)
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
    except Exception:
        pass
    
    return HttpResponse('Loi tao PDF', status=500)


def download_pdf_view(request, pk):
    """Tai xuong hoa don xuat vien PDF."""
    discharge_details = models.PatientDischargeDetails.objects.filter(patientId=pk).order_by('-id').first()
    
    if not discharge_details:
        return HttpResponse('Khong tim thay hoa don', status=404)
    
    context = {
        'patientName': discharge_details.patientName,
        'assignedDoctorName': discharge_details.assignedDoctorName,
        'address': discharge_details.address,
        'mobile': discharge_details.mobile,
        'symptoms': discharge_details.symptoms,
        'admitDate': discharge_details.admitDate,
        'releaseDate': discharge_details.releaseDate,
        'daySpent': discharge_details.daySpent,
        'medicineCost': discharge_details.medicineCost,
        'roomCharge': discharge_details.roomCharge,
        'doctorFee': discharge_details.doctorFee,
        'OtherCharge': discharge_details.OtherCharge,
        'total': discharge_details.total,
    }
    
    return render_to_pdf('hospital/download_bill.html', context)


# ================== APPOINTMENT VIEWS ==================

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    """Trang quan ly lich hen."""
    return render(request, 'hospital/admin_appointment.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    """Xem danh sach lich hen da duoc approve."""
    appointments = models.Appointment.objects.filter(status=True)
    return render(request, 'hospital/admin_view_appointment.html', {'appointments': appointments})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    """Them lich hen moi boi admin."""
    appointmentForm = forms.AppointmentForm()
    context = {'appointmentForm': appointmentForm}
    
    if request.method == 'POST':
        appointmentForm = forms.AppointmentForm(request.POST)
        
        if appointmentForm.is_valid():
            doctor_id = request.POST.get('doctorId')
            patient_id = request.POST.get('patientId')
            
            doctor = get_object_or_404(models.User, id=doctor_id)
            patient = get_object_or_404(models.User, id=patient_id)
            
            appointment = appointmentForm.save(commit=False)
            appointment.doctorId = doctor_id
            appointment.patientId = patient_id
            appointment.doctorName = doctor.first_name
            appointment.patientName = patient.first_name
            appointment.status = True
            appointment.save()
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Lịch hẹn đã được tạo thành công!',
                    'redirect': '/admin-view-appointment'
                })
            
            return HttpResponseRedirect('admin-view-appointment')
    
    return render(request, 'hospital/admin_add_appointment.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    """Xem danh sach lich hen cho duyet."""
    appointments = models.Appointment.objects.filter(status=False)
    return render(request, 'hospital/admin_approve_appointment.html', {'appointments': appointments})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request, pk):
    """Chap nhan lich hen."""
    appointment = get_object_or_404(models.Appointment, id=pk)
    appointment.status = True
    appointment.save()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Đã chấp nhận lịch hẹn!'
        })
    
    return redirect('admin-approve-appointment')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request, pk):
    """Tu choi lich hen."""
    appointment = get_object_or_404(models.Appointment, id=pk)
    appointment.delete()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Đã từ chối và xóa lịch hẹn!'
        })
    
    return redirect('admin-approve-appointment')


# ================== DOCTOR VIEWS ==================

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    """Dashboard cua bac si."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    
    patientcount = models.Patient.objects.filter(status=True, assignedDoctorId=request.user.id).count()
    appointmentcount = models.Appointment.objects.filter(status=True, doctorId=request.user.id).count()
    patientdischarged = models.PatientDischargeDetails.objects.filter(
        assignedDoctorName=request.user.first_name
    ).distinct().count()
    
    appointments = models.Appointment.objects.filter(
        status=True, doctorId=request.user.id
    ).order_by('-id')[:10]
    
    patients = models.Patient.objects.filter(
        status=True, assignedDoctorId=request.user.id
    ).order_by('-id')[:10]
    
    context = {
        'patientcount': patientcount,
        'appointmentcount': appointmentcount,
        'patientdischarged': patientdischarged,
        'appointments': zip(appointments, patients),
        'doctor': doctor,
    }
    return render(request, 'hospital/doctor_dashboard.html', context=context)


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    """Trang quan ly benh nhan cua bac si."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    return render(request, 'hospital/doctor_patient.html', {'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    """Xem danh sach benh nhan dang dieu tri."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    patients = models.Patient.objects.filter(status=True, assignedDoctorId=request.user.id)
    return render(request, 'hospital/doctor_view_patient.html', {'patients': patients, 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    """Tim kiem benh nhan."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    query = request.GET.get('query', '').strip()
    
    patients = models.Patient.objects.filter(
        status=True, assignedDoctorId=request.user.id
    ).filter(
        Q(symptoms__icontains=query) | Q(user__first_name__icontains=query)
    )
    
    return render(request, 'hospital/doctor_view_patient.html', {'patients': patients, 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    """Xem danh sach benh nhan da xuat vien."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    dischargedpatients = models.PatientDischargeDetails.objects.filter(
        assignedDoctorName=request.user.first_name
    ).distinct()
    return render(request, 'hospital/doctor_view_discharge_patient.html', 
                  {'dischargedpatients': dischargedpatients, 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    """Trang quan ly lich hen cua bac si."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    return render(request, 'hospital/doctor_appointment.html', {'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    """Xem lich hen cua bac si."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    appointments = models.Appointment.objects.filter(status=True, doctorId=request.user.id)
    patients = models.Patient.objects.filter(status=True, assignedDoctorId=request.user.id)
    return render(request, 'hospital/doctor_view_appointment.html', 
                  {'appointments': zip(appointments, patients), 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    """Trang xoa lich hen."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    appointments = models.Appointment.objects.filter(status=True, doctorId=request.user.id)
    patients = models.Patient.objects.filter(status=True, assignedDoctorId=request.user.id)
    return render(request, 'hospital/doctor_delete_appointment.html', 
                  {'appointments': zip(appointments, patients), 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request, pk):
    """Xoa lich hen."""
    appointment = get_object_or_404(models.Appointment, id=pk)
    appointment.delete()
    
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Lịch hẹn đã được xóa!'
        })
    
    return redirect('doctor-delete-appointment')


# ================== PATIENT VIEWS ==================

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    """Dashboard cua benh nhan."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    
    try:
        doctor = models.Doctor.objects.get(user_id=patient.assignedDoctorId)
        doctor_name = doctor.get_name
        doctor_mobile = doctor.mobile
        doctor_address = doctor.address
        doctor_department = doctor.department
    except models.Doctor.DoesNotExist:
        doctor_name = 'Chua phan cong'
        doctor_mobile = 'N/A'
        doctor_address = 'N/A'
        doctor_department = 'N/A'
    
    context = {
        'patient': patient,
        'doctorName': doctor_name,
        'doctorMobile': doctor_mobile,
        'doctorAddress': doctor_address,
        'symptoms': patient.symptoms,
        'doctorDepartment': doctor_department,
        'admitDate': patient.admitDate,
    }
    return render(request, 'hospital/patient_dashboard.html', context=context)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    """Trang quan ly lich hen cua benh nhan."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    return render(request, 'hospital/patient_appointment.html', {'patient': patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request):
    """Dat lich hen kham."""
    appointmentForm = forms.PatientAppointmentForm()
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    context = {'appointmentForm': appointmentForm, 'patient': patient}
    
    if request.method == 'POST':
        appointmentForm = forms.PatientAppointmentForm(request.POST)
        
        if appointmentForm.is_valid():
            doctor_id = request.POST.get('doctorId')
            doctor = get_object_or_404(models.Doctor, user_id=doctor_id)
            
            appointment = appointmentForm.save(commit=False)
            appointment.doctorId = doctor_id
            appointment.patientId = request.user.id
            appointment.doctorName = doctor.user.first_name
            appointment.patientName = request.user.first_name
            appointment.status = False
            appointment.save()
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Lịch hẹn đã được đặt thành công! Vui lòng chờ bác sĩ xác nhận.',
                    'redirect': '/patient-view-appointment'
                })
            
            return HttpResponseRedirect('patient-view-appointment')
    
    return render(request, 'hospital/patient_book_appointment.html', context=context)


def patient_view_doctor_view(request):
    """Xem danh sach bac si."""
    if not request.user.is_authenticated:
        return redirect('patientlogin')
    
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    doctors = models.Doctor.objects.filter(status=True)
    return render(request, 'hospital/patient_view_doctor.html', 
                  {'patient': patient, 'doctors': doctors})


def search_doctor_view(request):
    """Tim kiem bac si."""
    if not request.user.is_authenticated:
        return redirect('patientlogin')
    
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    query = request.GET.get('query', '').strip()
    
    doctors = models.Doctor.objects.filter(status=True).filter(
        Q(department__icontains=query) | Q(user__first_name__icontains=query)
    )
    
    return render(request, 'hospital/patient_view_doctor.html', 
                  {'patient': patient, 'doctors': doctors})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    """Xem lich hen cua benh nhan."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    appointments = models.Appointment.objects.filter(patientId=request.user.id)
    return render(request, 'hospital/patient_view_appointment.html', 
                  {'appointments': appointments, 'patient': patient})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    """Xem thong tin xuat vien."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    discharge_details = models.PatientDischargeDetails.objects.filter(
        patientId=patient.id
    ).order_by('-id').first()
    
    if discharge_details:
        context = {
            'is_discharged': True,
            'patient': patient,
            'patientId': patient.id,
            'patientName': patient.get_name,
            'assignedDoctorName': discharge_details.assignedDoctorName,
            'address': patient.address,
            'mobile': patient.mobile,
            'symptoms': patient.symptoms,
            'admitDate': patient.admitDate,
            'releaseDate': discharge_details.releaseDate,
            'daySpent': discharge_details.daySpent,
            'medicineCost': discharge_details.medicineCost,
            'roomCharge': discharge_details.roomCharge,
            'doctorFee': discharge_details.doctorFee,
            'OtherCharge': discharge_details.OtherCharge,
            'total': discharge_details.total,
        }
    else:
        context = {
            'is_discharged': False,
            'patient': patient,
            'patientId': request.user.id,
        }
    
    return render(request, 'hospital/patient_discharge.html', context=context)


# ================== PUBLIC VIEWS ==================

def aboutus_view(request):
    """Trang gioi thieu."""
    return render(request, 'hospital/aboutus.html')


def contactus_view(request):
    """Trang lien he."""
    contact_form = forms.ContactusForm()
    
    if request.method == 'POST':
        contact_form = forms.ContactusForm(request.POST)
        
        if contact_form.is_valid():
            name = contact_form.cleaned_data['Name']
            email = contact_form.cleaned_data['Email']
            message = contact_form.cleaned_data['Message']
            
            try:
                send_mail(
                    f'{name} || {email}',
                    message,
                    settings.EMAIL_HOST_USER,
                    settings.EMAIL_RECEIVING_USER,
                    fail_silently=False
                )
            except Exception:
                pass
            
            return render(request, 'hospital/contactussuccess.html')
    
    return render(request, 'hospital/contactus.html', {'form': contact_form})
