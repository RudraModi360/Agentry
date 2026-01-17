import sqlite3
import os

DB_PATH = 'd:/Scratchy/ui/scratchy_users.db'

def update_emails():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET email = 'rudramodi9560@gmail.com' WHERE username = 'Rudra'")
        conn.commit()
        print(f"Successfully updated {cursor.rowcount} users with email 'rudramodi9560@gmail.com'")
    except Exception as e:
        print(f"Error updating emails: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_emails()
