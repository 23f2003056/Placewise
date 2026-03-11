import sqlite3
import hashlib
import os

DB_PATH = 'placement_portal.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            department TEXT,
            cgpa REAL DEFAULT 0.0,
            graduation_year TEXT,
            skills TEXT,
            bio TEXT,
            resume TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            hr_contact TEXT,
            website TEXT,
            industry TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS placement_drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            job_description TEXT,
            eligibility TEXT,
            deadline TEXT,
            location TEXT,
            package TEXT,
            vacancies INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            drive_id INTEGER NOT NULL,
            status TEXT DEFAULT 'applied',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, drive_id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (drive_id) REFERENCES placement_drives(id)
        );
    ''')

    # Create default admin if not exists
    admin_exists = db.execute('SELECT id FROM admins WHERE email=?', ('admin@placement.edu',)).fetchone()
    if not admin_exists:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        db.execute("INSERT INTO admins (name, email, password) VALUES (?, ?, ?)",
                   ('Super Admin', 'admin@placement.edu', admin_password))
        db.commit()
        print("Default admin created: admin@placement.edu / admin123")

    db.commit()
    print("Database initialized successfully.")
