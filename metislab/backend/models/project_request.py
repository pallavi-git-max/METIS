from datetime import datetime
from enum import Enum
from backend.app import db

class StatusEnum(str, Enum):
    pending = "pending"
    lab_incharge_approved = "lab_incharge_approved"
    faculty_approved = "faculty_approved"
    hod_approved = "hod_approved"
    approved = "approved"
    rejected = "rejected"

class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class ProjectRequest(db.Model):
    __tablename__ = 'project_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    purpose = db.Column(db.String(500), nullable=False)
    expected_duration = db.Column(db.String(100), nullable=True)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.medium, nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.pending, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    hod_approved_at = db.Column(db.DateTime, nullable=True)
    faculty_approved_at = db.Column(db.DateTime, nullable=True)
    lab_incharge_approved_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'project_title': self.project_title,
            'description': self.description,
            'purpose': self.purpose,
            'expected_duration': self.expected_duration,
            'priority': self.priority.value,
            'status': self.status.value,
            'submitted_at': self.submitted_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'rejection_reason': self.rejection_reason,
            'hod_approved_at': self.hod_approved_at.isoformat() if self.hod_approved_at else None,
            'faculty_approved_at': self.faculty_approved_at.isoformat() if self.faculty_approved_at else None,
            'lab_incharge_approved_at': self.lab_incharge_approved_at.isoformat() if self.lab_incharge_approved_at else None,
            'updated_at': self.updated_at.isoformat()
        }

    def approve_by_role(self, role):
        """Approve request by specific role - Lab In-charge → Faculty → HOD → Admin"""
        now = datetime.utcnow()
        if role == 'lab_incharge':
            self.status = StatusEnum.lab_incharge_approved
            self.lab_incharge_approved_at = now
        elif role == 'faculty':
            self.status = StatusEnum.faculty_approved
            self.faculty_approved_at = now
        elif role == 'hod':
            self.status = StatusEnum.hod_approved
            self.hod_approved_at = now
        elif role == 'admin':
            self.status = StatusEnum.approved
            self.approved_at = now
        self.updated_at = now

    def reject_request(self, reason):
        """Reject the request with a reason"""
        self.status = StatusEnum.rejected
        self.rejected_at = datetime.utcnow()
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
