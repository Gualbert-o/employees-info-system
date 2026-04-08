import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend')  # Use frontend for templates and static files

app.secret_key = 'super_secret_key_for_demo'

# Database path

class DBWrapper:
    def __init__(self):
        self.conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='employees-info-system',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def execute(self, sql, params=None):
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = DBWrapper()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def log_activity(activity, employee_name):
    db = get_db()
    db.execute("INSERT INTO activity_logs (activity, employee_name) VALUES (%s, %s)", (activity, employee_name))
    db.commit()

# Decorator for requiring login
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator for admin only routes
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return "Unauthorized access. Admins only.", 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session.get('role') == 'user':
            return redirect(url_for('employee_info', id=session.get('employee_id')))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password)).fetchone()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['employee_id'] = user['employee_id']
            if user['role'] == 'user':
                return redirect(url_for('employee_info', id=user['employee_id']))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('employee_info', id=session.get('employee_id')))
        
    db = get_db()
    
    # Calculate counts based on status
    employees = db.execute('SELECT status FROM employees').fetchall()
    
    stats = {
        'active': len([e for e in employees if e['status'] != 'Separated']),
        'permanent': len([e for e in employees if e['status'] == 'Permanent']),
        'non_permanent': len([e for e in employees if e['status'] == 'Non-Permanent']),
        'temporary': len([e for e in employees if e['status'] == 'Temporary']),
        'separated': len([e for e in employees if e['status'] == 'Separated'])
    }
    
    # Recent Activities
    activities = db.execute('SELECT * FROM activity_logs ORDER BY date DESC LIMIT 10').fetchall()
    
    return render_template('dashboard.html', role=session.get('role'), stats=stats, activities=activities)

@app.route('/employees')
@login_required
def employee_list():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    db = get_db()
    
    query_params = []
    base_query = "SELECT * FROM employees"
    where_clauses = []
    
    if session.get('role') != 'admin':
        where_clauses.append("id = %s")
        query_params.append(session.get('employee_id'))

    if search:
        where_clauses.append("(last_name LIKE %s OR first_name LIKE %s OR status LIKE %s)")
        query_params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
    if status:
        if status == 'Active':
            where_clauses.append("status != 'Separated'")
        else:
            where_clauses.append("status = %s")
            query_params.append(status)

    if where_clauses:
        query = base_query + " WHERE " + " AND ".join(where_clauses)
    else:
        query = base_query
        
    employees = db.execute(query, query_params).fetchall()
        
    return render_template('employee_list.html', role=session.get('role'), employees=employees, search=search)

@app.route('/employees/add', methods=['POST'])
@admin_required
def add_employee():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    status = request.form['status']
    birthday = request.form['birthday']
    
    db = get_db()
    db.execute('INSERT INTO employees (first_name, last_name, status, birthday) VALUES (%s, %s, %s, %s)', 
               (first_name, last_name, status, birthday))
    db.commit()
    log_activity('Added new employee', f'{first_name} {last_name}')
    return redirect(url_for('employee_list'))

@app.route('/employees/edit/<int:id>', methods=['POST'])
@admin_required
def edit_employee(id):
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    status = request.form['status']
    birthday = request.form['birthday']
    
    db = get_db()
    db.execute('UPDATE employees SET first_name=%s, last_name=%s, status=%s, birthday=%s WHERE id=%s', 
               (first_name, last_name, status, birthday, id))
    db.commit()
    log_activity('Edited employee', f'{first_name} {last_name}')
    return redirect(url_for('employee_list'))

@app.route('/employees/delete/<int:id>', methods=['POST'])
@admin_required
def delete_employee(id):
    db = get_db()
    emp = db.execute('SELECT first_name, last_name FROM employees WHERE id = %s', (id,)).fetchone()
    if emp:
        db.execute('DELETE FROM employees WHERE id = %s', (id,))
        db.commit()
        log_activity('Deleted employee', f'{emp["first_name"]} {emp["last_name"]}')
    return redirect(url_for('employee_list'))

@app.route('/employee-info/<int:id>')
@login_required
def employee_info(id):
    if session.get('role') != 'admin' and session.get('employee_id') != id:
        return "Unauthorized access. You can only view your own account.", 403

    db = get_db()
    employee = db.execute('SELECT * FROM employees WHERE id = %s', (id,)).fetchone()
    if not employee:
        return "Employee not found", 404
        
    trainings = db.execute('SELECT * FROM trainings WHERE employee_id = %s ORDER BY date DESC LIMIT 5', (id,)).fetchall()
    service_records = db.execute('SELECT * FROM service_records WHERE employee_id = %s ORDER BY start_date DESC LIMIT 5', (id,)).fetchall()
    skills = db.execute('SELECT * FROM skills WHERE employee_id = %s', (id,)).fetchall()
    
    # Get completed gigs for this employee
    completed_gigs = db.execute('SELECT * FROM gigs WHERE awarded_to = %s AND status = "Completed"', (id,)).fetchall()
    
    # Calculate average rating
    ratings = [g['rating'] for g in completed_gigs if g['rating'] is not None]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    total_fee = sum([g['fee'] for g in completed_gigs if g['fee']])
    
    return render_template('employee-info.html', role=session.get('role'), 
                           employee=employee, trainings=trainings, 
                           service_records=service_records, skills=skills,
                           completed_gigs=completed_gigs, avg_rating=avg_rating, total_fee=total_fee)

@app.route('/trainings')
@login_required
def trainings():
    search = request.args.get('search', '')
    db = get_db()
    
    query_params = []
    base_query = "SELECT t.*, e.first_name, e.last_name FROM trainings t JOIN employees e ON t.employee_id = e.id"
    where_clauses = []

    if session.get('role') != 'admin':
        where_clauses.append("t.employee_id = %s")
        query_params.append(session.get('employee_id'))
        
    if search:
        where_clauses.append("(t.title LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s)")
        query_params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    if where_clauses:
        query = base_query + " WHERE " + " AND ".join(where_clauses)
    else:
        query = base_query
        
    records = db.execute(query, query_params).fetchall()
    employees = db.execute('SELECT id, first_name, last_name FROM employees').fetchall()
        
    return render_template('trainings.html', role=session.get('role'), trainings=records, search=search, employees=employees)

@app.route('/trainings/add', methods=['POST'])
@admin_required
def add_training():
    employee_id = request.form['employee_id']
    title = request.form['title']
    date = request.form['date']
    
    db = get_db()
    db.execute('INSERT INTO trainings (employee_id, title, date) VALUES (%s, %s, %s)', (employee_id, title, date))
    db.commit()
    
    emp = db.execute('SELECT first_name, last_name FROM employees WHERE id=%s', (employee_id,)).fetchone()
    return redirect(url_for('trainings'))

@app.route('/trainings/edit/<int:id>', methods=['POST'])
@admin_required
def edit_training(id):
    employee_id = request.form['employee_id']
    title = request.form['title']
    date = request.form['date']
    
    db = get_db()
    db.execute('UPDATE trainings SET employee_id=%s, title=%s, date=%s WHERE id=%s', (employee_id, title, date, id))
    db.commit()
    
    emp = db.execute('SELECT first_name, last_name FROM employees WHERE id=%s', (employee_id,)).fetchone()
    if emp:
        log_activity('Edited training record', f'{emp["first_name"]} {emp["last_name"]}')
    
    return redirect(url_for('trainings'))

@app.route('/trainings/delete/<int:id>', methods=['POST'])
@admin_required
def delete_training(id):
    db = get_db()
    training = db.execute('SELECT employee_id FROM trainings WHERE id = %s', (id,)).fetchone()
    if training:
        db.execute('DELETE FROM trainings WHERE id = %s', (id,))
        db.commit()
        emp = db.execute('SELECT first_name, last_name FROM employees WHERE id=%s', (training['employee_id'],)).fetchone()
        log_activity('Deleted training record', f'{emp["first_name"]} {emp["last_name"]}')
    return redirect(url_for('trainings'))

@app.route('/service-record')
@login_required
def service_record():
    search = request.args.get('search', '')
    db = get_db()
    
    query_params = []
    base_query = "SELECT s.*, e.first_name, e.last_name FROM service_records s JOIN employees e ON s.employee_id = e.id"
    where_clauses = []
    
    if session.get('role') != 'admin':
        where_clauses.append("s.employee_id = %s")
        query_params.append(session.get('employee_id'))
        
    if search:
        where_clauses.append("(s.position LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s)")
        query_params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    if where_clauses:
        query = base_query + " WHERE " + " AND ".join(where_clauses)
    else:
        query = base_query
        
    records = db.execute(query, query_params).fetchall()
    employees = db.execute('SELECT id, first_name, last_name FROM employees').fetchall()
        
    return render_template('service-record.html', role=session.get('role'), service_records=records, search=search, employees=employees)

@app.route('/service-record/add', methods=['POST'])
@admin_required
def add_service_record():
    employee_id = request.form['employee_id']
    position = request.form['position']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    if not end_date:
        end_date = None
        
    db = get_db()
    db.execute('INSERT INTO service_records (employee_id, position, start_date, end_date) VALUES (%s, %s, %s, %s)', 
               (employee_id, position, start_date, end_date))
    db.commit()
    
    emp = db.execute('SELECT first_name, last_name FROM employees WHERE id=%s', (employee_id,)).fetchone()
    log_activity('Added service record', f'{emp["first_name"]} {emp["last_name"]}')
    
    return redirect(url_for('service_record'))

@app.route('/service-record/edit/<int:id>', methods=['POST'])
@admin_required
def edit_service_record(id):
    employee_id = request.form['employee_id']
    position = request.form['position']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    if not end_date:
        end_date = None
        
    db = get_db()
    db.execute('UPDATE service_records SET employee_id=%s, position=%s, start_date=%s, end_date=%s WHERE id=%s', 
               (employee_id, position, start_date, end_date, id))
    db.commit()
    
    emp = db.execute('SELECT first_name, last_name FROM employees WHERE id=%s', (employee_id,)).fetchone()
    if emp:
        log_activity('Edited service record', f'{emp["first_name"]} {emp["last_name"]}')
    
    return redirect(url_for('service_record'))

@app.route('/service-record/delete/<int:id>', methods=['POST'])
@admin_required
def delete_service_record(id):
    db = get_db()
    record = db.execute('SELECT employee_id FROM service_records WHERE id = %s', (id,)).fetchone()
    if record:
        db.execute('DELETE FROM service_records WHERE id = %s', (id,))
        db.commit()
        emp = db.execute('SELECT first_name, last_name FROM employees WHERE id=%s', (record['employee_id'],)).fetchone()
        log_activity('Deleted service record', f'{emp["first_name"]} {emp["last_name"]}')
    return redirect(url_for('service_record'))

# --- Marketplace Routes ---

@app.route('/marketplace')
@login_required
def marketplace():
    db = get_db()
    
    # Get all open/visible gigs
    if session.get('role') == 'admin':
        gigs = db.execute('''
            SELECT g.*, e.first_name, e.last_name 
            FROM gigs g 
            JOIN employees e ON g.posted_by = e.id 
            ORDER BY g.created_at DESC
        ''').fetchall()
    else:
        gigs = db.execute('''
            SELECT g.*, e.first_name, e.last_name 
            FROM gigs g 
            JOIN employees e ON g.posted_by = e.id 
            WHERE g.posted_by = %s 
               OR g.status = 'Open' 
               OR (g.status IN ('In Progress', 'Awaiting Review', 'Completed') AND g.awarded_to = %s)
            ORDER BY g.created_at DESC
        ''', (session.get('employee_id'), session.get('employee_id'))).fetchall()
    
    # If user, get recommended gigs based on skills
    recommended = []
    if session.get('employee_id'):
        user_skills = [s['skill_name'].lower() for s in db.execute('SELECT skill_name FROM skills WHERE employee_id = %s', (session['employee_id'],)).fetchall()]
        
        for gig in gigs:
            if gig['status'] == 'Open' and gig['posted_by'] != session.get('employee_id'):
                # Simple keyword matching for recommendation
                gig_desc = gig['description'].lower() + " " + gig['title'].lower()
                if any(skill in gig_desc for skill in user_skills):
                    recommended.append(gig)
    
    # Get user's applications
    my_apps = []
    if session.get('employee_id'):
        my_apps = [a['gig_id'] for a in db.execute('SELECT gig_id FROM gig_applications WHERE applicant_id = %s', (session['employee_id'],)).fetchall()]

    # Get recent/pending applications on gigs posted by this user (or all if admin)
    gig_applications = []
    if session.get('role') == 'admin':
        gig_applications = db.execute('''
            SELECT ga.*, e.first_name, e.last_name, g.title 
            FROM gig_applications ga
            JOIN employees e ON ga.applicant_id = e.id
            JOIN gigs g ON ga.gig_id = g.id
            WHERE ga.status = 'Pending'
        ''').fetchall()
    elif session.get('employee_id'):
        gig_applications = db.execute('''
            SELECT ga.*, e.first_name, e.last_name, g.title 
            FROM gig_applications ga
            JOIN employees e ON ga.applicant_id = e.id
            JOIN gigs g ON ga.gig_id = g.id
            WHERE ga.status = 'Pending' AND g.posted_by = %s
        ''', (session['employee_id'],)).fetchall()

    return render_template('marketplace.html', role=session.get('role'), 
                           gigs=gigs, recommended=recommended, my_apps=my_apps, 
                           current_emp=session.get('employee_id'),
                           gig_applications=gig_applications)

@app.route('/marketplace/post', methods=['POST'])
@login_required
def post_gig():
    title = request.form['title']
    description = request.form['description']
    fee = request.form.get('fee', 10, type=int)
    posted_by = session.get('employee_id')
    status = 'Open' if session.get('role') == 'admin' else 'Pending Approval'
    
    if not posted_by:
        flash("You need an associated employee profile to post gigs.")
        return redirect(url_for('marketplace'))
        
    db = get_db()
    db.execute('INSERT INTO gigs (title, description, posted_by, fee, status) VALUES (%s, %s, %s, %s, %s)',
               (title, description, posted_by, fee, status))
    db.commit()
    log_activity('Requested a Gig', session.get('username'))
    
    return redirect(url_for('marketplace'))

@app.route('/marketplace/approve_gig/<int:gig_id>', methods=['POST'])
@admin_required
def approve_gig(gig_id):
    db = get_db()
    db.execute('UPDATE gigs SET status = "Open" WHERE id = %s', (gig_id,))
    db.commit()
    return redirect(url_for('marketplace'))

@app.route('/marketplace/submit_work/<int:gig_id>', methods=['POST'])
@login_required
def submit_work(gig_id):
    db = get_db()
    gig = db.execute('SELECT * FROM gigs WHERE id = %s AND awarded_to = %s AND status = "In Progress"', (gig_id, session.get('employee_id'))).fetchone()
    if gig:
        db.execute('UPDATE gigs SET status = "Awaiting Review" WHERE id = %s', (gig_id,))
        db.commit()
        log_activity('Submitted Work for Gig', session.get('username'))
    return redirect(url_for('marketplace'))

@app.route('/marketplace/apply/<int:gig_id>', methods=['POST'])
@login_required
def apply_gig(gig_id):
    applicant_id = session.get('employee_id')
    if not applicant_id:
        flash("You need an associated employee profile to apply.")
        return redirect(url_for('marketplace'))
        
    db = get_db()
    # Ensure they haven't applied already
    existing = db.execute('SELECT id FROM gig_applications WHERE gig_id=%s AND applicant_id=%s', (gig_id, applicant_id)).fetchone()
    if not existing:
        db.execute('INSERT INTO gig_applications (gig_id, applicant_id) VALUES (%s, %s)', (gig_id, applicant_id))
        db.commit()
        log_activity('Applied for Gig', session.get('username'))
        
    return redirect(url_for('marketplace'))

@app.route('/marketplace/accept/<int:app_id>', methods=['POST'])
@login_required
def accept_gig_application(app_id):
    db = get_db()
    application = db.execute('SELECT * FROM gig_applications WHERE id = %s', (app_id,)).fetchone()
    if not application:
        return "Not found", 404
        
    gig = db.execute('SELECT * FROM gigs WHERE id = %s', (application['gig_id'],)).fetchone()
    if gig['posted_by'] != session.get('employee_id') and session.get('role') != 'admin':
        return "Unauthorized", 403
        
    # Accept this app, reject others
    db.execute('UPDATE gig_applications SET status = "Accepted" WHERE id = %s', (app_id,))
    db.execute('UPDATE gig_applications SET status = "Rejected" WHERE gig_id = %s AND id != %s', (gig['id'], app_id))
    
    # Update gig
    db.execute('UPDATE gigs SET status = "In Progress", awarded_to = %s WHERE id = %s', (application['applicant_id'], gig['id']))
    db.commit()
    
    return redirect(url_for('marketplace'))

@app.route('/marketplace/complete/<int:gig_id>', methods=['POST'])
@login_required
def complete_gig(gig_id):
    rating = request.form.get('rating', type=int)
    db = get_db()
    gig = db.execute('SELECT * FROM gigs WHERE id = %s', (gig_id,)).fetchone()
    
    if not gig:
        return "Not found", 404
        
    if gig['posted_by'] != session.get('employee_id') and session.get('role') != 'admin':
        return "Unauthorized", 403
        
    db.execute('UPDATE gigs SET status = "Completed", rating = %s WHERE id = %s', (rating, gig_id))
    db.commit()
    log_activity('Completed a Gig', session.get('username'))
    
    return redirect(url_for('marketplace'))

@app.route('/profile/add_skill', methods=['POST'])
@login_required
def add_skill():
    skill_name = request.form['skill_name']
    employee_id = session.get('employee_id')
    if employee_id:
        db = get_db()
        db.execute('INSERT INTO skills (employee_id, skill_name) VALUES (%s, %s)', (employee_id, skill_name))
        db.commit()
    return redirect(url_for('employee_info', id=employee_id))

