from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, get_db
import hashlib
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'placement_portal_secret_2024'

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'company':
            return redirect(url_for('company_dashboard'))
        elif role == 'student':
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        db = get_db()

        if role == 'admin':
            admin = db.execute('SELECT * FROM admins WHERE email=? AND password=?',
                               (email, hash_password(password))).fetchone()
            if admin:
                session['user_id'] = admin['id']
                session['role'] = 'admin'
                session['name'] = admin['name']
                return redirect(url_for('admin_dashboard'))

        elif role == 'company':
            company = db.execute('SELECT * FROM companies WHERE email=? AND password=?',
                                 (email, hash_password(password))).fetchone()
            if company:
                if company['status'] == 'blacklisted':
                    flash('Your account has been blacklisted.', 'danger')
                    return redirect(url_for('login'))
                if company['status'] != 'approved':
                    flash('Your registration is pending admin approval.', 'warning')
                    return redirect(url_for('login'))
                session['user_id'] = company['id']
                session['role'] = 'company'
                session['name'] = company['company_name']
                return redirect(url_for('company_dashboard'))

        elif role == 'student':
            student = db.execute('SELECT * FROM students WHERE email=? AND password=?',
                                 (email, hash_password(password))).fetchone()
            if student:
                if student['status'] == 'blacklisted':
                    flash('Your account has been blacklisted.', 'danger')
                    return redirect(url_for('login'))
                if student['status'] != 'active':
                    flash('Your account is inactive.', 'warning')
                    return redirect(url_for('login'))
                session['user_id'] = student['id']
                session['role'] = 'student'
                session['name'] = student['name']
                return redirect(url_for('student_dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ─── REGISTRATION ────────────────────────────────────────────────────────────

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa', '0')
        graduation_year = request.form.get('graduation_year', '').strip()

        if not all([name, email, password, phone, department]):
            flash('All required fields must be filled.', 'danger')
            return render_template('register_student.html')

        db = get_db()
        existing = db.execute('SELECT id FROM students WHERE email=?', (email,)).fetchone()
        if existing:
            flash('Email already registered.', 'danger')
            return render_template('register_student.html')

        try:
            cgpa = float(cgpa)
        except:
            cgpa = 0.0

        db.execute('''INSERT INTO students (name, email, password, phone, department, cgpa, graduation_year, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, 'active')''',
                   (name, email, hash_password(password), phone, department, cgpa, graduation_year))
        db.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_student.html')

@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        hr_contact = request.form.get('hr_contact', '').strip()
        website = request.form.get('website', '').strip()
        industry = request.form.get('industry', '').strip()
        description = request.form.get('description', '').strip()

        if not all([company_name, email, password, hr_contact]):
            flash('All required fields must be filled.', 'danger')
            return render_template('register_company.html')

        db = get_db()
        existing = db.execute('SELECT id FROM companies WHERE email=?', (email,)).fetchone()
        if existing:
            flash('Email already registered.', 'danger')
            return render_template('register_company.html')

        db.execute('''INSERT INTO companies (company_name, email, password, hr_contact, website, industry, description, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')''',
                   (company_name, email, hash_password(password), hr_contact, website, industry, description))
        db.commit()
        flash('Registration submitted! Await admin approval before logging in.', 'info')
        return redirect(url_for('login'))
    return render_template('register_company.html')

# ─── ADMIN ───────────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    db = get_db()
    stats = {
        'students': db.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'companies': db.execute("SELECT COUNT(*) FROM companies WHERE status='approved'").fetchone()[0],
        'drives': db.execute('SELECT COUNT(*) FROM placement_drives').fetchone()[0],
        'applications': db.execute('SELECT COUNT(*) FROM applications').fetchone()[0],
        'pending_companies': db.execute("SELECT COUNT(*) FROM companies WHERE status='pending'").fetchone()[0],
        'pending_drives': db.execute("SELECT COUNT(*) FROM placement_drives WHERE status='pending'").fetchone()[0],
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/companies')
@login_required('admin')
def admin_companies():
    db = get_db()
    search = request.args.get('search', '').strip()
    if search:
        companies = db.execute("SELECT * FROM companies WHERE company_name LIKE ? OR id LIKE ?",
                               (f'%{search}%', f'%{search}%')).fetchall()
    else:
        companies = db.execute('SELECT * FROM companies ORDER BY created_at DESC').fetchall()
    return render_template('admin/companies.html', companies=companies, search=search)

@app.route('/admin/company/<int:cid>/action', methods=['POST'])
@login_required('admin')
def admin_company_action(cid):
    action = request.form.get('action')
    db = get_db()
    status_map = {'approve': 'approved', 'reject': 'rejected', 'blacklist': 'blacklisted', 'activate': 'approved'}
    if action in status_map:
        db.execute('UPDATE companies SET status=? WHERE id=?', (status_map[action], cid))
        db.commit()
        flash(f'Company status updated to {status_map[action]}.', 'success')
    elif action == 'delete':
        db.execute('DELETE FROM companies WHERE id=?', (cid,))
        db.commit()
        flash('Company deleted.', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/students')
@login_required('admin')
def admin_students():
    db = get_db()
    search = request.args.get('search', '').strip()
    if search:
        students = db.execute("SELECT * FROM students WHERE name LIKE ? OR id LIKE ? OR phone LIKE ?",
                              (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        students = db.execute('SELECT * FROM students ORDER BY created_at DESC').fetchall()
    return render_template('admin/students.html', students=students, search=search)

@app.route('/admin/student/<int:sid>/action', methods=['POST'])
@login_required('admin')
def admin_student_action(sid):
    action = request.form.get('action')
    db = get_db()
    if action == 'blacklist':
        db.execute("UPDATE students SET status='blacklisted' WHERE id=?", (sid,))
        db.commit()
        flash('Student blacklisted.', 'success')
    elif action == 'activate':
        db.execute("UPDATE students SET status='active' WHERE id=?", (sid,))
        db.commit()
        flash('Student activated.', 'success')
    elif action == 'delete':
        db.execute('DELETE FROM students WHERE id=?', (sid,))
        db.commit()
        flash('Student deleted.', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/drives')
@login_required('admin')
def admin_drives():
    db = get_db()
    drives = db.execute('''SELECT pd.*, c.company_name,
                           (SELECT COUNT(*) FROM applications WHERE drive_id=pd.id) as app_count
                           FROM placement_drives pd
                           JOIN companies c ON pd.company_id=c.id
                           ORDER BY pd.created_at DESC''').fetchall()
    return render_template('admin/drives.html', drives=drives)

@app.route('/admin/drive/<int:did>/action', methods=['POST'])
@login_required('admin')
def admin_drive_action(did):
    action = request.form.get('action')
    db = get_db()
    if action == 'approve':
        db.execute("UPDATE placement_drives SET status='approved' WHERE id=?", (did,))
        db.commit()
        flash('Drive approved.', 'success')
    elif action == 'reject':
        db.execute("UPDATE placement_drives SET status='rejected' WHERE id=?", (did,))
        db.commit()
        flash('Drive rejected.', 'success')
    elif action == 'delete':
        db.execute('DELETE FROM placement_drives WHERE id=?', (did,))
        db.commit()
        flash('Drive deleted.', 'success')
    return redirect(url_for('admin_drives'))

@app.route('/admin/applications')
@login_required('admin')
def admin_applications():
    db = get_db()
    applications = db.execute('''SELECT a.*, s.name as student_name, pd.job_title, c.company_name
                                 FROM applications a
                                 JOIN students s ON a.student_id=s.id
                                 JOIN placement_drives pd ON a.drive_id=pd.id
                                 JOIN companies c ON pd.company_id=c.id
                                 ORDER BY a.applied_at DESC''').fetchall()
    return render_template('admin/applications.html', applications=applications)

# ─── COMPANY ─────────────────────────────────────────────────────────────────

@app.route('/company/dashboard')
@login_required('company')
def company_dashboard():
    db = get_db()
    cid = session['user_id']
    company = db.execute('SELECT * FROM companies WHERE id=?', (cid,)).fetchone()
    drives = db.execute('''SELECT pd.*,
                           (SELECT COUNT(*) FROM applications WHERE drive_id=pd.id) as app_count
                           FROM placement_drives pd WHERE company_id=? ORDER BY created_at DESC''', (cid,)).fetchall()
    return render_template('company/dashboard.html', company=company, drives=drives)

@app.route('/company/drives/create', methods=['GET', 'POST'])
@login_required('company')
def company_create_drive():
    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        deadline = request.form.get('deadline', '').strip()
        location = request.form.get('location', '').strip()
        package = request.form.get('package', '').strip()
        vacancies = request.form.get('vacancies', '1')

        if not all([job_title, job_description, deadline]):
            flash('Please fill all required fields.', 'danger')
            return render_template('company/create_drive.html')

        db = get_db()
        db.execute('''INSERT INTO placement_drives (company_id, job_title, job_description, eligibility,
                      deadline, location, package, vacancies, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')''',
                   (session['user_id'], job_title, job_description, eligibility,
                    deadline, location, package, vacancies))
        db.commit()
        flash('Drive created and sent for admin approval.', 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('company/create_drive.html')

@app.route('/company/drives/<int:did>/edit', methods=['GET', 'POST'])
@login_required('company')
def company_edit_drive(did):
    db = get_db()
    drive = db.execute('SELECT * FROM placement_drives WHERE id=? AND company_id=?',
                       (did, session['user_id'])).fetchone()
    if not drive:
        flash('Drive not found.', 'danger')
        return redirect(url_for('company_dashboard'))

    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        deadline = request.form.get('deadline', '').strip()
        location = request.form.get('location', '').strip()
        package = request.form.get('package', '').strip()
        vacancies = request.form.get('vacancies', '1')

        db.execute('''UPDATE placement_drives SET job_title=?, job_description=?, eligibility=?,
                      deadline=?, location=?, package=?, vacancies=?, status='pending'
                      WHERE id=?''',
                   (job_title, job_description, eligibility, deadline, location, package, vacancies, did))
        db.commit()
        flash('Drive updated and re-submitted for approval.', 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('company/edit_drive.html', drive=drive)

@app.route('/company/drives/<int:did>/delete', methods=['POST'])
@login_required('company')
def company_delete_drive(did):
    db = get_db()
    db.execute('DELETE FROM placement_drives WHERE id=? AND company_id=?', (did, session['user_id']))
    db.commit()
    flash('Drive deleted.', 'success')
    return redirect(url_for('company_dashboard'))

@app.route('/company/drives/<int:did>/close', methods=['POST'])
@login_required('company')
def company_close_drive(did):
    db = get_db()
    db.execute("UPDATE placement_drives SET status='closed' WHERE id=? AND company_id=?",
               (did, session['user_id']))
    db.commit()
    flash('Drive closed.', 'success')
    return redirect(url_for('company_dashboard'))

@app.route('/company/drives/<int:did>/applications')
@login_required('company')
def company_view_applications(did):
    db = get_db()
    drive = db.execute('SELECT * FROM placement_drives WHERE id=? AND company_id=?',
                       (did, session['user_id'])).fetchone()
    if not drive:
        flash('Drive not found.', 'danger')
        return redirect(url_for('company_dashboard'))
    applications = db.execute('''SELECT a.*, s.name, s.email, s.phone, s.department, s.cgpa, s.resume
                                 FROM applications a JOIN students s ON a.student_id=s.id
                                 WHERE a.drive_id=? ORDER BY a.applied_at DESC''', (did,)).fetchall()
    return render_template('company/applications.html', drive=drive, applications=applications)

@app.route('/company/application/<int:aid>/update', methods=['POST'])
@login_required('company')
def company_update_application(aid):
    status = request.form.get('status')
    db = get_db()
    app_rec = db.execute('''SELECT a.*, pd.company_id FROM applications a
                            JOIN placement_drives pd ON a.drive_id=pd.id WHERE a.id=?''', (aid,)).fetchone()
    if not app_rec or app_rec['company_id'] != session['user_id']:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company_dashboard'))
    if status in ['shortlisted', 'selected', 'rejected']:
        db.execute('UPDATE applications SET status=? WHERE id=?', (status, aid))
        db.commit()
        flash(f'Application status updated to {status}.', 'success')
    return redirect(url_for('company_view_applications', did=app_rec['drive_id']))

# ─── STUDENT ─────────────────────────────────────────────────────────────────

@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    db = get_db()
    sid = session['user_id']
    student = db.execute('SELECT * FROM students WHERE id=?', (sid,)).fetchone()
    approved_drives = db.execute('''SELECT pd.*, c.company_name
                                    FROM placement_drives pd JOIN companies c ON pd.company_id=c.id
                                    WHERE pd.status='approved'
                                    AND pd.id NOT IN (SELECT drive_id FROM applications WHERE student_id=?)
                                    ORDER BY pd.created_at DESC''', (sid,)).fetchall()
    my_applications = db.execute('''SELECT a.*, pd.job_title, c.company_name
                                    FROM applications a
                                    JOIN placement_drives pd ON a.drive_id=pd.id
                                    JOIN companies c ON pd.company_id=c.id
                                    WHERE a.student_id=? ORDER BY a.applied_at DESC''', (sid,)).fetchall()
    return render_template('student/dashboard.html', student=student,
                           approved_drives=approved_drives, my_applications=my_applications)

@app.route('/student/apply/<int:did>', methods=['POST'])
@login_required('student')
def student_apply(did):
    db = get_db()
    sid = session['user_id']
    drive = db.execute("SELECT * FROM placement_drives WHERE id=? AND status='approved'", (did,)).fetchone()
    if not drive:
        flash('Drive not available.', 'danger')
        return redirect(url_for('student_dashboard'))
    existing = db.execute('SELECT id FROM applications WHERE student_id=? AND drive_id=?', (sid, did)).fetchone()
    if existing:
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('student_dashboard'))
    db.execute("INSERT INTO applications (student_id, drive_id, status) VALUES (?, ?, 'applied')", (sid, did))
    db.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required('student')
def student_profile():
    db = get_db()
    sid = session['user_id']
    student = db.execute('SELECT * FROM students WHERE id=?', (sid,)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa', '0')
        graduation_year = request.form.get('graduation_year', '').strip()
        skills = request.form.get('skills', '').strip()
        bio = request.form.get('bio', '').strip()

        try:
            cgpa = float(cgpa)
        except:
            cgpa = 0.0

        resume_filename = student['resume']
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"student_{sid}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                resume_filename = filename

        db.execute('''UPDATE students SET name=?, phone=?, department=?, cgpa=?, graduation_year=?,
                      skills=?, bio=?, resume=? WHERE id=?''',
                   (name, phone, department, cgpa, graduation_year, skills, bio, resume_filename, sid))
        db.commit()
        session['name'] = name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))

    return render_template('student/profile.html', student=student)

@app.route('/student/history')
@login_required('student')
def student_history():
    db = get_db()
    sid = session['user_id']
    history = db.execute('''SELECT a.*, pd.job_title, pd.location, pd.package, c.company_name
                            FROM applications a
                            JOIN placement_drives pd ON a.drive_id=pd.id
                            JOIN companies c ON pd.company_id=c.id
                            WHERE a.student_id=? ORDER BY a.applied_at DESC''', (sid,)).fetchall()
    return render_template('student/history.html', history=history)

if __name__ == '__main__':
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
