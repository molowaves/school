from extensions import db


class Enquiry(db.Model):
    __tablename__ = 'enquiries'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String, nullable=False)
    parent_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    student_name = db.Column(db.String, nullable=False, default='')
    year_group = db.Column(db.String, nullable=False, default='')
    message = db.Column(db.String, nullable=False)
    created_at = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default='New')


class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
