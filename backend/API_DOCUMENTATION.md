# METIS Lab Admin Dashboard API Documentation

## Overview
This document provides comprehensive API documentation for the METIS Lab Admin Dashboard backend system. The API follows RESTful principles and includes proper validation, error handling, and audit logging.

## Base URL
```
http://localhost:5000/admin
```

## Authentication
All admin endpoints require authentication and admin privileges. Include the session cookie or authentication token in requests.

## Error Response Format
All error responses follow this format:
```json
{
    "success": false,
    "message": "Error description",
    "error_type": "error_category",
    "field": "field_name" // Optional, for validation errors
}
```

## Success Response Format
All success responses follow this format:
```json
{
    "success": true,
    "message": "Success message", // Optional
    "data": {}, // Response data
    "pagination": {} // Optional, for paginated responses
}
```

## Endpoints

### Dashboard

#### GET /admin/dashboard
Get dashboard statistics and data.

**Response:**
```json
{
    "success": true,
    "data": {
        "stats": {
            "total_users": 247,
            "total_requests": 89,
            "pending_requests": 15,
            "hod_submitted": 5,
            "approved_requests": 67,
            "recent_users": 12,
            "recent_requests": 7
        },
        "recent_requests": [...],
        "active_users": [...],
        "pending_approvals": [...]
    }
}
```

### User Management

#### GET /admin/users
Get all users with pagination and filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 10)
- `role` (string): Filter by role
- `department` (string): Filter by department
- `search` (string): Search term

**Response:**
```json
{
    "success": true,
    "data": {
        "users": [
            {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "role": "student",
                "department": "computer_science",
                "designation": "Student",
                "student_id": "CS001",
                "phone": "+1234567890",
                "is_active": true,
                "last_login": "2024-01-15T10:30:00",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 10,
            "total": 247,
            "pages": 25,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

#### POST /admin/users
Create a new user.

**Request Body:**
```json
{
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "student",
    "department": "computer_science",
    "designation": "Student",
    "student_id": "CS002",
    "phone": "+1234567891",
    "password": "securepassword123",
    "is_active": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "User created successfully",
    "data": {
        "id": 2,
        "email": "newuser@example.com",
        "first_name": "Jane",
        "last_name": "Smith",
        "full_name": "Jane Smith",
        "role": "student",
        "department": "computer_science",
        "designation": "Student",
        "student_id": "CS002",
        "phone": "+1234567891",
        "is_active": true,
        "created_at": "2024-01-15T12:00:00",
        "updated_at": "2024-01-15T12:00:00"
    }
}
```

#### PUT /admin/users/{user_id}
Update user information.

**Request Body:**
```json
{
    "first_name": "Jane Updated",
    "role": "faculty",
    "department": "electronics",
    "is_active": false
}
```

#### DELETE /admin/users/{user_id}
Deactivate a user (soft delete).

**Response:**
```json
{
    "success": true,
    "message": "User deactivated successfully"
}
```

### Request Management

#### GET /admin/requests
Get all project requests with filtering and pagination.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 10)
- `status` (string): Filter by status
- `priority` (string): Filter by priority
- `search` (string): Search term

**Response:**
```json
{
    "success": true,
    "data": {
        "requests": [
            {
                "id": 1,
                "user_id": 1,
                "user_name": "John Doe",
                "project_title": "AI Research Project",
                "description": "Project description...",
                "purpose": "Research purpose...",
                "expected_duration": "6 months",
                "priority": "high",
                "status": "hod_submitted",
                "submitted_at": "2024-01-15T10:00:00",
                "hod_approved_at": "2024-01-15T11:00:00",
                "updated_at": "2024-01-15T11:00:00"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 10,
            "total": 89,
            "pages": 9,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

#### GET /admin/requests/{request_id}
Get detailed information about a specific request.

**Response:**
```json
{
    "success": true,
    "data": {
        "request": {
            "id": 1,
            "user_id": 1,
            "user_name": "John Doe",
            "project_title": "AI Research Project",
            "description": "Project description...",
            "purpose": "Research purpose...",
            "expected_duration": "6 months",
            "priority": "high",
            "status": "hod_submitted",
            "submitted_at": "2024-01-15T10:00:00",
            "hod_approved_at": "2024-01-15T11:00:00",
            "updated_at": "2024-01-15T11:00:00"
        },
        "approvals": [
            {
                "id": 1,
                "admin_name": "Admin User",
                "approved": true,
                "comments": "Approved by HoD",
                "timestamp": "2024-01-15T11:00:00"
            }
        ]
    }
}
```

#### POST /admin/requests/{request_id}/approve
Approve a project request.

**Request Body:**
```json
{
    "comments": "Approved for lab access"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Request approved successfully",
    "data": {
        "id": 1,
        "status": "approved",
        "approved_at": "2024-01-15T12:00:00",
        "updated_at": "2024-01-15T12:00:00"
    }
}
```

#### POST /admin/requests/{request_id}/reject
Reject a project request.

**Request Body:**
```json
{
    "reason": "Insufficient project details"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Request rejected successfully",
    "data": {
        "id": 1,
        "status": "rejected",
        "rejected_at": "2024-01-15T12:00:00",
        "rejection_reason": "Insufficient project details",
        "updated_at": "2024-01-15T12:00:00"
    }
}
```

#### PUT /admin/requests/{request_id}/status
Update request status.

**Request Body:**
```json
{
    "status": "approved",
    "reason": "Optional reason for status change"
}
```

### Export and Reports

#### GET /admin/export/reports
Export various reports.

**Query Parameters:**
- `type` (string): Report type (`requests`, `users`, `approvals`, `statistics`)
- `format` (string): Export format (`json`, `csv`)

**Response (JSON):**
```json
{
    "success": true,
    "data": [...],
    "exported_at": "2024-01-15T12:00:00",
    "total_records": 100
}
```

**Response (CSV):**
Returns CSV file with appropriate headers.

#### GET /admin/export/analytics
Export analytics data.

**Query Parameters:**
- `start_date` (string): Start date (ISO format)
- `end_date` (string): End date (ISO format)

**Response:**
```json
{
    "success": true,
    "data": {
        "date_range": {
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59"
        },
        "user_statistics": {
            "total_users": 247,
            "active_users": 200,
            "new_users_in_period": 12,
            "users_by_role": {
                "student": 200,
                "faculty": 30,
                "admin": 5
            }
        },
        "request_statistics": {
            "total_requests": 89,
            "requests_in_period": 15,
            "requests_by_status": {
                "pending": 10,
                "approved": 60,
                "rejected": 19
            },
            "requests_by_priority": {
                "low": 20,
                "medium": 40,
                "high": 25,
                "urgent": 4
            }
        },
        "approval_statistics": {
            "total_approvals": 79,
            "approvals_in_period": 12,
            "approval_rate": 75.95
        }
    },
    "exported_at": "2024-01-15T12:00:00"
}
```

#### GET /admin/export/backup
Export complete database backup.

**Response:**
```json
{
    "success": true,
    "data": {
        "exported_at": "2024-01-15T12:00:00",
        "exported_by": "Admin User",
        "users": [...],
        "project_requests": [...],
        "approvals": [...],
        "ndas": [...]
    },
    "total_records": {
        "users": 247,
        "project_requests": 89,
        "approvals": 79,
        "ndas": 45
    }
}
```

## Data Models

### User
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "student", // student, faculty, lab_incharge, hod, admin
    "department": "computer_science", // computer_science, electronics, mechanical, civil, electrical
    "designation": "Student",
    "student_id": "CS001",
    "phone": "+1234567890",
    "is_active": true,
    "last_login": "2024-01-15T10:30:00",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

### Project Request
```json
{
    "id": 1,
    "user_id": 1,
    "user_name": "John Doe",
    "project_title": "AI Research Project",
    "description": "Project description...",
    "purpose": "Research purpose...",
    "expected_duration": "6 months",
    "priority": "high", // low, medium, high, urgent
    "status": "hod_submitted", // pending, hod_submitted, faculty_approved, lab_incharge_approved, approved, rejected
    "submitted_at": "2024-01-15T10:00:00",
    "approved_at": "2024-01-15T12:00:00",
    "rejected_at": null,
    "rejection_reason": null,
    "hod_approved_at": "2024-01-15T11:00:00",
    "faculty_approved_at": null,
    "lab_incharge_approved_at": null,
    "updated_at": "2024-01-15T12:00:00"
}
```

### Approval
```json
{
    "id": 1,
    "project_request_id": 1,
    "admin_id": 1,
    "admin_name": "Admin User",
    "approved": true,
    "comments": "Approved for lab access",
    "timestamp": "2024-01-15T12:00:00"
}
```

## Validation Rules

### User Validation
- Email: Valid email format, unique
- First Name: Required, max 50 characters
- Last Name: Required, max 50 characters
- Role: Required, must be one of: student, faculty, lab_incharge, hod, admin
- Department: Optional, must be one of: computer_science, electronics, mechanical, civil, electrical
- Student ID: Optional, unique if provided
- Phone: Optional, valid phone format if provided
- Password: Min 8 characters, must contain uppercase, lowercase, and digit

### Project Request Validation
- Project Title: Required, max 255 characters
- Description: Required
- Purpose: Required, max 500 characters
- Priority: Optional, must be one of: low, medium, high, urgent

## Error Codes

- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Authentication required
- `403`: Forbidden - Admin privileges required
- `404`: Not Found - Resource not found
- `409`: Conflict - Resource already exists
- `500`: Internal Server Error - Server error

## Rate Limiting
Currently no rate limiting is implemented, but it's recommended for production use.

## Security Features
- CSRF protection
- SQL injection prevention
- XSS protection
- Input validation and sanitization
- Audit logging for all admin actions
- Secure password hashing
- Session management

## Audit Logging
All admin actions are automatically logged with:
- User ID
- Action performed
- Resource affected
- Timestamp
- IP address
- User agent
- Additional details

## Database Migrations
Run the following commands to set up the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```
