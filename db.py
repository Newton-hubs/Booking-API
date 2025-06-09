import sqlite3
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('fitness_studio.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create classes table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            datetime TEXT NOT NULL,
            instructor TEXT NOT NULL,
            available_slots INTEGER NOT NULL
        )
    ''')
    # Create bookings table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            client_email TEXT NOT NULL,
            booked_at TEXT NOT NULL,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )
    ''')
    conn.commit()
    conn.close()

def seed_data():
    conn = get_db_connection()
    cur = conn.cursor()
    # Check if classes already exist
    cur.execute('SELECT COUNT(*) FROM classes')
    if cur.fetchone()[0] == 0:
        # Insert sample classes (all in IST)
        now = datetime.now() + timedelta(days=1)
        classes = [
            ("Yoga", (now).strftime('%Y-%m-%d %H:%M:%S'), "Amit Sharma", 15),
            ("Zumba", (now + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'), "Priya Singh", 15),
            ("HIIT", (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), "Rahul Verma", 12)
        ]
        cur.executemany('INSERT INTO classes (name, datetime, instructor, available_slots) VALUES (?, ?, ?, ?)', classes)
        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_data()
