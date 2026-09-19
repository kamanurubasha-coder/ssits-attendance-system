import os
import sqlite3

def main():
    db_path = os.path.join(os.path.dirname(__file__), 'attendance.db')
    if not os.path.exists(db_path):
        print('[!] attendance.db not found in current folder.')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, username, email FROM admins WHERE role = 'superadmin' OR id = 1 LIMIT 1")
    admin = cursor.fetchone()

    if admin:
        cursor.execute("UPDATE admins SET is_2fa_enabled = 0, totp_secret = NULL WHERE id = ?", (admin[0],))
        conn.commit()
        print("=" * 60)
        print("  SSITS MASTER ADMIN - 2FA RESET COMPLETE")
        print("=" * 60)
        print(f"[*] Admin Name     : {admin[1]}")
        print(f"[*] Admin Username : {admin[2]}")
        print(f"[*] 2FA Status     : RESET to 0 (Disabled)")
        print("=" * 60)
        print("\n[NEXT STEPS]:")
        print("1. Open /admin in your browser.")
        print("2. Enter your Admin Username and Password.")
        print("3. The system will automatically show a fresh QR code.")
        print("4. Scan the QR code with Google Authenticator to re-link your phone!")
        print("=" * 60)
    else:
        print("[!] No Super Administrator found.")
    conn.close()

if __name__ == '__main__':
    main()
