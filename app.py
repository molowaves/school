import os
import secrets
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import check_password_hash, generate_password_hash



BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get('VERITAS_DATABASE', os.path.join(BASE_DIR, 'veritas.db'))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

SCHOOL = {
    'name': os.environ.get('SCHOOL_NAME', 'Veritas International Schools'),
    'tagline': 'Big dreams. Brilliant minds. Boundless futures.',
    'phone': os.environ.get('SCHOOL_PHONE', '+234 000 000 0000'),
    'email': os.environ.get('SCHOOL_EMAIL', 'info@example.com'),
    'address': os.environ.get('SCHOOL_ADDRESS', 'Add your school address'),
    'whatsapp': os.environ.get('SCHOOL_WHATSAPP', ''),
}


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            student_name TEXT DEFAULT '',
            year_group TEXT DEFAULT '',
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'New'
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )''')
        # Create the first admin only when credentials are explicitly configured.
        username = os.environ.get('ADMIN_USERNAME')
        password = os.environ.get('ADMIN_PASSWORD')
        if username and password:
            exists = conn.execute('SELECT id FROM admins WHERE username = ?', (username,)).fetchone()
            if not exists:
                conn.execute('INSERT INTO admins (username, password_hash) VALUES (?, ?)',
                             (username, generate_password_hash(password)))


@app.before_request
def ensure_csrf_token():
    session.setdefault('_csrf_token', secrets.token_urlsafe(32))


def csrf_valid():
    return secrets.compare_digest(session.get('_csrf_token', ''), request.form.get('_csrf_token', ''))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {'school': SCHOOL, 'csrf_token': session.get('_csrf_token', '')}


@app.route('/')
def home():
    return render_template('index.html', title='Welcome')


@app.route('/about')
def about():
    return render_template('about.html', title='About Us')


@app.route('/academics')
def academics():
    return render_template('academics.html', title='Academics')


@app.route('/admissions', methods=['GET', 'POST'])
def admissions():
    if request.method == 'POST':
        if not csrf_valid():
            abort(400, 'Your form session expired. Please reload and try again.')
        if request.form.get('website', '').strip():  # honeypot anti-spam field
            flash('Thank you. Your enquiry has been received.', 'success')
            return redirect(url_for('admissions'))
        data = collect_form('admissions')
        errors = validate_form(data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admissions.html', title='Admissions', form=data), 400
        save_enquiry(data)
        flash('Thank you! Your admissions enquiry has been submitted. Our team will contact you.', 'success')
        return redirect(url_for('admissions'))
    return render_template('admissions.html', title='Admissions', form={})


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        if not csrf_valid():
            abort(400, 'Your form session expired. Please reload and try again.')
        if request.form.get('website', '').strip():
            flash('Thank you. Your message has been received.', 'success')
            return redirect(url_for('contact'))
        data = collect_form('contact')
        errors = validate_form(data, contact_only=True)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('contact.html', title='Contact Us', form=data), 400
        save_enquiry(data)
        flash('Your message has been sent successfully. Thank you for contacting us.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', title='Contact Us', form={})


def collect_form(kind):
    return {
        'kind': kind,
        'parent_name': request.form.get('parent_name', '').strip()[:120],
        'email': request.form.get('email', '').strip()[:254],
        'phone': request.form.get('phone', '').strip()[:40],
        'student_name': request.form.get('student_name', '').strip()[:120],
        'year_group': request.form.get('year_group', '').strip()[:80],
        'message': request.form.get('message', '').strip()[:3000],
    }


def validate_form(data, contact_only=False):
    errors = []
    if not data['parent_name']:
        errors.append('Please enter your name.')
    if not data['email'] or '@' not in data['email'] or '.' not in data['email'].split('@')[-1]:
        errors.append('Please enter a valid email address.')
    if not data['phone']:
        errors.append('Please enter a phone number.')
    if not data['message']:
        errors.append('Please enter a message.')
    if not contact_only and not data['year_group']:
        errors.append('Please select the class or year group of interest.')
    return errors


def save_enquiry(data):
    with db() as conn:
        conn.execute('''INSERT INTO enquiries
            (kind, parent_name, email, phone, student_name, year_group, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['kind'], data['parent_name'], data['email'], data['phone'], data['student_name'],
             data['year_group'], data['message'], datetime.utcnow().isoformat(timespec='seconds') + 'Z'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_id'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        if not csrf_valid():
            abort(400)
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        with db() as conn:
            admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        if admin and check_password_hash(admin['password_hash'], password):
            session.clear()
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['_csrf_token'] = secrets.token_urlsafe(32)
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect username or password.', 'error')
    return render_template('admin_login.html', title='Admin Login')


@app.route('/admin')
@admin_required
def admin_dashboard():
    status = request.args.get('status', '').strip()
    kind = request.args.get('kind', '').strip()
    query = 'SELECT * FROM enquiries WHERE 1=1'
    params = []
    if status in ('New', 'Contacted', 'Closed'):
        query += ' AND status = ?'; params.append(status)
    if kind in ('admissions', 'contact'):
        query += ' AND kind = ?'; params.append(kind)
    query += ' ORDER BY id DESC LIMIT 500'
    with db() as conn:
        enquiries = conn.execute(query, params).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]
        new_count = conn.execute("SELECT COUNT(*) FROM enquiries WHERE status='New'").fetchone()[0]
    return render_template('admin_dashboard.html', title='Enquiries Dashboard', enquiries=enquiries,
                           total=total, new_count=new_count, current_status=status, current_kind=kind)


@app.route('/admin/enquiry/<int:enquiry_id>/status', methods=['POST'])
@admin_required
def update_status(enquiry_id):
    if not csrf_valid():
        abort(400)
    status = request.form.get('status', '')
    if status not in ('New', 'Contacted', 'Closed'):
        abort(400)
    with db() as conn:
        conn.execute('UPDATE enquiries SET status = ? WHERE id = ?', (status, enquiry_id))
    flash('Enquiry status updated.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    if not csrf_valid():
        abort(400)
    session.clear()
    flash('You have been signed out.', 'success')
    return redirect(url_for('home'))


@app.errorhandler(400)
def bad_request(error):
    return render_template('error.html', title='Request Error', message=getattr(error, 'description', 'The request could not be processed.')), 400


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', title='Page Not Found', message='Sorry, that page could not be found.'), 404


init_db()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
