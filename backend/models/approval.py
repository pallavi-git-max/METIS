from datetime import datetime
from .database import db

class Approval(db.Model):
    __tablename__ = 'approvals'

    id = db.Column(db.Integer, primary_key=True)
    project_request_id = db.Column(db.Integer, db.ForeignKey('project_requests.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved = db.Column(db.Boolean, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    project_request = db.relationship('ProjectRequest', backref='approval')
    admin = db.relationship('User', backref='approvals')
