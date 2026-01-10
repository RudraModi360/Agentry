import sqlite3
import os

DB_PATH = 'd:/Scratchy/ui/scratchy_users.db'

def inspect_users():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        print(f"Users found: {users}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_users()
