import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "attendance.db"))

TURSO_DEFAULT_URL = "libsql://ssits-attendance-kamanurubasha-coder.aws-ap-south-1.turso.io"
TURSO_DEFAULT_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODk4MzM1NTYsImlkIjoiMDFhMGJhNjEtYWIwMS03OWY3LWFkYTEtOTE0NjNlYWRmOGUxIiwia2lkIjoiUkVvNHdUTDktS3VnSWhaMG15X1NDeks3MVVQYzZlTThXQlMtTi01X2Y2WSIsInJpZCI6IjZhNTk2MGU5LTBhZjQtNGUyMy1hMjM3LTEwMWQ1YzMzOGY1YiJ9.B-xFreuAjs80CqWjitoOHnbF6pAVu7E-ET8SjSUSex8mWYVjZok1gp9QrUhsu01hb1Evwn6UsQJx42h91dPKDw"

def get_db_connection():
    if os.getenv("USE_LOCAL_SQLITE") == "1":
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    turso_url = os.getenv("TURSO_DATABASE_URL", TURSO_DEFAULT_URL)
    turso_token = os.getenv("TURSO_AUTH_TOKEN", TURSO_DEFAULT_TOKEN)
    if turso_url and turso_token:
        try:
            from turso_client import TursoConnection
            return TursoConnection(turso_url, turso_token)
        except Exception as e:
            print(f"[WARN] Turso connection fallback to SQLite: {e}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fast-path check: If schema and superadmin already exist, skip redundant DDL statements
    try:
        cursor.execute("SELECT 1 FROM programs LIMIT 1")
        if cursor.fetchone():
            cursor.execute("SELECT 1 FROM admins WHERE role = 'superadmin' LIMIT 1")
            if cursor.fetchone():
                conn.close()
                return
    except Exception:
        pass

    # 1. Programs (Diploma & B.Tech)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            duration_years INTEGER NOT NULL
        )
    """)

    # 2. Departments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """)

    # 3. Mapping Programs to Departments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            FOREIGN KEY (program_id) REFERENCES programs(id),
            FOREIGN KEY (department_id) REFERENCES departments(id),
            UNIQUE(program_id, department_id)
        )
    """)

    # 4. Academic Years (1st, 2nd, 3rd, 4th)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_name TEXT NOT NULL,
            year_code TEXT UNIQUE NOT NULL,
            year_num INTEGER NOT NULL
        )
    """)

    # 5. HODs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            is_approved INTEGER DEFAULT 1,
            FOREIGN KEY (program_id) REFERENCES programs(id),
            FOREIGN KEY (department_id) REFERENCES departments(id),
            UNIQUE(program_id, department_id)
        )
    """)

    # 6. Teachers / Faculty
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            program_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            year_id INTEGER NOT NULL,
            section TEXT DEFAULT 'A',
            email TEXT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL,
            FOREIGN KEY (program_id) REFERENCES programs(id),
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (year_id) REFERENCES academic_years(id)
        )
    """)

    # 7. Students
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            program_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            year_id INTEGER NOT NULL,
            section TEXT DEFAULT 'A',
            father_name TEXT NOT NULL,
            father_phone TEXT NOT NULL,
            FOREIGN KEY (program_id) REFERENCES programs(id),
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (year_id) REFERENCES academic_years(id)
        )
    """)

    # 8. Attendance Records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            session_type TEXT NOT NULL,
            section TEXT DEFAULT 'A',
            status TEXT NOT NULL,
            marked_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (marked_by) REFERENCES teachers(id),
            UNIQUE(student_id, attendance_date, session_type)
        )
    """)

    # 9. Day Status & Holidays Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS day_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            year_id INTEGER NOT NULL,
            section TEXT DEFAULT 'A',
            attendance_date TEXT NOT NULL,
            day_type TEXT NOT NULL,
            occasion_name TEXT,
            marked_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs(id),
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (year_id) REFERENCES academic_years(id),
            FOREIGN KEY (marked_by) REFERENCES teachers(id)
        )
    """)

    # 10. Super Administrators Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT DEFAULT 'superadmin',
            is_approved INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 11. Email OTP Verifications Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_verified INTEGER DEFAULT 0
        )
    """)

    # 12. Password Resets Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_used INTEGER DEFAULT 0
        )
    """)

    # --- Schema Migrations for Existing Tables ---
    cursor.execute("PRAGMA table_info(teachers)")
    t_cols = [r[1] for r in cursor.fetchall()]
    if "email" not in t_cols:
        cursor.execute("ALTER TABLE teachers ADD COLUMN email TEXT")
    if "section" not in t_cols:
        cursor.execute("ALTER TABLE teachers ADD COLUMN section TEXT DEFAULT 'A'")

    cursor.execute("PRAGMA table_info(hods)")
    h_cols = [r[1] for r in cursor.fetchall()]
    if "username" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN username TEXT")
    if "password" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN password TEXT DEFAULT 'hod123'")
    if "email" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN email TEXT")

    cursor.execute("PRAGMA table_info(students)")
    s_cols = [r[1] for r in cursor.fetchall()]
    if "section" not in s_cols:
        cursor.execute("ALTER TABLE students ADD COLUMN section TEXT DEFAULT 'A'")

    cursor.execute("PRAGMA table_info(attendance_records)")
    a_cols = [r[1] for r in cursor.fetchall()]
    if "section" not in a_cols:
        cursor.execute("ALTER TABLE attendance_records ADD COLUMN section TEXT DEFAULT 'A'")

    cursor.execute("PRAGMA table_info(day_status)")
    d_cols = [r[1] for r in cursor.fetchall()]
    if "section" not in d_cols:
        cursor.execute("ALTER TABLE day_status ADD COLUMN section TEXT DEFAULT 'A'")

    # Migration: Ensure hods table has username and password columns
    cursor.execute("PRAGMA table_info(hods)")
    h_cols = [r[1] for r in cursor.fetchall()]
    if "username" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN username TEXT")
    if "password" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN password TEXT DEFAULT 'hod123'")

    # Migration: Ensure teachers table has Google Authenticator 2FA columns and is_approved
    cursor.execute("PRAGMA table_info(teachers)")
    t_cols = [r[1] for r in cursor.fetchall()]
    if "totp_secret" not in t_cols:
        cursor.execute("ALTER TABLE teachers ADD COLUMN totp_secret TEXT")
    if "is_2fa_enabled" not in t_cols:
        cursor.execute("ALTER TABLE teachers ADD COLUMN is_2fa_enabled INTEGER DEFAULT 0")
    if "is_approved" not in t_cols:
        cursor.execute("ALTER TABLE teachers ADD COLUMN is_approved INTEGER DEFAULT 1")

    # Migration: Ensure hods table has Google Authenticator 2FA columns and is_approved
    cursor.execute("PRAGMA table_info(hods)")
    h_cols = [r[1] for r in cursor.fetchall()]
    if "totp_secret" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN totp_secret TEXT")
    if "is_2fa_enabled" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN is_2fa_enabled INTEGER DEFAULT 0")
    if "is_approved" not in h_cols:
        cursor.execute("ALTER TABLE hods ADD COLUMN is_approved INTEGER DEFAULT 1")

    # Migration: Ensure admins table has Google Authenticator 2FA columns and is_approved
    cursor.execute("PRAGMA table_info(admins)")
    adm_cols = [r[1] for r in cursor.fetchall()]
    if "totp_secret" not in adm_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN totp_secret TEXT")
    if "is_2fa_enabled" not in adm_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN is_2fa_enabled INTEGER DEFAULT 0")
    if "is_approved" not in adm_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN is_approved INTEGER DEFAULT 1")

    # Ensure permanent shield against unwanted legacy faculty auto-insertion
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_unwanted_faculty_seed
        BEFORE INSERT ON teachers
        FOR EACH ROW
        WHEN LOWER(NEW.username) IN ('faizan', 'lakshmidattatri', 'dattatri')
          OR LOWER(NEW.name) LIKE '%faizan%'
          OR LOWER(NEW.name) LIKE '%dattatri%'
        BEGIN
            SELECT RAISE(IGNORE);
        END;
    """)

    # 13. System Settings Table (Geo-fencing, Campus configs, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default system settings if missing
    default_settings = [
        ("geofence_enabled", "0"),
        ("college_latitude", "14.0044"),
        ("college_longitude", "78.7523"),
        ("geofence_radius_meters", "1000"),
        ("emergency_bypass_key", "SSITS@2026")
    ]
    for k, v in default_settings:
        cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key = ?", (k,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO system_settings (key, value) VALUES (?, ?)", (k, v))

    # 14. Security & Activity Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_role TEXT NOT NULL,
            user_id INTEGER,
            user_name TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 15. Performance Optimization Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_att_lookup ON attendance_records(attendance_date, session_type, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_att_student ON attendance_records(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_lookup ON students(program_id, department_id, year_id, section)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_teachers_lookup ON teachers(program_id, department_id, year_id, section)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_day_status_lookup ON day_status(program_id, department_id, year_id, attendance_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_role ON audit_logs(user_role)")

    # Backfill default values
    cursor.execute("UPDATE teachers SET section = 'A' WHERE section IS NULL OR section = ''")
    cursor.execute("UPDATE students SET section = 'A' WHERE section IS NULL OR section = ''")
    cursor.execute("UPDATE attendance_records SET section = 'A' WHERE section IS NULL OR section = ''")
    cursor.execute("UPDATE day_status SET section = 'A' WHERE section IS NULL OR section = ''")
    cursor.execute("UPDATE teachers SET email = username || '@gmail.com' WHERE email IS NULL OR email = ''")

    # Set HOD usernames (e.g. hod_ece, hod_cse, etc.) and passwords
    cursor.execute("""
        UPDATE hods 
        SET username = 'hod_' || LOWER((SELECT code FROM departments WHERE departments.id = hods.department_id))
        WHERE username IS NULL OR username = ''
    """)
    cursor.execute("UPDATE hods SET password = 'hod123' WHERE password IS NULL OR password = ''")

    # Seed / Update Super Admin (Kamanuru Basha)
    cursor.execute("SELECT id, username, email, password, totp_secret, is_2fa_enabled FROM admins WHERE role = 'superadmin' OR username = 'admin' OR username = 'reddybashakamanuru18@gmail.com' OR LOWER(email) = 'reddybashakamanuru18@gmail.com' OR LOWER(email) = 'kamanurubasha@gmail.com' LIMIT 1")
    admin_match = cursor.fetchone()
    admin_env_pw = os.getenv("ADMIN_PASSWORD")
    MASTER_ADMIN_SECRET = "TW6JMF5JLJAASADJIEO57HDBD24JRCMC"

    if not admin_match:
        target_admin_pw = admin_env_pw if admin_env_pw else "Hamzark@123"
        cursor.execute("""
            INSERT INTO admins (username, password, name, email, phone, role, is_2fa_enabled, totp_secret, is_approved)
            VALUES ('reddybashakamanuru18@gmail.com', ?, 'Kamanuru Basha', 'reddybashakamanuru18@gmail.com', '9848099999', 'superadmin', 1, ?, 1)
        """, (target_admin_pw, MASTER_ADMIN_SECRET))
    else:
        # Prioritize the password saved in the database! It will never be overwritten
        existing_db_pw = admin_match["password"]
        new_pw = existing_db_pw if existing_db_pw else (admin_env_pw if admin_env_pw else "Hamzark@123")
        current_secret = admin_match["totp_secret"] or MASTER_ADMIN_SECRET
        cursor.execute("""
            UPDATE admins 
            SET username = 'reddybashakamanuru18@gmail.com',
                email = 'reddybashakamanuru18@gmail.com',
                name = 'Kamanuru Basha',
                password = ?,
                is_2fa_enabled = 1,
                totp_secret = ?,
                is_approved = 1
            WHERE id = ?
        """, (new_pw, current_secret, admin_match["id"]))

    # Seed Principal Account if not exists
    cursor.execute("SELECT COUNT(*) FROM admins WHERE role = 'principal' OR username = 'principal'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO admins (username, password, name, email, phone, role)
            VALUES ('principal', 'principal123', 'Dr. Principal / Director (SSITS)', 'principal@srisaitech.ac.in', '9848099901', 'principal')
        """)

    # Note: Faculty accounts are dynamically maintained in Turso cloud database.

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM programs")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor, conn)

    conn.close()
    print("Database initialized with Super Admin, Day Status, Section and Email support!")

def seed_data(cursor, conn):
    print("Seeding programs: Diploma (5 branches x 3 years) & B.Tech (3 branches x 4 years)...")

    programs = [
        ("DIPLOMA", "Diploma (Polytechnic)", 3),
        ("BTECH", "B.Tech (Bachelor of Technology)", 4)
    ]
    cursor.executemany("INSERT INTO programs (code, name, duration_years) VALUES (?, ?, ?)", programs)

    depts = [
        ("ECE", "Electronics & Communication Engineering"),
        ("EEE", "Electrical & Electronics Engineering"),
        ("CSE", "Computer Science & Engineering"),
        ("MECH", "Mechanical Engineering"),
        ("CIVIL", "Civil Engineering"),
        ("AIDS", "Artificial Intelligence & Data Science")
    ]
    cursor.executemany("INSERT INTO departments (code, name) VALUES (?, ?)", depts)

    years = [
        ("1st Year", "1_YEAR", 1),
        ("2nd Year", "2_YEAR", 2),
        ("3rd Year", "3_YEAR", 3),
        ("4th Year", "4_YEAR", 4)
    ]
    cursor.executemany("INSERT INTO academic_years (year_name, year_code, year_num) VALUES (?, ?, ?)", years)

    cursor.execute("SELECT id, code FROM programs")
    prog_map = {row["code"]: row["id"] for row in cursor.fetchall()}

    cursor.execute("SELECT id, code FROM departments")
    dept_map = {row["code"]: row["id"] for row in cursor.fetchall()}

    cursor.execute("SELECT id, year_num FROM academic_years")
    year_map = {row["year_num"]: row["id"] for row in cursor.fetchall()}

    diploma_branches = ["ECE", "EEE", "CSE", "MECH", "CIVIL"]
    for b in diploma_branches:
        cursor.execute("INSERT INTO program_departments (program_id, department_id) VALUES (?, ?)",
                       (prog_map["DIPLOMA"], dept_map[b]))

    btech_branches = ["ECE", "CSE", "AIDS"]
    for b in btech_branches:
        cursor.execute("INSERT INTO program_departments (program_id, department_id) VALUES (?, ?)",
                       (prog_map["BTECH"], dept_map[b]))

    diploma_hods = [
        (prog_map["DIPLOMA"], dept_map["ECE"], "Sri. K. Venkatesh (HOD - Diploma ECE)", "9848011221", "hod_dip_ece@srisaitech.ac.in"),
        (prog_map["DIPLOMA"], dept_map["EEE"], "Sri. N. Ramesh (HOD - Diploma EEE)", "9848011222", "hod_dip_eee@srisaitech.ac.in"),
        (prog_map["DIPLOMA"], dept_map["CSE"], "Smt. P. Madhavi (HOD - Diploma CSE)", "9848011223", "hod_dip_cse@srisaitech.ac.in"),
        (prog_map["DIPLOMA"], dept_map["MECH"], "Sri. T. Srinivas (HOD - Diploma MECH)", "9848011224", "hod_dip_mech@srisaitech.ac.in"),
        (prog_map["DIPLOMA"], dept_map["CIVIL"], "Sri. V. Ashok (HOD - Diploma CIVIL)", "9848011225", "hod_dip_civil@srisaitech.ac.in")
    ]
    cursor.executemany("INSERT INTO hods (program_id, department_id, name, phone, email) VALUES (?, ?, ?, ?, ?)", diploma_hods)

    btech_hods = [
        (prog_map["BTECH"], dept_map["ECE"], "Dr. P. Mallikarjuna Rao (HOD - B.Tech ECE)", "9848044550", "hod_ece@srisaitech.ac.in"),
        (prog_map["BTECH"], dept_map["CSE"], "Dr. K. V. Ramanjaneyulu (HOD - B.Tech CSE)", "9848022338", "hod_cse@srisaitech.ac.in"),
        (prog_map["BTECH"], dept_map["AIDS"], "Dr. S. Lakshmi Narayana (HOD - B.Tech AI&DS)", "9848033449", "hod_aids@srisaitech.ac.in")
    ]
    cursor.executemany("INSERT INTO hods (program_id, department_id, name, phone, email) VALUES (?, ?, ?, ?, ?)", btech_hods)

    teachers_to_add = []
    teacher_names = [
        "Smt. K. Sunitha", "Sri. B. Ramesh", "Smt. M. Vani", "Sri. Ch. Naresh",
        "Smt. G. Bhavani", "Sri. D. Suresh", "Sri. T. Srinivas", "Sri. N. Rajesh",
        "Smt. V. Kalyani", "Sri. E. Mahesh", "Sri. Y. Prasad", "Smt. S. Anitha",
        "Sri. R. Kiran", "Sri. J. Praveen", "Smt. B. Swathi"
    ]
    idx = 0
    for b in diploma_branches:
        for yr in [1, 2, 3]:
            t_name = teacher_names[idx % len(teacher_names)]
            username = f"dip_{b.lower()}_{yr}yr"
            phone = f"9440{idx:02d}5566"
            teachers_to_add.append((t_name, prog_map["DIPLOMA"], dept_map[b], year_map[yr], username, "123456", phone))
            idx += 1

    btech_teacher_names = [
        "Dr. A. Sudhakar", "Dr. P. Swaroop", "Smt. L. Deepthi", "Sri. V. Raghavendra",
        "Dr. M. Sridhar", "Smt. K. Hema", "Sri. P. Sandeep", "Smt. T. Sirisha",
        "Dr. N. Bharathi", "Sri. G. Vijay", "Smt. R. Pavani", "Sri. C. Kalyan"
    ]
    b_idx = 0
    for b in btech_branches:
        for yr in [1, 2, 3, 4]:
            t_name = btech_teacher_names[b_idx % len(btech_teacher_names)]
            username = f"btech_{b.lower()}_{yr}yr"
            phone = f"9849{b_idx:02d}7788"
            teachers_to_add.append((t_name, prog_map["BTECH"], dept_map[b], year_map[yr], username, "123456", phone))
            b_idx += 1

    cursor.executemany("""
        INSERT INTO teachers (name, program_id, department_id, year_id, username, password, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, teachers_to_add)

    seed_students(cursor, conn)

def seed_students(cursor, conn):
    cursor.execute("SELECT id, code FROM programs")
    prog_map = {row["code"]: row["id"] for row in cursor.fetchall()}

    cursor.execute("SELECT id, code FROM departments")
    dept_map = {row["code"]: row["id"] for row in cursor.fetchall()}

    cursor.execute("SELECT id, year_num FROM academic_years")
    year_map = {row["year_num"]: row["id"] for row in cursor.fetchall()}

    diploma_branches = ["ECE", "EEE", "CSE", "MECH", "CIVIL"]
    btech_branches = ["ECE", "CSE", "AIDS"]

    sample_students_data = [
        ("G. Sai Kumar", "G. Narayana Rao", "9849112233"),
        ("P. Venkata Ramana", "P. Subba Rao", "9440223344"),
        ("K. Ananya", "K. Srinivasa Rao", "9988334455"),
        ("M. Manoj Reddy", "M. Rami Reddy", "9700445566"),
        ("B. Tejaswini", "B. Venkateswarlu", "9848556677"),
        ("Ch. Harish Babu", "Ch. Prabhakar", "9618667788"),
        ("D. Divya Vani", "D. Ramana Murthy", "9490778899"),
        ("T. Akhil Varma", "T. Satyanarayana", "9866889900"),
        ("V. Sneha Latha", "V. Anjaneyulu", "9959990011"),
        ("S. Mahesh Chandra", "S. Chandrasekhar", "9849001122"),
        ("R. Swetha", "R. Krishna Murthy", "9440112233"),
        ("N. Pawan Kalyan", "N. Appa Rao", "9988223344"),
        ("Y. Sravani", "Y. Mallikarjuna", "9700334455"),
        ("A. Karthik", "A. Nagendra Babu", "9848445566"),
        ("E. Keerthana", "E. Lakshman Rao", "9618556677")
    ]

    all_students = []
    dip_branch_codes = {"ECE": "EC", "EEE": "EE", "CSE": "CM", "MECH": "ME", "CIVIL": "CE"}
    dip_year_prefixes = {1: "23", 2: "22", 3: "21"}
    for b in diploma_branches:
        b_code = dip_branch_codes[b]
        for yr in [1, 2, 3]:
            y_prefix = dip_year_prefixes[yr]
            for s_idx, (s_name, f_name, f_phone) in enumerate(sample_students_data, start=1):
                roll = f"{y_prefix}-SSIT-{b_code}-{s_idx:03d}"
                all_students.append((
                    roll, s_name, prog_map["DIPLOMA"], dept_map[b], year_map[yr], f_name, f_phone
                ))

    btech_branch_codes = {"ECE": "04", "CSE": "05", "AIDS": "54"}
    btech_year_prefixes = {1: "23G31A", 2: "22G31A", 3: "21G31A", 4: "20G31A"}
    for b in btech_branches:
        b_code = btech_branch_codes[b]
        for yr in [1, 2, 3, 4]:
            y_prefix = btech_year_prefixes[yr] + b_code
            for s_idx, (s_name, f_name, f_phone) in enumerate(sample_students_data, start=1):
                roll = f"{y_prefix}{s_idx:02d}"
                all_students.append((
                    roll, s_name, prog_map["BTECH"], dept_map[b], year_map[yr], f_name, f_phone
                ))

    cursor.executemany("""
        INSERT INTO students (roll_number, name, program_id, department_id, year_id, father_name, father_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, all_students)

    conn.commit()
    print(f"Added {len(all_students)} students across Diploma (3 Years) and B.Tech (4 Years)!")
    return len(all_students)

def sync_pending_faculty_to_turso(conn=None):
    """
    Guarantees zero lost registrations.
    If a faculty registered while Turso was in cooldown or offline,
    this automatically pulls any unapproved faculty (is_approved=0) from local SQLite
    and syncs them to Turso Cloud so the Admin ALWAYS sees them in the dashboard.
    """
    if os.getenv("USE_LOCAL_SQLITE") == "1":
        return
    try:
        import sqlite3
        if not os.path.exists(DB_PATH):
            return
        loc = sqlite3.connect(DB_PATH)
        loc.row_factory = sqlite3.Row
        cur = loc.cursor()
        cur.execute("SELECT * FROM teachers WHERE is_approved = 0")
        pending_local = cur.fetchall()
        loc.close()

        if not pending_local:
            return

        should_close = False
        if conn is None:
            conn = get_db_connection()
            should_close = True

        cloud_cur = conn.cursor()
        for t in pending_local:
            cloud_cur.execute("SELECT id FROM teachers WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)", (t["email"], t["username"]))
            if not cloud_cur.fetchone():
                cloud_cur.execute("""
                    INSERT INTO teachers (name, program_id, department_id, year_id, section, email, username, password, phone, is_approved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (t["name"], t["program_id"], t["department_id"], t["year_id"], t["section"] or "A", t["email"], t["username"], t["password"], t["phone"]))
                if hasattr(conn, "commit"):
                    conn.commit()
                print(f"[SYNC] Pushed unapproved faculty '{t['name']}' ({t['username']}) to Turso Cloud!")
        if should_close:
            conn.close()
    except Exception as e:
        print(f"[WARN] sync_pending_faculty_to_turso: {e}")

if __name__ == "__main__":
    init_db()

