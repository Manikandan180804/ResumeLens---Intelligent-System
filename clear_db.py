import sqlite3
import time

def clear_db():
    conn = sqlite3.connect('resume_intelligence.db', timeout=30)
    cursor = conn.cursor()
    try:
        print("Clearing evaluations...")
        cursor.execute("DELETE FROM evaluations")
        print("Clearing resumes...")
        cursor.execute("DELETE FROM resumes")
        print("Clearing job descriptions...")
        cursor.execute("DELETE FROM job_descriptions")
        conn.commit()
        print("Database cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clear_db()
