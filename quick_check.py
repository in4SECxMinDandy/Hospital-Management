
import os
import django
from django.contrib.auth import authenticate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospitalmanagement.settings')
django.setup()

from django.contrib.auth.models import User

def quick_check():
    users = [
        ('admin', 'admin123'),
        ('admin123@gmail.com', 'admin123'),
        ('doctor_cardio', 'doctor_cardio'),
        ('patient_1', 'patient_1'),
        ('doctor_cardio', 'hospital123'),
        ('patient_1', 'hospital123'),
    ]
    
    for u, p in users:
        user = authenticate(username=u, password=p)
        if user:
            print(f"Match: {u} / {p}")
        else:
            print(f"Fail: {u} / {p}")

if __name__ == "__main__":
    quick_check()
