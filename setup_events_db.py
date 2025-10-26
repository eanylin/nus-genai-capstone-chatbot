import sqlite3
import os

def setup_database():
    DB_FILE = "events.db"
    
    # Simulated current date
    TODAY_STR = "2025-10-26"
    TOMORROW_STR = "2025-10-27"

    # Remove and recreate DB if file exists
    if os.path.exists(DB_FILE):
        print(f"'{DB_FILE}' already exists. Deleting old file...")
        os.remove(DB_FILE)

    print(f"Creating new database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Database schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,  -- 'indoor' or 'outdoor'
            description TEXT,
            location TEXT,
            date TEXT
        )
    ''')

    # Sample events
    events = [
        # Events for today (Oct 26, 2025)
        ('AI Tech Summit', 'indoor', 'A deep dive into generative AI.', 'Suntec Convention Centre', TODAY_STR),
        ('Singapore Airshow', 'outdoor', 'International aerospace and defence exhibitions', 'Changi Exhibition Centre', TODAY_STR),
        ('Marina Bay Night Run', 'outdoor', 'A 5km fun run around the bay.', 'Marina Bay Sands', TODAY_STR),
        ('Jazz in the Park', 'outdoor', 'Relaxing evening with live jazz music.', 'Botanic Gardens', TODAY_STR),
        
        # Events for tomorrow (Oct 27, 2025)
        ('Gourmet Food Festival', 'indoor', 'Taste dishes from around the world.', 'Food Republic @ VivoCity', TOMORROW_STR),
        ('Theater Show', 'indoor', 'Classical drama', 'Grand Theater', TOMORROW_STR),
        ('Cybersecurity Asia 2025', 'indoor', 'Tech, ''Marina Bay Sands', TOMORROW_STR),
        ('Movies at The Fort', 'outdoor', 'Lifestyle', 'Fort Canning Park', TOMORROW_STR)
    ]

    c.executemany('INSERT INTO events (name, type, description, location, date) VALUES (?,?,?,?,?)', events)
    conn.commit()
    conn.close()
    
    print(f"\nDatabase '{DB_FILE}' created and populated successfully.")
    print(f"Data has been added for {TODAY_STR}.")

if __name__ == "__main__":
    setup_database()
