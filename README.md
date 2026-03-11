# PlaceWise — Campus Placement Portal
## MAD 1 Project | IITM BS Programme

A full-featured campus placement portal built with Flask + Jinja2 + Bootstrap + SQLite.

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000
```

---

## Default Admin Credentials
| Field    | Value                     |
|----------|---------------------------|
| Role     | Admin                     |
| Email    | admin@placement.edu       |
| Password | admin123                  |

---

## Project Structure
```
placement_portal/
├── app.py                  # Main Flask application
├── database.py             # DB init & helper
├── requirements.txt
├── placement_portal.db     # Auto-created on first run
├── templates/
│   ├── base.html           # Shared layout, navbar, sidebar
│   ├── index.html          # Landing page
│   ├── login.html
│   ├── register_student.html
│   ├── register_company.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── companies.html
│   │   ├── students.html
│   │   ├── drives.html
│   │   └── applications.html
│   ├── company/
│   │   ├── dashboard.html
│   │   ├── create_drive.html
│   │   ├── edit_drive.html
│   │   └── applications.html
│   └── student/
│       ├── dashboard.html
│       ├── profile.html
│       └── history.html
└── static/
    └── uploads/
        └── resumes/        # Uploaded student resumes
```

---

## Features Implemented

### Admin
- Dashboard with live stats (students, companies, drives, applications)
- Approve / Reject company registrations
- Approve / Reject placement drives  
- Blacklist / Activate / Delete students
- Blacklist / Activate / Delete companies
- Search students by name, ID, phone
- Search companies by name
- View all applications (historical data)

### Company
- Register + await admin approval
- Dashboard with drives and applicant counts
- Create / Edit / Delete / Close placement drives
- View all applicants per drive with student details
- Update application status (Applied → Shortlisted → Selected / Rejected)

### Student
- Register and login
- Dashboard showing available drives and application statuses
- Apply for approved drives (duplicate prevention enforced)
- View and edit profile
- Upload resume (PDF/DOC)
- View full placement history

---

## Tech Stack
- **Backend**: Flask (Python)
- **Frontend**: Jinja2, HTML5, Bootstrap 5
- **Database**: SQLite (programmatic creation, no DB Browser)
- **Fonts**: Syne (headings) + DM Sans (body) via Google Fonts
- **Icons**: Bootstrap Icons CDN

---

## Notes
- Database is created automatically on first `python app.py` run
- Admin is pre-seeded — no admin registration allowed
- Only approved companies can create drives
- Only approved drives are visible to students
- JS is used only for flash message auto-dismiss (non-core feature)
