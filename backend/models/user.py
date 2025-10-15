from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .database import db, login_manager
from enum import Enum

class RoleEnum(str, Enum):
    student = "student"
    faculty = "faculty"
    project_guide = "project_guide"
    hod = "hod"
    it_services = "it_services"
    admin = "admin"
    external = "external"

class DepartmentEnum(str, Enum):
    computer_science = "computer_science"
    electronics = "electronics"
    mechanical = "mechanical"
    civil = "civil"
    electrical = "electrical"

class CampusEnum(str, Enum):
    central_campus = "Central Campus"
    kengeri_campus = "Kengeri Campus"
    yeshwanthpur_campus = "Yeshwanthpur Campus"
    bannerghatta_campus = "Bannerghatta Campus"
    delhi_ncr = "Delhi NCR"
    pune_lavasa_campus = "Pune Lavasa Campus"

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    department = db.Column(db.String(200), nullable=False)
    campus = db.Column(db.Enum(CampusEnum), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    aadhar_card = db.Column(db.String(12), nullable=True)
    profession = db.Column(db.String(100), nullable=True)
    institution = db.Column(db.String(200), nullable=True)
    address = db.Column(db.Text, nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_temp_password = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project_requests = db.relationship('ProjectRequest', foreign_keys='ProjectRequest.user_id', backref='user', lazy=True)
    guide_approved_requests = db.relationship('ProjectRequest', foreign_keys='ProjectRequest.guide_approved_by', backref='guide_approver', lazy=True)
    hod_approved_requests = db.relationship('ProjectRequest', foreign_keys='ProjectRequest.hod_approved_by', backref='hod_approver', lazy=True)
    it_services_approved_requests = db.relationship('ProjectRequest', foreign_keys='ProjectRequest.it_services_approved_by', backref='it_services_approver', lazy=True)
    ndas = db.relationship('NDA', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Use UserMixin's default properties for authentication state

    def get_id(self):
        return str(self.id)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role == RoleEnum.admin

    @property
    def is_faculty(self):
        return self.role in [RoleEnum.faculty, RoleEnum.project_guide, RoleEnum.hod, RoleEnum.it_services]

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role.value,
            'department': self.department,
            'campus': self.campus.value if self.campus else None,
            'designation': self.designation,
            'student_id': self.student_id,
            'phone': self.phone,
            'aadhar_card': self.aadhar_card,
            'profession': self.profession,
            'institution': self.institution,
            'pincode': self.pincode,
            'city': self.city,
            'state': self.state,
            'profile_photo': self.profile_photo,
            'is_active': self.is_active,
            'is_temp_password': self.is_temp_password,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
