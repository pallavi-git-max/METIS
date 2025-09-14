# METIS Lab Approval Workflow Documentation

## Overview
This document describes the comprehensive approval workflow, email notification system, and Role-Based Access Control (RBAC) implementation for the METIS Lab Management System.

## Approval Workflow

### Sequential Approval Process
The approval workflow follows a strict sequential order:

1. **Lab In-charge** → 2. **Faculty In-charge** → 3. **HOD** → 4. **Admin**

### Workflow Stages

#### Stage 1: Request Submission
- **Status**: `pending`
- **Action**: User submits project request
- **Trigger**: Email notification sent to all admins
- **Next**: Lab In-charge reviews

#### Stage 2: Lab In-charge Approval
- **Status**: `lab_incharge_approved`
- **Action**: Lab In-charge approves/rejects
- **Access**: Only Lab In-charge can approve pending requests
- **Next**: Faculty In-charge reviews

#### Stage 3: Faculty In-charge Approval
- **Status**: `faculty_approved`
- **Action**: Faculty In-charge approves/rejects
- **Access**: Only Faculty can approve lab_incharge_approved requests
- **Next**: HOD reviews

#### Stage 4: HOD Approval
- **Status**: `hod_approved`
- **Action**: HOD approves/rejects
- **Access**: Only HOD can approve faculty_approved requests
- **Next**: Admin final approval

#### Stage 5: Admin Final Approval
- **Status**: `approved`
- **Action**: Admin grants final approval
- **Access**: Only Admin can approve hod_approved requests
- **Trigger**: Email notification sent to user with credentials

### Rejection at Any Stage
- **Status**: `rejected`
- **Action**: Any faculty member or admin can reject
- **Trigger**: Email notification sent to user with rejection reason

## Role-Based Access Control (RBAC)

### User Roles and Permissions

#### Student
- **Can**: View own requests, submit new requests, update profile
- **Cannot**: Approve/reject requests, view other users' requests

#### Lab In-charge
- **Can**: Approve pending requests, view all requests, manage lab resources
- **Cannot**: Approve requests at other stages

#### Faculty
- **Can**: Approve lab_incharge_approved requests, view all requests, reject any request
- **Cannot**: Approve requests at other stages

#### HOD (Head of Department)
- **Can**: Approve faculty_approved requests, view all requests, reject any request
- **Cannot**: Approve requests at other stages

#### Admin
- **Can**: Approve hod_approved requests, view all requests, manage all users, access admin dashboard
- **Cannot**: None (full access)

### Access Control Implementation

#### Request Visibility
```python
# Users can only see their own requests
if user.role == 'student':
    requests = ProjectRequest.query.filter_by(user_id=user.id)

# Faculty and Admin can see all requests
if user.is_faculty or user.is_admin:
    requests = ProjectRequest.query
```

#### Approval Permissions
```python
# Lab In-charge can only approve pending requests
if user.role == 'lab_incharge' and request.status == 'pending':
    can_approve = True

# Faculty can only approve lab_incharge_approved requests
if user.role == 'faculty' and request.status == 'lab_incharge_approved':
    can_approve = True
```

## Email Notification System

### Email Templates

#### 1. New Request Notification (to Admins)
- **Trigger**: When user submits new request
- **Recipients**: All admin users
- **Content**: Request details, user information, direct link to review

#### 2. Approval Notification (to User)
- **Trigger**: When request is fully approved (status = approved)
- **Recipients**: Request submitter
- **Content**: Approval confirmation, access credentials, next steps

#### 3. Rejection Notification (to User)
- **Trigger**: When request is rejected at any stage
- **Recipients**: Request submitter
- **Content**: Rejection reason, suggestions for improvement, contact information

### Email Configuration

#### Environment Variables
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@metislab.edu
FROM_NAME=METIS Lab
BASE_URL=http://localhost:5000
```

#### Email Service Features
- HTML and text email templates
- Automatic retry on failure
- Logging of email delivery status
- Graceful handling of email failures (doesn't break request flow)

## Database Schema Updates

### ProjectRequest Model Changes
```python
class StatusEnum(str, Enum):
    pending = "pending"                    # Initial state
    lab_incharge_approved = "lab_incharge_approved"  # After lab in-charge approval
    faculty_approved = "faculty_approved"  # After faculty approval
    hod_approved = "hod_approved"          # After HOD approval
    approved = "approved"                  # Final approval
    rejected = "rejected"                  # Rejected at any stage
```

### New Fields
- `lab_incharge_approved_at`: Timestamp of lab in-charge approval
- `faculty_approved_at`: Timestamp of faculty approval
- `hod_approved_at`: Timestamp of HOD approval
- `rejection_reason`: Reason for rejection

## API Endpoints

### Request Management
- `POST /projects/submit` - Submit new request (triggers admin notification)
- `GET /projects/` - Get user's requests (RBAC filtered)
- `GET /projects/{id}` - Get request details (RBAC filtered)

### Approval Management
- `GET /approvals/pending` - Get pending requests (role-based filtering)
- `POST /approvals/{id}/approve` - Approve request (workflow-based)
- `POST /approvals/{id}/reject` - Reject request (triggers user notification)
- `GET /approvals/queue` - Get approval queue for current user

### Admin Management
- `GET /admin/dashboard` - Admin dashboard (full access)
- `GET /admin/requests` - All requests (admin only)
- `GET /admin/users` - User management (admin only)

## Security Features

### Authentication
- Session-based authentication
- Password hashing with bcrypt
- CSRF protection on all forms

### Authorization
- Role-based access control
- Endpoint-level permission checks
- Resource-level access validation

### Audit Logging
- All actions logged with user, timestamp, and details
- Failed access attempts logged
- Email delivery status tracked

## Error Handling

### Graceful Degradation
- Email failures don't break request flow
- Database errors properly rolled back
- User-friendly error messages

### Logging
- Comprehensive logging at all levels
- Error tracking and monitoring
- Performance metrics

## Testing Recommendations

### Unit Tests
- Test approval workflow logic
- Test RBAC permissions
- Test email service functionality

### Integration Tests
- Test complete approval flow
- Test email delivery
- Test error scenarios

### Security Tests
- Test unauthorized access attempts
- Test role escalation prevention
- Test data isolation

## Deployment Considerations

### Email Configuration
- Configure SMTP settings for production
- Set up email monitoring
- Configure backup email service

### Database
- Run migrations for schema updates
- Set up database backups
- Configure connection pooling

### Monitoring
- Set up application monitoring
- Configure log aggregation
- Set up alerting for failures

## Troubleshooting

### Common Issues

#### Email Not Sending
1. Check SMTP credentials
2. Verify network connectivity
3. Check email service logs

#### Permission Denied
1. Verify user role
2. Check request status
3. Review RBAC configuration

#### Workflow Stuck
1. Check approval permissions
2. Verify user roles
3. Review audit logs

### Support Contacts
- Technical Support: tech-support@metislab.edu
- Admin Support: admin-support@metislab.edu
- Email Issues: email-support@metislab.edu
