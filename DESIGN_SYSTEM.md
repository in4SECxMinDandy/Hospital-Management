# Hospital Management - Design System
*Generated: 2026-04-07 | Framework: Streamlit + Django REST API*

## Executive Summary

Thiết kế hệ thống Hospital Management với giao diện **100% Python** sử dụng Streamlit. Lấy cảm hứng từ **"Clinical Clarity"** - thiết kế tập trung vào sự rõ ràng, chuyên nghiệp và dễ sử dụng trong môi trường y tế.

## Visual Direction

### Theme: "Clinical Clarity"

```
┌─────────────────────────────────────────────────────────────┐
│  Màu sắc chủ đạo: Deep Teal (#0D9488)                     │
│  Accent: Emerald (#10B981)                                 │
│  Background: Slate (#F8FAFC)                               │
│  Text: Slate-900 (#0F172A)                                  │
│  Border: Slate-200 (#E2E8F0)                               │
└─────────────────────────────────────────────────────────────┘
```

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Dashboard Title | Inter | 32px | 700 |
| Card Title | Inter | 20px | 600 |
| Body Text | Inter | 16px | 400 |
| Caption | Inter | 14px | 400 |
| Button | Inter | 14px | 500 |

### Color Palette

```
Primary:      #0D9488 (Teal-600)     - Nút chính, sidebar
Primary Dark: #0F766E (Teal-700)     - Hover states
Success:      #10B981 (Emerald-500)  - Trạng thái thành công
Warning:      #F59E0B (Amber-500)    - Cảnh báo, chờ duyệt
Danger:       #EF4444 (Red-500)      - Lỗi, xóa
Info:         #3B82F6 (Blue-500)    - Thông tin
Background:   #F8FAFC (Slate-50)     - Nền chính
Surface:      #FFFFFF (White)        - Card, panel
Border:       #E2E8F0 (Slate-200)   - Viền, divider
Text:         #0F172A (Slate-900)   - Văn bản chính
Text Muted:   #64748B (Slate-500)    - Văn bản phụ
```

### Spacing System

```
xs: 4px   - Padding nhỏ
sm: 8px   - Spacing giữa items
md: 16px  - Padding chuẩn
lg: 24px  - Gap giữa sections
xl: 32px  - Margin ngoài
2xl: 48px - Spacing lớn
```

## Component Library

### 1. Stat Card

```python
┌──────────────────────────────┐
│  [Icon]                      │
│                              │
│  42                          │  ← Value (32px, bold)
│  Tổng Bác sĩ                 │  ← Label (14px, muted)
│  3 chờ duyệt                 │  ← Subtext (12px, warning)
└──────────────────────────────┘
```

### 2. Data Table

```
┌──────────────────────────────────────────────────────────────┐
│  [Search Icon] ___________________________ [Filter] [Add]   │
├──────────────────────────────────────────────────────────────┤
│  Tên          │  Khoa        │  Liên hệ    │  Thao tác     │
├───────────────┼──────────────┼─────────────┼───────────────┤
│  Dr. Nguyễn   │  Tim mạch    │  0912...    │  [Edit][Delete│
│  Dr. Trần     │  Thần kinh   │  0934...    │  [Edit][Delete│
└──────────────────────────────────────────────────────────────┘
```

### 3. Sidebar Navigation

```
┌──────────────────────────────────────────────────────────────┐
│  🏥 Hospital Pro                                           │
│  ─────────────────────────────────                          │
│  Tổng quan                                                  │
│  📊 Dashboard                                              │
│                                                              │
│  Quản lý                                                    │
│  👨‍⚕️ Bác sĩ (3)                                            │
│  👥 Bệnh nhân (12)                                          │
│  📅 Lịch hẹn (5)                                           │
│                                                              │
│  ─────────────────────────────────                          │
│  [Avatar] Dr. Nguyễn Văn A                                 │
│  [Logout]                                                   │
└──────────────────────────────────────────────────────────────┘
```

## Key Pages

### 1. Login Page

- Logo + Hospital name
- Role selector (Admin/Doctor/Patient)
- Username + Password fields
- Login button with loading state
- Hospital-themed background

### 2. Admin Dashboard

- 4 stat cards (Doctors, Patients, Appointments, Pending)
- Recent activity table
- Quick action buttons
- Pending approvals sidebar

### 3. Doctor Dashboard

- Patient count + appointment count
- Today's appointments list
- Patient list quick view
- Notifications

### 4. Patient Dashboard

- Assigned doctor info
- Appointment history
- Book appointment button
- Discharge status

## Animation & Motion

| Animation | Duration | Easing |
|-----------|----------|--------|
| Page transition | 300ms | ease-in-out |
| Hover state | 150ms | ease |
| Modal open | 200ms | ease-out |
| Loading spinner | 1000ms | linear |

## Accessibility

- Color contrast ratio: 4.5:1 minimum
- Focus states: 2px solid ring
- Font sizes: minimum 12px
- Touch targets: minimum 44px

## Technical Implementation

### Streamlit Config

```toml
[theme]
primaryColor = "#0D9488"
backgroundColor = "#F8FAFC"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#0F172A"
font = "sans serif"
```

### File Structure

```
streamlit_app/
├── main.py                 # Entry point
├── pages/                  # Multi-page navigation
│   ├── 1_🔐_Login.py
│   ├── 2_📊_Dashboard.py
│   ├── 3_👨‍⚕️_Doctors.py
│   ├── 4_👥_Patients.py
│   ├── 5_📅_Appointments.py
│   └── 6_💳_Billing.py
├── components/             # Reusable UI components
│   ├── cards.py
│   ├── tables.py
│   ├── forms.py
│   └── navigation.py
├── services/              # API client & business logic
│   ├── api.py
│   └── auth.py
├── styles/               # Custom CSS
│   └── custom.css
└── utils/                # Utilities
    └── helpers.py
```
