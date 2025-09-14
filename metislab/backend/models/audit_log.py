from datetime import datetime
from backend.app import db
from enum import Enum

class ActionEnum(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.Enum(ActionEnum), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # 'user', 'project_request', 'approval', etc.
    resource_id = db.Column(db.Integer, nullable=True)  # ID of the affected resource
    details = db.Column(db.Text, nullable=True)  # JSON string with additional details
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'Unknown',
            'action': self.action.value,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat()
        }

    @staticmethod
    def log_action(user_id, action, resource_type, resource_id=None, details=None, 
                   ip_address=None, user_agent=None):
        """Create a new audit log entry"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(audit_log)
            db.session.commit()
            return audit_log
        except Exception as e:
            db.session.rollback()
            # Log the error but don't fail the main operation
            print(f"Failed to create audit log: {str(e)}")
            return None
