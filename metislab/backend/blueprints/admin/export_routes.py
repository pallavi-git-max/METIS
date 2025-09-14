
from flask import Blueprint, jsonify, request, make_response
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import csv
import io
import logging
from models.user import User
from models.project_request import ProjectRequest, StatusEnum
from models.approval import Approval
from models.nda import NDA
from app import db

export_bp = Blueprint('admin_export', __name__)

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(f"Unauthorized admin access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            return jsonify({
                'success': False,
                'message': 'Access forbidden. Admin privileges required.'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

@export_bp.route('/export/reports', methods=['GET'])
@login_required
@admin_required
def export_reports():
    """Export various reports"""
    try:
        report_type = request.args.get('type', 'requests')
        format_type = request.args.get('format', 'json')
        
        if report_type == 'requests':
            # Export all requests
            requests = ProjectRequest.query.order_by(desc(ProjectRequest.submitted_at)).all()
            data = [req.to_dict() for req in requests]
            
        elif report_type == 'users':
            # Export all users
            users = User.query.order_by(desc(User.created_at)).all()
            data = [user.to_dict() for user in users]
            
        elif report_type == 'approvals':
            # Export approval statistics
            approvals = Approval.query.order_by(desc(Approval.timestamp)).all()
            data = [{
                'id': approval.id,
                'project_request_id': approval.project_request_id,
                'admin_name': approval.admin.full_name if approval.admin else 'Unknown',
                'approved': approval.approved,
                'comments': approval.comments,
                'timestamp': approval.timestamp.isoformat()
            } for approval in approvals]
            
        elif report_type == 'statistics':
            # Export dashboard statistics
            total_users = User.query.count()
            total_requests = ProjectRequest.query.count()
            pending_requests = ProjectRequest.query.filter_by(status=StatusEnum.pending).count()
            approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()
            rejected_requests = ProjectRequest.query.filter_by(status=StatusEnum.rejected).count()
            
            # Get statistics for the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
            recent_requests = ProjectRequest.query.filter(ProjectRequest.submitted_at >= thirty_days_ago).count()
            
            data = {
                'total_users': total_users,
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'approved_requests': approved_requests,
                'rejected_requests': rejected_requests,
                'recent_users_30_days': recent_users,
                'recent_requests_30_days': recent_requests,
                'exported_at': datetime.utcnow().isoformat()
            }
            
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid report type'
            }), 400
        
        if format_type == 'csv':
            return export_csv(data, report_type)
        
        logger.info(f"Report exported by admin {current_user.id}: {report_type}")
        
        return jsonify({
            'success': True,
            'data': data,
            'exported_at': datetime.utcnow().isoformat(),
            'total_records': len(data) if isinstance(data, list) else 1
        })
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to export report'
        }), 500

def export_csv(data, report_type):
    """Export data as CSV"""
    try:
        output = io.StringIO()
        
        if isinstance(data, list) and len(data) > 0:
            # Get fieldnames from the first item
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            # For single object, create rows with key-value pairs
            writer = csv.writer(output)
            writer.writerow(['Field', 'Value'])
            for key, value in data.items():
                writer.writerow([key, value])
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating CSV export: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create CSV export'
        }), 500

@export_bp.route('/export/analytics', methods=['GET'])
@login_required
@admin_required
def export_analytics():
    """Export analytics data"""
    try:
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()
        
        # Get analytics data
        analytics = {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'user_statistics': {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'new_users_in_period': User.query.filter(
                    User.created_at >= start_date,
                    User.created_at <= end_date
                ).count(),
                'users_by_role': {}
            },
            'request_statistics': {
                'total_requests': ProjectRequest.query.count(),
                'requests_in_period': ProjectRequest.query.filter(
                    ProjectRequest.submitted_at >= start_date,
                    ProjectRequest.submitted_at <= end_date
                ).count(),
                'requests_by_status': {},
                'requests_by_priority': {}
            },
            'approval_statistics': {
                'total_approvals': Approval.query.count(),
                'approvals_in_period': Approval.query.filter(
                    Approval.timestamp >= start_date,
                    Approval.timestamp <= end_date
                ).count(),
                'approval_rate': 0
            }
        }
        
        # Get users by role
        role_counts = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        analytics['user_statistics']['users_by_role'] = {role.value: count for role, count in role_counts}
        
        # Get requests by status
        status_counts = db.session.query(ProjectRequest.status, func.count(ProjectRequest.id)).group_by(ProjectRequest.status).all()
        analytics['request_statistics']['requests_by_status'] = {status.value: count for status, count in status_counts}
        
        # Get requests by priority
        priority_counts = db.session.query(ProjectRequest.priority, func.count(ProjectRequest.id)).group_by(ProjectRequest.priority).all()
        analytics['request_statistics']['requests_by_priority'] = {priority.value: count for priority, count in priority_counts}
        
        # Calculate approval rate
        total_approvals = Approval.query.count()
        approved_count = Approval.query.filter_by(approved=True).count()
        if total_approvals > 0:
            analytics['approval_statistics']['approval_rate'] = round((approved_count / total_approvals) * 100, 2)
        
        logger.info(f"Analytics exported by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': analytics,
            'exported_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to export analytics'
        }), 500

@export_bp.route('/export/backup', methods=['GET'])
@login_required
@admin_required
def export_backup():
    """Export complete database backup"""
    try:
        # Get all data
        backup_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'exported_by': current_user.full_name,
            'users': [user.to_dict() for user in User.query.all()],
            'project_requests': [req.to_dict() for req in ProjectRequest.query.all()],
            'approvals': [{
                'id': approval.id,
                'project_request_id': approval.project_request_id,
                'admin_id': approval.admin_id,
                'approved': approval.approved,
                'comments': approval.comments,
                'timestamp': approval.timestamp.isoformat()
            } for approval in Approval.query.all()],
            'ndas': [{
                'id': nda.id,
                'user_id': nda.user_id,
                'filename': nda.filename,
                'upload_date': nda.upload_date.isoformat()
            } for nda in NDA.query.all()]
        }
        
        logger.info(f"Database backup exported by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': backup_data,
            'total_records': {
                'users': len(backup_data['users']),
                'project_requests': len(backup_data['project_requests']),
                'approvals': len(backup_data['approvals']),
                'ndas': len(backup_data['ndas'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error exporting backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to export backup'
        }), 500
