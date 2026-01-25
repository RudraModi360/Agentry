import sqlite3
import os

DB_PATH = r"d:\Scratchy\ui\scratchy_users.db"

def check_schema():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(user_active_settings)")
    columns = cursor.fetchall()
    
    print("Columns in user_active_settings:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Check column names
    col_names = [col[1] for col in columns]
    if "model_type" not in col_names:
        print("\n[ALERT] model_type column is MISSING!")
        try:
            cursor.execute("ALTER TABLE user_active_settings ADD COLUMN model_type TEXT")
            conn.commit()
            print("[FIXED] Added model_type column to user_active_settings")
        except Exception as e:
            print(f"[RETRY] Failed to add column: {e}")
    else:
        print("\nmodel_type column exists.")
        
    conn.close()

if __name__ == "__main__":
    check_schema()
