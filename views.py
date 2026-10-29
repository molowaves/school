import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from extensions import db
from models import Admin, Enquiry


main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)


def csrf_valid():
    return secrets.compare_digest(
        session.get('_csrf_token', ''),
        request.form.get('_csrf_token', ''),
    )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin.login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


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
    created_at = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    db.session.add(Enquiry(**data, created_at=created_at))
    db.session.commit()


@main_bp.route('/')
def home():
    return render_template('index.html', title='Welcome')


@main_bp.route('/about')
def about():
    return render_template('about.html', title='About Us')


@main_bp.route('/academics')
def academics():
    return render_template('academics.html', title='Academics')


@main_bp.route('/admissions', methods=['GET', 'POST'])
def admissions():
    if request.method == 'POST':
        if not csrf_valid():
            abort(400, 'Your form session expired. Please reload and try again.')
        if request.form.get('website', '').strip():
            flash('Thank you. Your enquiry has been received.', 'success')
            return redirect(url_for('main.admissions'))
        data = collect_form('admissions')
        errors = validate_form(data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admissions.html', title='Admissions', form=data), 400
        save_enquiry(data)
        flash('Thank you! Your admissions enquiry has been submitted. Our team will contact you.', 'success')
        return redirect(url_for('main.admissions'))
    return render_template('admissions.html', title='Admissions', form={})


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        if not csrf_valid():
            abort(400, 'Your form session expired. Please reload and try again.')
        if request.form.get('website', '').strip():
            flash('Thank you. Your message has been received.', 'success')
            return redirect(url_for('main.contact'))
        data = collect_form('contact')
        errors = validate_form(data, contact_only=True)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('contact.html', title='Contact Us', form=data), 400
        save_enquiry(data)
        flash('Your message has been sent successfully. Thank you for contacting us.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', title='Contact Us', form={})


@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_id'):
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        if not csrf_valid():
            abort(400)
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session.clear()
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session['_csrf_token'] = secrets.token_urlsafe(32)
            return redirect(url_for('admin.dashboard'))
        flash('Incorrect username or password.', 'error')
    return render_template('admin_login.html', title='Admin Login')


@admin_bp.route('/admin')
@admin_required
def dashboard():
    status = request.args.get('status', '').strip()
    kind = request.args.get('kind', '').strip()
    query = Enquiry.query
    if status in ('New', 'Contacted', 'Closed'):
        query = query.filter_by(status=status)
    if kind in ('admissions', 'contact'):
        query = query.filter_by(kind=kind)
    enquiries = query.order_by(Enquiry.id.desc()).limit(500).all()
    total = db.session.query(db.func.count(Enquiry.id)).scalar()
    new_count = Enquiry.query.filter_by(status='New').count()
    return render_template(
        'admin_dashboard.html',
        title='Enquiries Dashboard',
        enquiries=enquiries,
        total=total,
        new_count=new_count,
        current_status=status,
        current_kind=kind,
    )


@admin_bp.route('/admin/enquiry/<int:enquiry_id>/status', methods=['POST'])
@admin_required
def update_status(enquiry_id):
    if not csrf_valid():
        abort(400)
    status = request.form.get('status', '')
    if status not in ('New', 'Contacted', 'Closed'):
        abort(400)
    enquiry = db.session.get(Enquiry, enquiry_id)
    if enquiry is not None:
        enquiry.status = status
        db.session.commit()
    flash('Enquiry status updated.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/logout', methods=['POST'])
@admin_required
def logout():
    if not csrf_valid():
        abort(400)
    session.clear()
    flash('You have been signed out.', 'success')
    return redirect(url_for('main.home'))
