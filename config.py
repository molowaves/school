import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


load_dotenv()


def database_uri():
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    if database_url:
        url = make_url(database_url)
        if url.drivername in ('postgres', 'postgresql'):
            url = url.set(drivername='postgresql+psycopg')
        if url.drivername.startswith('postgresql') and 'sslmode' not in url.query:
            url = url.update_query_dict({'sslmode': 'require'})
        return url.render_as_string(hide_password=False)

    database_path = Path(os.environ.get(
        'VERITAS_DATABASE',
        str(Path(__file__).resolve().parent / 'veritas.db'),
    ))
    return URL.create('sqlite', database=str(database_path)).render_as_string(hide_password=False)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    SQLALCHEMY_DATABASE_URI = database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG') == '1'
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    SCHOOL = {
        'name': os.environ.get('SCHOOL_NAME', 'Veritas International Schools'),
        'tagline': 'Big dreams. Brilliant minds. Boundless futures.',
        'phone': os.environ.get('SCHOOL_PHONE', '+234 000 000 0000'),
        'email': os.environ.get('SCHOOL_EMAIL', 'info@example.com'),
        'address': os.environ.get('SCHOOL_ADDRESS', 'Add your school address'),
        'whatsapp': os.environ.get('SCHOOL_WHATSAPP', ''),
    }
