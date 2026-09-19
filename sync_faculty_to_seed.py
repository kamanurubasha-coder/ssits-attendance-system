#!/usr/bin/env python3
"""
=============================================================================
Sri Sai Institute of Technology and Science (Autonomous)
Solution 2 Helper: Sync Registered Faculty into database.py Seed Roster
=============================================================================
Usage:
    python sync_faculty_to_seed.py

Description:
    Reads all approved faculty members currently registered in attendance.db
    and generates a permanent seeding function in database.py.
    This guarantees that even if Render restarts or creates a new container,
    all 27 of your official college faculty will be automatically preserved!
=============================================================================
"""

import os
import sqlite3
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")
DATABASE_PY = os.path.join(os.path.dirname(__file__), "database.py")
GITHUB_DATABASE_PY = os.path.join(os.path.dirname(__file__), "github_upload", "database.py")

def sync_faculty():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, program_id, department_id, year_id, section, email, username, password, phone, is_approved, is_2fa_enabled, totp_secret
        FROM teachers
        WHERE is_approved = 1
        ORDER BY id ASC
    """)
    teachers = cursor.fetchall()
    conn.close()

    print(f"[*] Found {len(teachers)} approved faculty member(s) in {DB_PATH}:")
    for idx, t in enumerate(teachers, 1):
        print(f"   {idx}. {t['name']} | User: {t['username']} | Dept: {t['department_id']} | Year: {t['year_id']} | Sec: {t['section']}")

    if not teachers:
        print("[!] No approved faculty found to sync.")
        return

    # Generate Python code to insert these teachers permanently
    lines = ["    # Permanent preservation of registered college faculties (Auto-synced)\n"]
    lines.append("    official_faculty_roster = [\n")
    for t in teachers:
        record = {
            "name": t["name"],
            "program_id": t["program_id"],
            "department_id": t["department_id"],
            "year_id": t["year_id"],
            "section": t["section"] or "A",
            "email": t["email"] or f"{t['username']}@srisaitech.ac.in",
            "username": t["username"],
            "password": t["password"],
            "phone": t["phone"],
            "is_approved": 1,
            "is_2fa_enabled": t["is_2fa_enabled"] or 0,
            "totp_secret": t["totp_secret"]
        }
        lines.append(f"        {repr(record)},\n")
    lines.append("    ]\n")
    lines.append("    for fac in official_faculty_roster:\n")
    lines.append("        cursor.execute('SELECT id FROM teachers WHERE LOWER(username) = ?', (fac['username'].lower(),))\n")
    lines.append("        if not cursor.fetchone():\n")
    lines.append("            cursor.execute('''\n")
    lines.append("                INSERT INTO teachers (name, program_id, department_id, year_id, section, email, username, password, phone, is_approved, is_2fa_enabled, totp_secret)\n")
    lines.append("                VALUES (:name, :program_id, :department_id, :year_id, :section, :email, :username, :password, :phone, :is_approved, :is_2fa_enabled, :totp_secret)\n")
    lines.append("            ''', fac)\n")
    lines.append("        else:\n")
    lines.append("            cursor.execute('''\n")
    lines.append("                UPDATE teachers SET is_approved = 1 WHERE LOWER(username) = ?\n")
    lines.append("            ''', (fac['username'].lower(),))\n")

    sync_code_block = "".join(lines)

    # Inject into database.py
    for target_path in [DATABASE_PY, GITHUB_DATABASE_PY]:
        if not os.path.exists(target_path):
            continue
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r"(    # Permanent preservation of registered faculties.*?\n)(.*?)(    # Seed Principal Account|\Z)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, rf"\1{sync_code_block}\n\3", content, flags=re.DOTALL)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[SUCCESS] Updated {target_path} with {len(teachers)} permanent faculty records!")
        else:
            print(f"[WARN] Marker not found in {target_path}. Please inspect manually.")

    print("\n[DONE] Solution 2 Complete! Your registered faculty are now permanently protected in code.")

if __name__ == "__main__":
    sync_faculty()
