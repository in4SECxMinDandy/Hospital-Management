# Hospital Management System

A Django-based hospital management system with role-based dashboards for administrators, doctors, and patients. The current codebase combines:

- server-rendered Django pages for the main product UI
- Django REST Framework endpoints for API access and future integrations
- SQLite for local persistence
- PDF discharge bill generation with Vietnamese-friendly output
- Docker and GitHub Actions scaffolding for deployment and CI work

This repository has been updated beyond the original tutorial-style version. It now includes patient treatment-state tracking, richer admin workflows, AJAX-based actions, a larger automated test suite, and a REST API layer.

## Current Highlights

- Django 4.2 style dependency set in [`requirements.txt`](requirements.txt)
- Role-based web flows for `ADMIN`, `DOCTOR`, and `PATIENT`
- REST API under `/api/` for auth, admin, doctor, and patient operations
- Appointment booking with explicit business-hour time slots
- Admin approval flow for appointments using CSRF-safe AJAX `POST`
- Patient treatment lifecycle with `under_treatment` and `treated`
- Separate admin views for active patients and treated/history patients
- Patient self-profile page and matching profile API
- Discharge billing flow with invoice numbers and downloadable PDF bills
- Expanded tests for permissions, billing, patient status changes, API-related behavior, and appointment workflows

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Django |
| API | Django REST Framework |
| Templates | Django Templates + `django-widget-tweaks` |
| Database | SQLite |
| PDF | `xhtml2pdf` + ReportLab font registration helper |
| Test tools | Django test runner, `pytest`, `pytest-django` |
| Quality tools | `ruff`, `bandit`, `safety` |
| Container | Docker, Docker Compose |

Recommended local Python version: `3.10+`.

The included Docker image uses `python:3.12-slim`.

## Architecture

```text
Browser
  -> Django template views
  -> AJAX actions via static/js/clinic.js
  -> Django ORM
  -> SQLite

API clients
  -> /api/*
  -> Django REST Framework views + serializers
  -> Django ORM
  -> SQLite
```

Main application areas:

- [`hospital/views.py`](hospital/views.py): main web application logic
- [`hospital/api.py`](hospital/api.py): REST API endpoints
- [`hospital/forms.py`](hospital/forms.py): web form validation
- [`hospital/serializers.py`](hospital/serializers.py): API serializers
- [`hospital/models.py`](hospital/models.py): doctor, patient, appointment, discharge models
- [`templates/hospital/`](templates/hospital): role-based HTML templates
- [`static/js/clinic.js`](static/js/clinic.js): AJAX helpers, confirmation dialogs, toasts

## Roles and Permissions

### Administrator

Admins can:

- access the admin dashboard
- create, update, approve, and remove doctors
- add and update patients
- view active patients and treated patients separately
- create, view, approve, or reject appointments
- discharge patients and generate bills
- download PDF discharge invoices
- access admin REST endpoints

### Doctor

Doctors can:

- sign up and log in
- wait for approval if their account is not approved
- see dashboard counts and assigned patients
- view their own appointment list
- access a patient-history style appointment page
- use doctor REST endpoints for dashboard and patient data

Note:

- the old doctor appointment deletion route is retained for compatibility, but the current UX treats that page as history-oriented rather than as a destructive delete workflow

### Patient

Patients can:

- sign up and log in
- update their own profile
- view assigned doctor information
- browse/search available doctors
- book appointments
- see their own appointment list and appointment status
- view discharge details and download their own bill PDF
- access patient REST endpoints for dashboard, profile, doctors, and booking

Important behavior in the current version:

- patient sign-up is auto-activated in the current implementation
- patient approval routes are kept mainly for backward compatibility and redirect to the normal patient list workflow

## Domain Model

### Doctor

Fields include:

- linked Django `User`
- profile picture
- address and mobile
- department
- schedule/fee/profile metadata fields
- approval status

### Patient

Fields include:

- linked Django `User`
- profile picture
- contact information
- symptoms
- assigned doctor id
- admit date
- approval status
- `treatment_status`

Current treatment states:

- `under_treatment`
- `treated`

### Appointment

Fields include:

- `patientId`
- `doctorId`
- `patientName`
- `doctorName`
- `appointmentDate`
- `appointmentTime`
- `description`
- `status`

Configured appointment slots:

- `08:00`
- `09:00`
- `10:00`
- `11:00`
- `13:00`
- `14:00`
- `15:00`
- `16:00`

### PatientDischargeDetails

Stores generated discharge billing data:

- patient and doctor summary
- admit/release dates
- days spent
- room charge
- medicine cost
- doctor fee
- other charges
- total bill

## Web Features

### Admin workflows

- Dashboard with doctor, patient, treated-patient, and appointment counts
- Doctor management pages
- Patient management pages
- Separate treated-patient history page at `/admin-treated-patient`
- Appointment management with AJAX-based approval/rejection
- Discharge and bill generation workflow

### Patient status split

One of the notable updates in this project is the separation of patient lists:

- `/admin-view-patient` for active patients under treatment
- `/admin-treated-patient` for treated/history patients

When a patient is discharged, the system moves that patient to `treated`.

### Billing and PDF output

The discharge flow now includes:

- sanitized charge parsing
- invoice number generation
- consistent bill context building
- PDF rendering with Unicode-aware font registration
- bill download access restricted to admins or the matching patient

### Appointment approval fix

The admin appointment approval page now uses a CSRF-safe AJAX flow:

- page sets the CSRF cookie
- approval uses `POST`
- rejection accepts `DELETE` or `POST`
- test coverage exists for this workflow

## REST API Overview

Base prefix: `/api/`

Response pattern is generally:

```json
{
  "success": true,
  "data": {},
  "message": "Optional message"
}
```

### Auth endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/login/` | Role-aware login response |
| `POST` | `/api/auth/logout/` | Logout response |

### Admin endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/admin/dashboard/` | Dashboard metrics |
| `GET,POST` | `/api/admin/doctors/` | List or create doctors |
| `GET,PUT,DELETE` | `/api/admin/doctors/<id>/` | Doctor detail |
| `POST` | `/api/admin/doctors/<id>/approve/` | Approve doctor |
| `GET,POST` | `/api/admin/patients/` | List or create patients |
| `GET,PUT,DELETE` | `/api/admin/patients/<id>/` | Patient detail |
| `POST` | `/api/admin/patients/<id>/approve/` | Legacy-compatible patient approval route |
| `GET,POST` | `/api/admin/appointments/` | List or create appointments |
| `DELETE` | `/api/admin/appointments/<id>/` | Remove appointment |
| `POST` | `/api/admin/appointments/<id>/approve/` | Approve appointment |
| `GET,POST` | `/api/admin/discharge/` | Discharge helpers |
| `GET,POST` | `/api/admin/discharge/<id>/` | Discharge a specific patient |

### Doctor endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/doctor/dashboard/` | Doctor metrics |
| `GET` | `/api/doctor/patients/` | Assigned patients |

### Patient endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/patient/dashboard/` | Patient dashboard data |
| `GET,PUT,PATCH` | `/api/patient/profile/` | Patient profile |
| `GET` | `/api/patient/doctors/` | Available doctors |
| `POST` | `/api/patient/book-appointment/` | Book appointment |

## Local Setup

### 1. Clone the project

```bash
git clone <your-repo-url>
cd "Hospital-Management new"
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` if needed. Supported settings include:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_RECEIVING_USER=
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create sample accounts

```bash
python manage.py create_test_users
```

Default accounts created by the command:

- `admin / admin123`
- `doctor / doctor123`
- `patient / patient123`

### 7. Run the development server

```bash
python manage.py runserver
```

Open:

- `http://127.0.0.1:8000/`

## Docker

Build and run with Docker Compose:

```bash
docker-compose up --build
```

Services currently included:

- `django` on port `8000`
- `redis` on port `6379`

Note:

- Redis is provisioned in Compose, but the current business logic is still centered on Django + SQLite

## Testing

### Django test suite

```bash
python manage.py test hospital.tests -v
```

### Pytest

```bash
pytest hospital/tests.py -v
```

### Lint and security checks

```bash
ruff check .
bandit -r hospital
safety check
```

Current local regression status at the time of the latest update:

- full `hospital.tests` suite passes
- appointment approval AJAX flow is covered
- patient treated/history split is covered
- PDF billing behavior is covered

## Project Structure

```text
.
|-- hospital/
|   |-- admin.py
|   |-- api.py
|   |-- api_urls.py
|   |-- forms.py
|   |-- management/
|   |   `-- commands/
|   |       `-- create_test_users.py
|   |-- migrations/
|   |-- models.py
|   |-- serializers.py
|   |-- tests.py
|   `-- views.py
|-- hospitalmanagement/
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|-- static/
|   |-- images/
|   |-- js/
|   `-- style.css
|-- templates/
|   `-- hospital/
|-- .github/
|   `-- workflows/
|-- Dockerfile
|-- docker-compose.yml
|-- manage.py
|-- pytest.ini
|-- requirements.txt
`-- README.md
```

Template inventory currently contains 60+ role-based pages, including:

- public pages
- admin dashboards and CRUD pages
- doctor dashboard, patient, and appointment views
- patient dashboard, profile, booking, and discharge views

## Notable Updated Routes

### Web routes

- `/admin-dashboard`
- `/admin-view-patient`
- `/admin-treated-patient`
- `/admin-approve-appointment`
- `/doctor-dashboard`
- `/doctor-delete-appointment`
- `/patient-dashboard`
- `/patient-profiles`
- `/patient-book-appointment`
- `/patient-view-appointment`
- `/patient-discharge`

### Utility routes

- `/download-pdf/<patient_id>`
- `/search`
- `/searchdoctor`

## GitHub Actions

The repository includes a CI/CD workflow at [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml).

It currently provides a useful starting point for:

- linting
- Django tests
- Docker image builds

Note:

- some workflow jobs still reference Streamlit-related steps from an earlier direction of the project and should be aligned further if you want a fully production-ready CI pipeline for the current repository

## Known Notes

- SQLite is the default database in this repository
- media files are currently stored under the static/media-style setup used by this project
- the REST login endpoint returns a simple demo token string rather than a production auth token system such as JWT
- some legacy routes are intentionally preserved for compatibility with earlier templates and links

## Roadmap Ideas

- move from simple token placeholders to JWT/session API auth strategy
- normalize foreign-key-like integer references such as `assignedDoctorId`, `doctorId`, and `patientId`
- separate media storage from static assets
- align GitHub Actions fully with the current Django-only repository shape
- add pagination and filtering for larger admin datasets
- add richer API authentication and OpenAPI documentation

## License

This project is distributed under the MIT License. See [`LICENSE`](LICENSE).
