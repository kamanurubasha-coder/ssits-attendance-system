#!/usr/bin/env python3
"""
=============================================================================
Sri Sai Institute of Technology and Science (Autonomous)
Academic Attendance Portal - Academic Data Reset Utility
=============================================================================
Usage:
    python reset_data.py               # Interactive prompt
    python reset_data.py --attendance  # Direct Attendance & Logs purge
    python reset_data.py --factory     # Full factory re-seed
=============================================================================
"""

import sys
import os
import sqlite3
import argparse
from database import get_db_connection, DB_PATH, seed_data, seed_students

def print_banner():
    print("=" * 70)
    print("  SRI SAI INSTITUTE OF TECHNOLOGY AND SCIENCE (AUTONOMOUS)")
    print("  ACADEMIC DATA PURGE & SEMESTER RESET TOOL")
    print(f"  Target Database: {DB_PATH}")
    print("=" * 70)

def reset_attendance_only():
    """Wipes all daily attendance, day status, OTPs, and password reset tokens."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM attendance_records")
        att_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM day_status")
        day_count = cursor.fetchone()[0]

        print(f"[*] Found {att_count} attendance records and {day_count} college day status records.")
        print("[*] Erasing attendance records, day statuses, email OTPs, and password tokens...")

        cursor.execute("DELETE FROM attendance_records")
        cursor.execute("DELETE FROM day_status")
        cursor.execute("DELETE FROM email_otps")
        cursor.execute("DELETE FROM password_resets")

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM students")
        stud_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM teachers")
        teacher_count = cursor.fetchone()[0]

        print("\n[SUCCESS] ACADEMIC ATTENDANCE RESET COMPLETE!")
        print(f"  - Cleared: Attendance records wiped to 0")
        print(f"  - Cleared: Day status flags wiped to 0")
        print(f"  - Preserved: {stud_count} Enrolled Student profiles are intact")
        print(f"  - Preserved: {teacher_count} Faculty login accounts remain active")
        print(f"  - Status: Portal is 100% clean and ready for next month's launch!\n")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Reset failed: {e}")
        return False
    finally:
        conn.close()

def reset_factory():
    """Wipes attendance and re-seeds official student master rosters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print("[*] Performing full factory reset...")
        cursor.execute("DELETE FROM attendance_records")
        cursor.execute("DELETE FROM day_status")
        cursor.execute("DELETE FROM email_otps")
        cursor.execute("DELETE FROM password_resets")
        cursor.execute("DELETE FROM students")

        seed_students(cursor, conn)

        cursor.execute("SELECT COUNT(*) FROM students")
        stud_count = cursor.fetchone()[0]

        print("\n[SUCCESS] FULL FACTORY RESET COMPLETE!")
        print(f"  - Re-seeded: {stud_count} Official Student records across all 27 sections")
        print(f"  - Cleared: All test attendance records reset to 0")
        print("  - Status: Database is fresh from factory state!\n")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Factory reset failed: {e}")
        return False
    finally:
        conn.close()

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="SSITS Attendance Portal Data Reset Tool")
    parser.add_argument("--attendance", action="store_true", help="Purge attendance records only (keeps students & faculty)")
    parser.add_argument("--factory", action="store_true", help="Full factory reset with re-seeded students")
    args = parser.parse_args()

    if args.attendance:
        reset_attendance_only()
        return

    if args.factory:
        reset_factory()
        return

    print("\nSelect an option to prepare your portal:")
    print("  [1] Monthly / Academic Attendance Reset (RECOMMENDED for next month)")
    print("      -> Erases all attendance records & test data.")
    print("      -> Keeps all student enrollments, faculty accounts & department setups safe.\n")
    print("  [2] Full Factory Reset")
    print("      -> Erases attendance and re-seeds original master students.\n")
    print("  [3] Cancel & Exit\n")

    choice = input("Enter choice (1, 2, or 3): ").strip()

    if choice == "1":
        confirm = input("Type 'YES' to confirm wiping attendance data: ").strip()
        if confirm == "YES":
            reset_attendance_only()
        else:
            print("[*] Aborted. No changes made.")
    elif choice == "2":
        confirm = input("Type 'YES' to confirm full factory reset: ").strip()
        if confirm == "YES":
            reset_factory()
        else:
            print("[*] Aborted. No changes made.")
    else:
        print("[*] Operation cancelled.")

if __name__ == "__main__":
    main()
