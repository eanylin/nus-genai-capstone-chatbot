import sqlite3

def setup_database():
    conn = sqlite3.connect('company.db')
    c = conn.cursor()

    # Create sample tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary REAL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            budget REAL
        )
    ''')

    # Insert sample data
    c.execute("INSERT OR IGNORE INTO employees VALUES (1, 'John Doe', 'Engineering', 75000)")
    c.execute("INSERT OR IGNORE INTO employees VALUES (2, 'Jane Smith', 'Marketing', 65000)")
    c.execute("INSERT OR IGNORE INTO departments VALUES (1, 'Engineering', 1000000)")
    c.execute("INSERT OR IGNORE INTO departments VALUES (2, 'Marketing', 500000)")

    conn.commit()
    conn.close()

# Test database setup
if __name__ == "__main__":
    setup_database()

    # Verify the setup
    conn = sqlite3.connect('company.db')
    c = conn.cursor()

    print("Employees table:")
    c.execute("SELECT * FROM employees")
    print(c.fetchall())

    print("\nDepartments table:")
    c.execute("SELECT * FROM departments")
    print(c.fetchall())

    conn.close()
