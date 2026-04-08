import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def init_db():
    print("Initializing database...")
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    
    cursor = conn.cursor()
    
    # Check if users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("Inserting placeholder data...")
        # Insert Admin and User
        # Link admin to Employee 1 (John Smith) and user to Employee 2 (Jane Doe)
        cursor.execute("INSERT INTO users (username, password, role, employee_id) VALUES ('admin', 'admin123', 'admin', 1)")
        cursor.execute("INSERT INTO users (username, password, role, employee_id) VALUES ('user', 'user123', 'user', 2)")
        
        # Insert Employees
        employees = [
            ('Smith', 'John', '1985-06-15', 'Permanent'),
            ('Doe', 'Jane', '1990-08-22', 'Non-Permanent'),
            ('Johnson', 'Michael', '1988-11-05', 'Temporary'),
            ('Williams', 'Sarah', '1992-02-14', 'Separated'),
            ('Brown', 'David', '1980-04-10', 'Permanent')
        ]
        cursor.executemany("INSERT INTO employees (last_name, first_name, birthday, status) VALUES (?, ?, ?, ?)", employees)
        
        # Insert Trainings
        trainings = [
            (1, 'Agile Methodologies', '2023-01-15'),
            (1, 'Advanced Project Management', '2023-05-20'),
            (2, 'Data Analytics Basics', '2022-11-10'),
            (5, 'Leadership Workshop', '2023-08-05')
        ]
        cursor.executemany("INSERT INTO trainings (employee_id, title, date) VALUES (?, ?, ?)", trainings)
        
        # Insert Service Records
        service_records = [
            (1, 'Junior Developer', '2020-01-10', '2022-01-15'),
            (1, 'Senior Developer', '2022-01-16', None),
            (2, 'Analyst', '2021-03-01', None),
            (5, 'Team Lead', '2019-06-01', None)
        ]
        cursor.executemany("INSERT INTO service_records (employee_id, position, start_date, end_date) VALUES (?, ?, ?, ?)", service_records)
        
        # Insert Activity Logs
        activities = [
            ('Added new employee', 'Jane Doe', '2021-03-01 10:00:00'),
            ('Updated training record', 'John Smith', '2023-05-21 14:30:00'),
            ('Employee separated', 'Sarah Williams', '2023-10-01 09:15:00')
        ]
        cursor.executemany("INSERT INTO activity_logs (activity, employee_name, date) VALUES (?, ?, ?)", activities)
        
        # Insert Skills
        skills = [
            (1, 'Project Management'),
            (1, 'Python Programming'),
            (2, 'Data Analysis'),
            (2, 'Excel Automation'),
            (3, 'Graphic Design'),
            (5, 'Leadership')
        ]
        cursor.executemany("INSERT INTO skills (employee_id, skill_name) VALUES (?, ?)", skills)

        # Insert Gigs
        gigs = [
            ('Need a poster for Company Event', 'Looking for someone with Graphic Design skills to create an eye-catching poster.', 1, 'Open', None, None, 150),
            ('Help with monthly Excel report', 'Need someone who knows Excel automation to write a macro for me.', 5, 'In Progress', 2, None, 200),
            ('Review my Python script', 'Can someone review a small script I wrote? Should take 30 mins.', 2, 'Completed', 1, 5, 50),
            ('Design new Logo for department', 'Need a fresh logo with standard colors.', 2, 'Pending Approval', None, None, 100)
        ]
        cursor.executemany("INSERT INTO gigs (title, description, posted_by, status, awarded_to, rating, fee) VALUES (?, ?, ?, ?, ?, ?, ?)", gigs)

        # Insert Gig Applications
        gig_apps = [
            (1, 3, 'Pending'),   # Employee 3 applied for gig 1
            (2, 2, 'Accepted'),  # Employee 2 applied for gig 2
            (3, 1, 'Accepted')   # Employee 1 applied for gig 3
        ]
        cursor.executemany("INSERT INTO gig_applications (gig_id, applicant_id, status) VALUES (?, ?, ?)", gig_apps)
        
        conn.commit()
    
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
