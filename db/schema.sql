CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL, -- 'admin' or 'user'
    employee_id INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    birthday DATE,
    status TEXT NOT NULL -- 'Permanent', 'Non-Permanent', 'Temporary', 'Separated'
);

CREATE TABLE IF NOT EXISTS trainings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS service_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    position TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gigs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    posted_by INTEGER NOT NULL, -- employee_id
    status TEXT NOT NULL DEFAULT 'Open', -- 'Pending Approval', 'Open', 'In Progress', 'Awaiting Review', 'Completed'
    awarded_to INTEGER, -- employee_id
    rating INTEGER,
    fee INTEGER DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES employees (id) ON DELETE CASCADE,
    FOREIGN KEY (awarded_to) REFERENCES employees (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS gig_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gig_id INTEGER NOT NULL,
    applicant_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'Accepted', 'Rejected'
    FOREIGN KEY (gig_id) REFERENCES gigs (id) ON DELETE CASCADE,
    FOREIGN KEY (applicant_id) REFERENCES employees (id) ON DELETE CASCADE
);
