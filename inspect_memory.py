import sqlite3
import os
import argparse
from datetime import datetime

def inspect_db(db_path: str = None):
    if db_path is None:
        # Default path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "scratchy", "user_data", "memory.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    print(f"📂 Inspecting Database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. List Sessions
        print("="*60)
        print("📊 SESSIONS")
        print("="*60)
        cursor.execute("SELECT * FROM sessions ORDER BY last_activity DESC")
        sessions = cursor.fetchall()
        
        if not sessions:
            print("   (No sessions found)")
        else:
            for s in sessions:
                print(f"   🆔 ID: {s['session_id']}")
                print(f"      Created: {s['created_at']}")
                print(f"      Last Active: {s['last_activity']}")
                print("-" * 40)

        # 2. List Memories
        print("\n" + "="*60)
        print("🧠 MEMORIES (Long-Term Facts)")
        print("="*60)
        cursor.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT 20")
        memories = cursor.fetchall()
        
        if not memories:
            print("   (No memories found)")
        else:
            for m in memories:
                print(f"   [{m['type'].upper()}] (Session: {m['session_id']})")
                print(f"   📝 {m['content']}")
                print(f"   🕒 {m['timestamp']}")
                print("-" * 40)

        # 3. List Agent State
        print("\n" + "="*60)
        print("⚙️  AGENT STATE (Checkpoints)")
        print("="*60)
        cursor.execute("SELECT * FROM agent_state ORDER BY updated_at DESC LIMIT 20")
        states = cursor.fetchall()
        
        if not states:
            print("   (No state checkpoints found)")
        else:
            for st in states:
                print(f"   🔑 Key: {st['key']} (Session: {st['session_id']})")
                print(f"      Value: {st['value'][:100]}..." if len(str(st['value'])) > 100 else f"      Value: {st['value']}")
                print(f"      Updated: {st['updated_at']}")
                print("-" * 40)

    except Exception as e:
        print(f"❌ Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Scratchy Memory DB")
    parser.add_argument("--path", help="Path to memory.db file", default=None)
    args = parser.parse_args()
    
    inspect_db(args.path)
