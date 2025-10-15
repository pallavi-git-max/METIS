from datetime import datetime
from enum import Enum
from .database import db

class StatusEnum(str, Enum):
    pending = "pending"
    guide_approved = "guide_approved"
    hod_approved = "hod_approved"
    it_services_approved = "it_services_approved"
    approved = "approved"
    rejected = "rejected"
    closed = "closed"

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
    guide_email = db.Column(db.String(255), nullable=True)  # Project guide's email
    expected_duration = db.Column(db.String(100), nullable=True)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.medium, nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.pending, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    guide_approved_at = db.Column(db.DateTime, nullable=True)
    hod_approved_at = db.Column(db.DateTime, nullable=True)
    it_services_approved_at = db.Column(db.DateTime, nullable=True)
    guide_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    hod_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    it_services_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'project_title': self.project_title,
            'description': self.description,
            'purpose': self.purpose,
            'guide_email': self.guide_email,
            'expected_duration': self.expected_duration,
            'priority': self.priority.value,
            'status': self.status.value,
            'submitted_at': self.submitted_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'rejection_reason': self.rejection_reason,
            'guide_approved_at': self.guide_approved_at.isoformat() if self.guide_approved_at else None,
            'hod_approved_at': self.hod_approved_at.isoformat() if self.hod_approved_at else None,
            'it_services_approved_at': self.it_services_approved_at.isoformat() if self.it_services_approved_at else None,
            'guide_approved_by': self.guide_approved_by,
            'hod_approved_by': self.hod_approved_by,
            'it_services_approved_by': self.it_services_approved_by,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'closed_by': self.closed_by,
            'updated_at': self.updated_at.isoformat()
        }

    def approve_by_role(self, role, approver_id=None):
        """Approve request by specific role - Guide → HOD → IT Services → Final Approval"""
        now = datetime.utcnow()
        if role == 'guide':
            self.status = StatusEnum.guide_approved
            self.guide_approved_at = now
            self.guide_approved_by = approver_id
        elif role == 'hod':
            self.status = StatusEnum.hod_approved
            self.hod_approved_at = now
            self.hod_approved_by = approver_id
        elif role == 'it_services':
            self.status = StatusEnum.it_services_approved
            self.it_services_approved_at = now
            self.it_services_approved_by = approver_id
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
