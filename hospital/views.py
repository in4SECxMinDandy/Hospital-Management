from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from . import forms, models
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime, date
from django.db.models import Q
from django.db import transaction
import io
import os
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.views.decorators.csrf import ensure_csrf_cookie
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def is_ajax(request):
    """Kiem tra neu request la AJAX."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def pair_appointments_with_patients(appointments_qs):
    """
    Ghep tung Appointment voi Patient theo patientId (User.id cua benh nhan).
    Tranh zip() theo thu tu — khong dung voi danh sach benh nhan duoc gan bac si.
    """
    appointments = list(appointments_qs)
    if not appointments:
        return []
    user_ids = [a.patientId for a in appointments if a.patientId is not None]
    if not user_ids:
        return [(a, None) for a in appointments]
    patient_map = {
        p.user_id: p
        for p in models.Patient.objects.filter(user_id__in=user_ids).select_related('user')
    }
    return [(a, patient_map.get(a.patientId)) for a in appointments]


def build_doctor_patient_history(doctor_id):
    """Tong hop lich su lich hen cua mot bac si theo tung benh nhan."""
    appointments_qs = models.Appointment.objects.filter(
        doctorId=doctor_id
    ).order_by('-appointmentDate', '-appointmentTime', '-id')
    rows = pair_appointments_with_patients(appointments_qs)

    history_map = {}
    for appointment, patient in rows:
        patient_key = appointment.patientId or f"name:{appointment.patientName or appointment.id}"
        if patient_key not in history_map:
            history_map[patient_key] = {
                'patient': patient,
                'patient_name': appointment.patientName or (
                    patient.get_name if patient else 'Khong ro benh nhan'
                ),
                'mobile': patient.mobile if patient else '',
                'address': patient.address if patient else '',
                'symptoms': patient.symptoms if patient else '',
                'latest_appointment': appointment,
                'confirmed_count': 0,
                'pending_count': 0,
                'total_appointments': 0,
            }

        history_entry = history_map[patient_key]
        history_entry['total_appointments'] += 1
        if appointment.status:
            history_entry['confirmed_count'] += 1
        else:
            history_entry['pending_count'] += 1

    return list(history_map.values())


def format_currency(amount):
    """Dinh dang tien theo kieu ngan cach hang nghin, them don vi VND."""
    return f"{int(amount):,}".replace(",", ".") + " VND"


def parse_charge_amount(raw_value, field_label):
    """Phan tich gia tri chi phi va chan du lieu am hoac khong hop le."""
    cleaned = (raw_value or "").strip()
    if not cleaned:
        return 0

    normalized = cleaned.replace(" ", "").replace(".", "").replace(",", "")
    if not normalized.isdigit():
        raise ValueError(f"{field_label} khong hop le.")

    amount = int(normalized)
    if amount < 0:
        raise ValueError(f"{field_label} khong duoc am.")
    return amount


def build_invoice_number(record_id, release_date):
    """Tao ma hoa don de hien thi tren giao dien va file PDF."""
    return f"HD-{release_date:%Y%m%d}-{record_id:05d}"


def build_discharge_context(patient, doctor_name, days_spent, charge_data=None, errors=None, invoice_number=None):
    """Dong bo du lieu cho form tao hoa don, trang ket qua va file PDF."""
    release_date = date.today()
    room_charge_per_day = 0
    doctor_fee = 0
    medicine_cost = 0
    other_charge = 0

    if charge_data:
        room_charge_per_day = charge_data.get('room_charge_per_day', 0)
        doctor_fee = charge_data.get('doctor_fee', 0)
        medicine_cost = charge_data.get('medicine_cost', 0)
        other_charge = charge_data.get('other_charge', 0)

    room_charge_total = room_charge_per_day * days_spent
    total = room_charge_total + doctor_fee + medicine_cost + other_charge

    return {
        'patientId': patient.id,
        'name': patient.get_name,
        'mobile': patient.mobile,
        'address': patient.address,
        'symptoms': patient.symptoms,
        'admitDate': patient.admitDate,
        'todayDate': release_date,
        'releaseDate': release_date,
        'day': days_spent,
        'daySpent': days_spent,
        'assignedDoctorName': doctor_name,
        'invoiceNumber': invoice_number or 'Se tao sau khi luu',
        'errorMessage': errors[0] if errors else '',
        'errors': errors or [],
        'roomChargePerDay': room_charge_per_day,
        'roomCharge': room_charge_total,
        'doctorFee': doctor_fee,
        'medicineCost': medicine_cost,
        'OtherCharge': other_charge,
        'total': total,
        'roomChargePerDayDisplay': format_currency(room_charge_per_day),
        'roomChargeDisplay': format_currency(room_charge_total),
        'doctorFeeDisplay': format_currency(doctor_fee),
        'medicineCostDisplay': format_currency(medicine_cost),
        'otherChargeDisplay': format_currency(other_charge),
        'totalDisplay': format_currency(total),
    }


def ensure_pdf_fonts_registered():
    """Dang ky font Unicode de xhtml2pdf co the render tieng Viet on dinh."""
    if getattr(ensure_pdf_fonts_registered, '_done', False):
        return

    font_candidates = [
        ('ClinicSans', r'C:\Windows\Fonts\arial.ttf'),
        ('ClinicSansBold', r'C:\Windows\Fonts\arialbd.ttf'),
    ]
    for font_name, font_path in font_candidates:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont(font_name, font_path))

    ensure_pdf_fonts_registered._done = True


def render_invoice_pdf(context_dict):
    """Tao file PDF hoa don bang ReportLab de giu unicode tieng Viet on dinh."""
    ensure_pdf_fonts_registered()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ClinicTitle',
        fontName='ClinicSansBold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='ClinicHeading',
        fontName='ClinicSansBold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='ClinicBody',
        fontName='ClinicSans',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#1f2937'),
    ))
    styles.add(ParagraphStyle(
        name='ClinicMuted',
        fontName='ClinicSans',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#64748b'),
    ))
    styles.add(ParagraphStyle(
        name='ClinicTotal',
        fontName='ClinicSansBold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#2563eb'),
    ))

    story = []
    header_table = Table(
        [[
            [
                Paragraph('Clinic Pro', styles['ClinicTitle']),
                Paragraph('Hóa đơn xuất viện và thanh toán điều trị nội trú', styles['ClinicMuted']),
            ],
            [
                Paragraph('Mã hóa đơn', styles['ClinicMuted']),
                Paragraph(context_dict['invoiceNumber'], styles['ClinicHeading']),
            ],
        ]],
        colWidths=[11.2 * cm, 5.1 * cm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, -1), 1.4, colors.HexColor('#2563eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5 * cm))

    meta_rows = [
        [
            Paragraph('<b>Bệnh nhân</b><br/>{}'.format(context_dict['patientName']), styles['ClinicBody']),
            Paragraph('<b>Bác sĩ phụ trách</b><br/>{}'.format(context_dict['assignedDoctorName']), styles['ClinicBody']),
        ],
        [
            Paragraph('<b>Điện thoại</b><br/>{}'.format(context_dict['mobile']), styles['ClinicBody']),
            Paragraph('<b>Địa chỉ</b><br/>{}'.format(context_dict['address']), styles['ClinicBody']),
        ],
        [
            Paragraph('<b>Ngày nhập viện</b><br/>{}'.format(context_dict['admitDate']), styles['ClinicBody']),
            Paragraph('<b>Ngày xuất viện</b><br/>{}'.format(context_dict['releaseDate']), styles['ClinicBody']),
        ],
        [
            Paragraph('<b>Số ngày nằm viện</b><br/>{} ngày'.format(context_dict['daySpent']), styles['ClinicBody']),
            Paragraph('', styles['ClinicBody']),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[8.15 * cm, 8.15 * cm], hAlign='LEFT')
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#e5e7eb')),
        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.45 * cm))

    story.append(Paragraph('Triệu chứng / ghi chú điều trị', styles['ClinicHeading']))
    note_table = Table([[Paragraph(context_dict['symptoms'], styles['ClinicBody'])]], colWidths=[16.3 * cm])
    note_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#e5e7eb')),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(note_table)
    story.append(Spacer(1, 0.45 * cm))

    story.append(Paragraph('Chi tiết thanh toán', styles['ClinicHeading']))
    detail_rows = [
        [Paragraph('Khoản mục', styles['ClinicHeading']), Paragraph('Giá trị', styles['ClinicHeading'])],
        [Paragraph('Tiền phòng mỗi ngày', styles['ClinicBody']), Paragraph(context_dict['roomChargePerDayDisplay'], styles['ClinicBody'])],
        [Paragraph(f"Tiền phòng {context_dict['daySpent']} ngày", styles['ClinicBody']), Paragraph(context_dict['roomChargeDisplay'], styles['ClinicBody'])],
        [Paragraph('Phí bác sĩ', styles['ClinicBody']), Paragraph(context_dict['doctorFeeDisplay'], styles['ClinicBody'])],
        [Paragraph('Tiền thuốc', styles['ClinicBody']), Paragraph(context_dict['medicineCostDisplay'], styles['ClinicBody'])],
        [Paragraph('Chi phí khác', styles['ClinicBody']), Paragraph(context_dict['otherChargeDisplay'], styles['ClinicBody'])],
    ]
    detail_table = Table(detail_rows, colWidths=[11.8 * cm, 4.5 * cm], hAlign='LEFT')
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('FONTNAME', (0, 0), (-1, 0), 'ClinicSansBold'),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#e5e7eb')),
        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.HexColor('#e5e7eb')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 9),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.28 * cm))

    total_table = Table(
        [[Paragraph('Tổng thanh toán', styles['ClinicTotal']), Paragraph(context_dict['totalDisplay'], styles['ClinicTotal'])]],
        colWidths=[11.8 * cm, 4.5 * cm],
        hAlign='LEFT'
    )
    total_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1.2, colors.HexColor('#cbd5e1')),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph('Clinic Pro - Hệ thống quản lý bệnh viện', styles['ClinicMuted']))

    doc.build(story)
    return HttpResponse(buffer.getvalue(), content_type='application/pdf')


def collect_form_errors(*forms_to_check):
    """Gom loi validation tu nhieu form thanh danh sach de tra JSON de doc hon."""
    errors = []
    for form in forms_to_check:
        for field_name, field_errors in form.errors.items():
            label = form.fields.get(field_name).label if field_name in form.fields else field_name
            for error in field_errors:
                if field_name == '__all__':
                    errors.append(str(error))
                else:
                    errors.append(f"{label}: {error}")
    return errors


def json_form_error_response(*forms_to_check):
    """Tra loi form cho request AJAX de frontend khong hieu nham HTML la thanh cong."""
    errors = collect_form_errors(*forms_to_check)
    return JsonResponse({
        'success': False,
        'message': errors[0] if errors else 'Du lieu khong hop le.',
        'errors': errors,
    }, status=400)


def prepare_update_user_form(form):
    """Cho phep bo trong password khi cap nhat va giu nguyen tai khoan cu."""
    form.fields['password'].required = False
    return form


def home_view(request):
    """Landing page cong khai tai /home."""
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'hospital/index.html')


def adminclick_view(request):
    """Route cu, giu de tuong thich va chuyen sang trang chon dang nhap moi."""
    return redirect('selectlogin')


def selectlogin_view(request):
    """Trang chon phan quyen dang nhap cong khai."""
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'hospital/selectlogin.html')


def doctorclick_view(request):
    """Trang lua chon bac si."""
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'hospital/doctorclick.html')


def patientclick_view(request):
    """Trang lua chon benh nhan."""
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'hospital/patientclick.html')


def admin_signup_view(request):
    """Khong cho phep dang ky admin qua UI, chuyen sang dang nhap."""
    return redirect('adminlogin')


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
            
            return redirect('doctorlogin')
    
    return render(request, 'hospital/doctorsignup.html', context=context)


def patient_signup_view(request):
    """Dang ky tai khoan benh nhan."""
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
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
            assigned_doctor = patientForm.cleaned_data.get('assignedDoctorId')
            patient.assignedDoctorId = assigned_doctor.user_id if assigned_doctor else None
            patient.save()
            
            my_patient_group, _ = Group.objects.get_or_create(name='PATIENT')
            my_patient_group.user_set.add(user)
            
            return redirect('patientlogin')
    context = {'userForm': userForm, 'patientForm': patientForm}
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
        patient = models.Patient.objects.filter(user_id=request.user.id).first()
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
    original_password = user.password
    
    userForm = prepare_update_user_form(forms.DoctorUserForm(instance=user))
    doctorForm = forms.DoctorForm(instance=doctor)
    context = {'userForm': userForm, 'doctorForm': doctorForm}
    
    if request.method == 'POST':
        userForm = prepare_update_user_form(forms.DoctorUserForm(request.POST, instance=user))
        doctorForm = forms.DoctorForm(request.POST, request.FILES, instance=doctor)
        
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save(commit=False)
            password = userForm.cleaned_data.get('password')
            if password:
                user.set_password(password)
            else:
                user.password = original_password
            user.save()
            
            doctor = doctorForm.save(commit=False)
            doctor.status = True
            doctor.save()

            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Cập nhật thông tin bác sĩ thành công.',
                    'redirect': '/admin-view-doctor'
                })

            return redirect('admin-view-doctor')

        if is_ajax(request):
            return json_form_error_response(userForm, doctorForm)
    
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
            with transaction.atomic():
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
            
            return redirect('admin-view-doctor')

        if is_ajax(request):
            return json_form_error_response(userForm, doctorForm)
    
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
    context = {
        'patientcount': models.Patient.objects.filter(
            status=True,
            treatment_status='under_treatment',
        ).count(),
        'treatedpatientcount': models.Patient.objects.filter(
            status=True,
            treatment_status='treated',
        ).count(),
        'pendingpatientcount': models.Patient.objects.filter(status=False).count(),
    }
    return render(request, 'hospital/admin_patient.html', context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    """Xem danh sach benh nhan dang dieu tri."""
    patients = models.Patient.objects.filter(
        status=True,
        treatment_status='under_treatment',
    ).select_related('user').order_by('-id')
    return render(request, 'hospital/admin_view_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_treated_patient_view(request):
    """Xem lich su benh nhan da dieu tri."""
    patients = models.Patient.objects.filter(
        status=True,
        treatment_status='treated',
    ).select_related('user').order_by('-id')
    return render(request, 'hospital/admin_treated_patient.html', {'patients': patients})


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
    original_password = user.password
    
    userForm = prepare_update_user_form(forms.PatientUserForm(instance=user))
    patientForm = forms.PatientForm(
        instance=patient,
        initial={
            'assignedDoctorId': patient.assignedDoctorId,
            'treatment_status': patient.treatment_status,
        },
    )
    context = {'userForm': userForm, 'patientForm': patientForm}
    
    if request.method == 'POST':
        userForm = prepare_update_user_form(forms.PatientUserForm(request.POST, instance=user))
        patientForm = forms.PatientForm(request.POST, request.FILES, instance=patient)
        
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save(commit=False)
            password = userForm.cleaned_data.get('password')
            if password:
                user.set_password(password)
            else:
                user.password = original_password
            user.save()
            
            patient = patientForm.save(commit=False)
            patient.status = True
            assigned_doctor = patientForm.cleaned_data.get('assignedDoctorId')
            patient.assignedDoctorId = assigned_doctor.user_id if assigned_doctor else None
            patient.save()
            redirect_url = '/admin-treated-patient' if patient.treatment_status == 'treated' else '/admin-view-patient'

            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Cập nhật thông tin bệnh nhân thành công.',
                    'redirect': redirect_url
                })

            return redirect(redirect_url)

        if is_ajax(request):
            return json_form_error_response(userForm, patientForm)
    
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
            patient.treatment_status = patientForm.cleaned_data.get('treatment_status') or 'under_treatment'
            assigned_doctor = patientForm.cleaned_data.get('assignedDoctorId')
            patient.assignedDoctorId = assigned_doctor.user_id if assigned_doctor else None
            patient.save()
            
            my_patient_group, _ = Group.objects.get_or_create(name='PATIENT')
            my_patient_group.user_set.add(user)
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Bệnh nhân đã được thêm thành công!',
                    'redirect': '/admin-view-patient'
                })
            
            return redirect('admin-view-patient')

        if is_ajax(request):
            return json_form_error_response(userForm, patientForm)
    
    return render(request, 'hospital/admin_add_patient.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    """Bo qua man duyet benh nhan va quay lai danh sach."""
    return redirect('admin-view-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request, pk):
    """Chap nhan dang ky benh nhan."""
    patient = get_object_or_404(models.Patient, id=pk)
    patient.status = True
    if not patient.treatment_status:
        patient.treatment_status = 'under_treatment'
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


# Compatibility override: patient approval is no longer a separate workflow.
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request, pk):
    """Route cu duoc giu lai de tranh loi link, nhung khong con xu ly duyet rieng."""
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Danh sach benh nhan khong con yeu cau buoc duyet rieng.',
            'redirect': '/admin-view-patient'
        })

    return redirect('admin-view-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request, pk):
    """Route cu duoc giu lai de tranh loi link, nhung khong con man tu choi rieng."""
    if is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': 'Vui long quan ly ho so truc tiep trong danh sach benh nhan.',
            'redirect': '/admin-view-patient'
        })

    return redirect('admin-view-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    """Trang xuat vien benh nhan."""
    patients = models.Patient.objects.filter(
        status=True,
        treatment_status='under_treatment',
    ).select_related('user')
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
    doctor_name = doctor.get_full_name().strip() if doctor and doctor.get_full_name().strip() else 'Chua phan cong'
    patient_context = build_discharge_context(patient, doctor_name, days_spent)
    
    if request.method == 'POST':
        try:
            charge_data = {
                'room_charge_per_day': parse_charge_amount(request.POST.get('roomCharge'), 'Tien phong moi ngay'),
                'doctor_fee': parse_charge_amount(request.POST.get('doctorFee'), 'Phi bac si'),
                'medicine_cost': parse_charge_amount(request.POST.get('medicineCost'), 'Tien thuoc'),
                'other_charge': parse_charge_amount(request.POST.get('OtherCharge'), 'Chi phi khac'),
            }
        except ValueError as exc:
            patient_context = build_discharge_context(patient, doctor_name, days_spent, errors=[str(exc)])
            return render(request, 'hospital/patient_generate_bill.html', context=patient_context)

        patient_context = build_discharge_context(patient, doctor_name, days_spent, charge_data=charge_data)

        discharge_details = models.PatientDischargeDetails.objects.create(
            patientId=patient.id,
            patientName=patient.get_name,
            assignedDoctorName=doctor_name,
            address=patient.address,
            mobile=patient.mobile,
            symptoms=patient.symptoms,
            admitDate=patient.admitDate,
            releaseDate=patient_context['releaseDate'],
            daySpent=days_spent,
            medicineCost=patient_context['medicineCost'],
            roomCharge=patient_context['roomCharge'],
            doctorFee=patient_context['doctorFee'],
            OtherCharge=patient_context['OtherCharge'],
            total=patient_context['total'],
        )
        patient.treatment_status = 'treated'
        patient.save(update_fields=['treatment_status'])

        patient_context['invoiceNumber'] = build_invoice_number(discharge_details.id, discharge_details.releaseDate)
        return render(request, 'hospital/patient_final_bill.html', context=patient_context)
    
    return render(request, 'hospital/patient_generate_bill.html', context=patient_context)


def render_to_pdf(template_src, context_dict):
    """Chuyen doi HTML template sang PDF."""
    if template_src == 'hospital/download_bill.html':
        return render_invoice_pdf(context_dict)

    ensure_pdf_fonts_registered()
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    
    try:
        pdf = pisa.pisaDocument(io.BytesIO(html.encode('utf-8')), result, encoding='utf-8')
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
    except Exception as exc:
        return HttpResponse(f'Loi tao PDF: {exc}', status=500)
    
    return HttpResponse('Loi tao PDF', status=500)


@login_required(login_url='adminlogin')
def download_pdf_view(request, pk):
    """Tai xuong hoa don xuat vien PDF."""
    discharge_details = models.PatientDischargeDetails.objects.filter(patientId=pk).order_by('-id').first()
    
    if not discharge_details:
        return HttpResponse('Khong tim thay hoa don', status=404)
    
    # Permission check: chi admin hoac chinh benh nhan do moi duoc tai
    if not is_admin(request.user):
        try:
            patient = models.Patient.objects.get(id=pk)
            if patient.user_id != request.user.id:
                return HttpResponse('Ban khong co quyen tai hoa don nay', status=403)
        except models.Patient.DoesNotExist:
            return HttpResponse('Ban khong co quyen tai hoa don nay', status=403)
    
    context = {
        'patientName': discharge_details.patientName,
        'patientId': discharge_details.patientId,
        'invoiceNumber': build_invoice_number(discharge_details.id, discharge_details.releaseDate),
        'assignedDoctorName': discharge_details.assignedDoctorName,
        'address': discharge_details.address,
        'mobile': discharge_details.mobile,
        'symptoms': discharge_details.symptoms,
        'admitDate': discharge_details.admitDate,
        'releaseDate': discharge_details.releaseDate,
        'daySpent': discharge_details.daySpent,
        'roomChargePerDay': discharge_details.roomCharge // max(discharge_details.daySpent, 1),
        'medicineCost': discharge_details.medicineCost,
        'roomCharge': discharge_details.roomCharge,
        'doctorFee': discharge_details.doctorFee,
        'OtherCharge': discharge_details.OtherCharge,
        'total': discharge_details.total,
        'roomChargeDisplay': format_currency(discharge_details.roomCharge),
        'roomChargePerDayDisplay': format_currency(discharge_details.roomCharge // max(discharge_details.daySpent, 1)),
        'doctorFeeDisplay': format_currency(discharge_details.doctorFee),
        'medicineCostDisplay': format_currency(discharge_details.medicineCost),
        'otherChargeDisplay': format_currency(discharge_details.OtherCharge),
        'totalDisplay': format_currency(discharge_details.total),
    }

    response = render_to_pdf('hospital/download_bill.html', context)
    if response.status_code == 200:
        response['Content-Disposition'] = (
            f'attachment; filename="hoa-don-xuat-vien-{discharge_details.patientId}-{discharge_details.id}.pdf"'
        )
    return response


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
    appointments = models.Appointment.objects.filter(status=True).order_by('-appointmentDate', '-appointmentTime', '-id')
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
            appointment.appointmentTime = appointmentForm.cleaned_data['appointmentTime']
            # Handle appointmentDate - use form data if provided, otherwise use today
            appointment_date = request.POST.get('appointmentDate')
            if appointment_date:
                from datetime import datetime as dt
                appointment.appointmentDate = dt.strptime(appointment_date, '%Y-%m-%d').date()
            else:
                appointment.appointmentDate = date.today()
            appointment.save()
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Lịch hẹn đã được tạo thành công!',
                    'redirect': '/admin-view-appointment'
                })
            
            return redirect('admin-view-appointment')
    
    return render(request, 'hospital/admin_add_appointment.html', context=context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@ensure_csrf_cookie
def admin_approve_appointment_view(request):
    """Xem danh sach lich hen cho duyet."""
    appointments = models.Appointment.objects.filter(status=False).order_by('-appointmentDate', '-appointmentTime', '-id')
    return render(request, 'hospital/admin_approve_appointment.html', {'appointments': appointments})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request, pk):
    """Chap nhan lich hen."""
    if request.method != 'POST':
        if is_ajax(request):
            return JsonResponse({
                'success': False,
                'message': 'Chi ho tro duyet lich hen bang POST.'
            }, status=405)
        return redirect('admin-approve-appointment')

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
    if request.method not in {'POST', 'DELETE'}:
        if is_ajax(request):
            return JsonResponse({
                'success': False,
                'message': 'Chi ho tro tu choi lich hen bang POST hoac DELETE.'
            }, status=405)
        return redirect('admin-approve-appointment')

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
    
    patientcount = models.Patient.objects.filter(
        status=True,
        assignedDoctorId=request.user.id,
        treatment_status='under_treatment',
    ).count()
    appointmentcount = models.Appointment.objects.filter(doctorId=request.user.id).count()
    patientdischarged = models.PatientDischargeDetails.objects.filter(
        assignedDoctorName=request.user.first_name
    ).distinct().count()
    
    appointments_qs = models.Appointment.objects.filter(
        doctorId=request.user.id
    ).order_by('-appointmentDate', '-appointmentTime', '-id')[:10]
    
    patients_list = list(
        models.Patient.objects.filter(
            status=True,
            assignedDoctorId=request.user.id,
            treatment_status='under_treatment',
        ).order_by('-id')[:10]
    )
    
    context = {
        'patientcount': patientcount,
        'appointmentcount': appointmentcount,
        'patientdischarged': patientdischarged,
        'appointments': pair_appointments_with_patients(appointments_qs),
        'patients': patients_list,
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
    patients = models.Patient.objects.filter(
        status=True,
        assignedDoctorId=request.user.id,
        treatment_status='under_treatment',
    )
    return render(request, 'hospital/doctor_view_patient.html', {'patients': patients, 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    """Tim kiem benh nhan."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    query = request.GET.get('query', '').strip()
    
    patients = models.Patient.objects.filter(
        status=True,
        assignedDoctorId=request.user.id,
        treatment_status='under_treatment',
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
    """Xem lich hen cua bac si (ca cho duyet va da xac nhan)."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    appointments_qs = models.Appointment.objects.filter(
        doctorId=request.user.id
    ).order_by('-appointmentDate', '-appointmentTime', '-id')
    rows = pair_appointments_with_patients(appointments_qs)
    return render(request, 'hospital/doctor_view_appointment.html',
                  {'appointments': rows, 'doctor': doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    """Trang lich su benh nhan da tung dat lich voi bac si."""
    doctor = get_object_or_404(models.Doctor, user_id=request.user.id)
    history_rows = build_doctor_patient_history(request.user.id)
    return render(request, 'hospital/doctor_delete_appointment.html',
                  {
                      'history_rows': history_rows,
                      'doctor': doctor,
                      'total_appointments': sum(row['total_appointments'] for row in history_rows),
                      'confirmed_appointments': sum(row['confirmed_count'] for row in history_rows),
                      'pending_appointments': sum(row['pending_count'] for row in history_rows),
                      'forbidden': request.GET.get('forbidden') == '1',
                  })


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request, pk):
    """Bac si khong duoc xoa lich hen tu giao dien nay nua."""
    if is_ajax(request):
        return JsonResponse({
            'success': False,
            'message': 'Bac si khong co quyen xoa lich hen.'
        }, status=403)

    return redirect(f"{reverse('doctor-delete-appointment')}?forbidden=1")


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
def patient_profile_view(request):
    """Xem va cap nhat ho so ca nhan cua benh nhan."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    user = patient.user

    if request.method == 'POST':
        userForm = forms.PatientProfileUserForm(request.POST, instance=user)
        patientForm = forms.PatientProfileForm(request.POST, request.FILES, instance=patient)

        if userForm.is_valid() and patientForm.is_valid():
            userForm.save()
            patientForm.save()

            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Há»“ sÆ¡ cÃ¡ nhÃ¢n Ä‘Ã£ Ä‘Æ°á»£c cáº­p nháº­t.',
                    'redirect': '/patient-profiles?updated=1'
                })

            return redirect('/patient-profiles?updated=1')
    else:
        userForm = forms.PatientProfileUserForm(instance=user)
        patientForm = forms.PatientProfileForm(instance=patient)

    assigned_doctor = models.Doctor.objects.filter(user_id=patient.assignedDoctorId).first()

    context = {
        'patient': patient,
        'userForm': userForm,
        'patientForm': patientForm,
        'assignedDoctor': assigned_doctor,
        'updated': request.GET.get('updated') == '1',
    }
    return render(request, 'hospital/patient_profiles.html', context=context)


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
            doctor = appointmentForm.cleaned_data['doctorId']
            appointment = appointmentForm.save(commit=False)
            appointment.doctorId = doctor.user_id
            appointment.patientId = request.user.id
            appointment.doctorName = doctor.get_name
            appointment.patientName = patient.get_name
            appointment.status = False
            appointment.appointmentTime = appointmentForm.cleaned_data['appointmentTime']
            # Handle appointmentDate - use form data if provided, otherwise use today
            appointment_date = request.POST.get('appointmentDate')
            if appointment_date:
                from datetime import datetime as dt
                appointment.appointmentDate = dt.strptime(appointment_date, '%Y-%m-%d').date()
            else:
                appointment.appointmentDate = date.today()
            appointment.save()
            
            if is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Lịch hẹn đã được đặt thành công! Vui lòng chờ bác sĩ xác nhận.',
                    'redirect': '/patient-view-appointment'
                })
            
            return redirect('patient-view-appointment')
        context['appointmentForm'] = appointmentForm
    
    return render(request, 'hospital/patient_book_appointment.html', context=context)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_doctor_view(request):
    """Xem danh sach bac si."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    doctors = models.Doctor.objects.filter(status=True)
    return render(request, 'hospital/patient_view_doctor.html', 
                  {'patient': patient, 'doctors': doctors})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def search_doctor_view(request):
    """Tim kiem bac si."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    query = request.GET.get('query', '').strip()

    doctors = models.Doctor.objects.filter(status=True).select_related('user')
    if query:
        for term in query.split():
            doctors = doctors.filter(
                Q(department__icontains=term)
                | Q(user__first_name__icontains=term)
                | Q(user__last_name__icontains=term)
                | Q(user__username__icontains=term)
                | Q(mobile__icontains=term)
                | Q(address__icontains=term)
            )
    doctors = doctors.distinct()

    return render(request, 'hospital/patient_view_doctor.html', 
                  {'patient': patient, 'doctors': doctors})


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    """Xem lich hen cua benh nhan."""
    patient = get_object_or_404(models.Patient, user_id=request.user.id)
    appointments = models.Appointment.objects.filter(
        patientId=request.user.id
    ).order_by('-appointmentDate', '-appointmentTime', '-id')
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
    return render(request, 'hospital/contactus.html')
