# METIS Lab Approval Workflow Documentation

## Overview
This document describes the comprehensive approval workflow, email notification system, and Role-Based Access Control (RBAC) implementation for the METIS Lab Management System.

## Approval Workflow

### Sequential Approval Process
The approval workflow follows a strict sequential order:

**For Students/External Users:**
1. **Project Guide** → 2. **HOD** → 3. **IT Services** → 4. **Admin**

**For Faculty:**
1. **HOD** → 2. **IT Services** → 3. **Admin** (Project Guide step is automatically bypassed)

### Workflow Stages

#### Stage 1: Request Submission
- **Status**: `pending` (for students/external) or `guide_approved` (for faculty)
- **Action**: User submits project request
- **Trigger**: 
  - Students/External: Email notification sent to all project guides
  - Faculty: Email notification sent directly to HOD (Project Guide step is bypassed)
- **Next**: 
  - Students/External: Project Guide reviews
  - Faculty: HOD reviews directly

#### Stage 2: Project Guide Approval
- **Status**: `guide_approved`
- **Action**: Project Guide approves/rejects
- **Access**: Only Project Guide can approve pending requests
- **Next**: HOD reviews

#### Stage 3: HOD Approval
- **Status**: `hod_approved`
- **Action**: HOD approves/rejects
- **Access**: Only HOD can approve guide_approved requests
- **Next**: IT Services reviews

#### Stage 4: IT Services Approval
- **Status**: `it_services_approved`
- **Action**: IT Services approves/rejects
- **Access**: Only IT Services can approve hod_approved requests
- **Next**: Admin final approval

#### Stage 5: Admin Final Approval
- **Status**: `approved`
- **Action**: Admin grants final approval
- **Access**: Only Admin can approve it_services_approved requests
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
- **Workflow**: Submitted → Project Guide → HOD → IT Services → Admin

#### Faculty
- **Can**: View own requests, submit new requests, update profile
- **Cannot**: Approve/reject requests, view other users' requests
- **Workflow**: Submitted → **HOD** → IT Services → Admin (Project Guide step bypassed)
- **Note**: Faculty requests automatically skip Project Guide approval and go directly to HOD

#### Project Guide
- **Can**: Approve pending requests, view all requests, reject any request
- **Cannot**: Approve requests at other stages

#### HOD (Head of Department)
- **Can**: Approve guide_approved requests, view all requests, reject any request
- **Cannot**: Approve requests at other stages

#### IT Services
- **Can**: Approve hod_approved requests, view all requests, reject any request
- **Cannot**: Approve requests at other stages

#### Admin
- **Can**: Approve it_services_approved requests, view all requests, manage all users, access admin dashboard
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
# Project Guide can only approve pending requests
if user.role == 'project_guide' and request.status == 'pending':
    can_approve = True

# HOD can only approve guide_approved requests
if user.role == 'hod' and request.status == 'guide_approved':
    can_approve = True

# IT Services can only approve hod_approved requests
if user.role == 'it_services' and request.status == 'hod_approved':
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
    pending = "pending"                              # Initial state
    guide_approved = "guide_approved"                # After project guide approval
    hod_approved = "hod_approved"                    # After HOD approval
    it_services_approved = "it_services_approved"    # After IT Services approval
    approved = "approved"                            # Final approval
    rejected = "rejected"                            # Rejected at any stage
```

### New Fields
- `guide_approved_at`: Timestamp of project guide approval
- `guide_approved_by`: User ID of approving project guide
- `hod_approved_at`: Timestamp of HOD approval
- `hod_approved_by`: User ID of approving HOD
- `it_services_approved_at`: Timestamp of IT Services approval
- `it_services_approved_by`: User ID of approving IT Services
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
