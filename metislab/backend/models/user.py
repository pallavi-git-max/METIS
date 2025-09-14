from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.app import db, login_manager
from enum import Enum

class RoleEnum(str, Enum):
    student = "student"
    faculty = "faculty"
    lab_incharge = "lab_incharge"
    hod = "hod"
    admin = "admin"

class DepartmentEnum(str, Enum):
    computer_science = "computer_science"
    electronics = "electronics"
    mechanical = "mechanical"
    civil = "civil"
    electrical = "electrical"

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    department = db.Column(db.Enum(DepartmentEnum), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project_requests = db.relationship('ProjectRequest', backref='user', lazy=True)
    ndas = db.relationship('NDA', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self.is_active

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
        return self.role in [RoleEnum.faculty, RoleEnum.lab_incharge, RoleEnum.hod]

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role.value,
            'department': self.department.value if self.department else None,
            'designation': self.designation,
            'student_id': self.student_id,
            'phone': self.phone,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
