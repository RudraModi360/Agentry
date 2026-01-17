import sqlite3
import json

def check_db():
    try:
        conn = sqlite3.connect('ui/scratchy_users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='user_media'")
        schema = cursor.fetchone()
        print(f"Schema: {schema[0] if schema else 'Not found'}")
        
        # Get latest items
        cursor.execute("SELECT * FROM user_media ORDER BY created_at DESC LIMIT 5")
        rows = [dict(row) for row in cursor.fetchall()]
        print(f"Latest items: {json.dumps(rows, indent=2)}")
        
        # Count items
        cursor.execute("SELECT count(*) FROM user_media")
        count = cursor.fetchone()[0]
        print(f"Total count: {count}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_db()
