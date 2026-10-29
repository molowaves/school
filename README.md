# Veritas International Schools — Flask Website

A responsive Flask website starter for a nursery/early-years, primary and secondary school. It includes public pages, admissions and contact forms, SQLAlchemy-backed SQLite/PostgreSQL storage, a protected staff dashboard, enquiry status management, CSRF protection, basic form validation and a spam honeypot.

## What's included

- Home, About, Academics, Admissions and Contact pages
- Responsive design for desktop, tablet and mobile
- Admissions enquiry form and general contact form
- Enquiries stored through Flask-SQLAlchemy in local SQLite or production PostgreSQL (no third-party form service needed)
- Admin sign-in and dashboard to view enquiries and update their status
- Parameterized SQL queries, password hashing, session-based admin access, CSRF tokens, basic input limits and honeypot anti-spam field
- Gunicorn start command for compatible hosts

## 1. Run locally

You need Python 3.10 or newer.

### Windows PowerShell

```powershell
cd veritas_flask_site
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_USERNAME = "schooladmin"
$env:ADMIN_PASSWORD = "use-a-long-unique-password-here"
$env:SCHOOL_PHONE = "+234 801 234 5678"
$env:SCHOOL_EMAIL = "admissions@your-school-domain.example"
$env:SCHOOL_ADDRESS = "Your full school address"
$env:SCHOOL_WHATSAPP = "2348012345678"
python app.py
```

### macOS / Linux

```bash
cd veritas_flask_site
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="replace-with-a-long-random-secret"
export ADMIN_USERNAME="schooladmin"
export ADMIN_PASSWORD="use-a-long-unique-password-here"
export SCHOOL_PHONE="+234 801 234 5678"
export SCHOOL_EMAIL="admissions@your-school-domain.example"
export SCHOOL_ADDRESS="Your full school address"
export SCHOOL_WHATSAPP="2348012345678"
python app.py
```

Open http://127.0.0.1:5000 in your browser. The admin login is at http://127.0.0.1:5000/admin/login.

**Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` before the first app launch.** The first admin is created on startup if those environment variables are present and the username does not already exist. If you change the password later, update the admin account through a planned password-reset procedure or recreate the database only if you are comfortable deleting all enquiries.

## 2. Configure the school details

Set these environment variables in your `.env` file locally or in your hosting dashboard:

- `SECRET_KEY`: long, random, private value; required for production
- `ADMIN_USERNAME`: admin username, set before first launch
- `ADMIN_PASSWORD`: strong unique password, set before first launch
- `DATABASE_URL`: PostgreSQL connection URL; use the pooled Neon URL for Vercel. PostgreSQL URLs use SSL by default.
- `SCHOOL_NAME`: defaults to Veritas International Schools
- `SCHOOL_PHONE`: official school phone
- `SCHOOL_EMAIL`: official school email
- `SCHOOL_ADDRESS`: official school address
- `SCHOOL_WHATSAPP`: WhatsApp number in international digits, e.g. `2348012345678` (no plus sign)
- `VERITAS_DATABASE`: optional path to a SQLite file when `DATABASE_URL` is not set; defaults to `veritas.db`

The app creates missing tables at startup. Existing SQLite data stays in the SQLite file; switching to PostgreSQL does not transfer it automatically.

Replace placeholder contact details before launch. The programme descriptions are starter copy; confirm that they accurately reflect the school's actual offerings and curriculum.

## 3. Deploying

This project can run on a Python web host that supports Flask/Gunicorn. The included `Procfile` uses:

```bash
gunicorn app:app
```

Add the environment variables above in your hosting provider's dashboard. For Vercel with Neon, set `DATABASE_URL` to Neon's pooled connection URL and keep the database credentials private. SQLite is intended for local development; use PostgreSQL in production because serverless filesystems are not persistent. Test backups and restore procedures before collecting real enquiries.

A custom domain is optional and usually costs extra. Hosting may provide a free subdomain and HTTPS, depending on provider.

## 4. Important production checklist

- Use a strong private `SECRET_KEY`; never deploy the example or a development secret.
- Set strong, unique admin credentials and keep them out of source control.
- Enable HTTPS through the host.
- Use a managed PostgreSQL database such as Neon in production and test backups and restore procedures.
- Confirm all phone, email, address, WhatsApp, curriculum and admissions information.
- The enquiry forms save submissions to the admin dashboard; **they do not automatically email the school**. Add a verified email provider/SMTP configuration if email notifications are required.
- This is a practical starter, not a substitute for a full security review. Limit access to student/parent data, establish retention and deletion rules, and publish an appropriate privacy notice before launch.
- Images are loaded from Unsplash and fonts from Google Fonts, so the visitor's browser needs internet access to display those remote assets. Replace with properly licensed local assets if preferred.

## Project structure

```text
veritas_flask_site/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── views.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   ├── academics.html
│   ├── admissions.html
│   ├── contact.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── error.html
└── static/
    └── style.css
```
