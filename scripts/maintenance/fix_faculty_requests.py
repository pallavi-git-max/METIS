"""Fix faculty/external requests that have incorrect guide_approved status"""
from app import create_app
from backend.models import db
from backend.models.user import User, RoleEnum
from backend.models.project_request import ProjectRequest, StatusEnum

app = create_app()

with app.app_context():
    print("\n=== FIXING FACULTY/EXTERNAL REQUESTS ===")
    
    # Find all faculty/external requests with guide_approved status
    faculty_external_requests = ProjectRequest.query.join(
        User, ProjectRequest.user_id == User.id
    ).filter(
        User.role.in_([RoleEnum.faculty, RoleEnum.external]),
        ProjectRequest.status == StatusEnum.guide_approved
    ).all()
    
    if not faculty_external_requests:
        print("✓ No faculty/external requests found with guide_approved status")
    else:
        print(f"Found {len(faculty_external_requests)} faculty/external requests with incorrect status:")
        
        for req in faculty_external_requests:
            print(f"\n  Request #{req.id}")
            print(f"  Title: {req.project_title}")
            print(f"  User: {req.user.full_name} ({req.user.role.value})")
            print(f"  Current Status: {req.status.value}")
            print(f"  Guide Approved At: {req.guide_approved_at}")
            print(f"  HOD Approved At: {req.hod_approved_at}")
            
            # Reset to pending if guide is the only approval
            if req.hod_approved_at is None:
                print(f"  → Changing status to 'pending' (waiting for HOD)")
                req.status = StatusEnum.pending
                req.guide_approved_at = None
                req.guide_approved_by = None
            else:
                print(f"  → Already HOD approved, keeping current status")
        
        try:
            db.session.commit()
            print(f"\n✓ Successfully fixed {len(faculty_external_requests)} requests")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error fixing requests: {e}")
    
    print("\n=== VERIFICATION ===")
    # Verify the fix
    remaining_bad = ProjectRequest.query.join(
        User, ProjectRequest.user_id == User.id
    ).filter(
        User.role.in_([RoleEnum.faculty, RoleEnum.external]),
        ProjectRequest.status == StatusEnum.guide_approved,
        ProjectRequest.hod_approved_at.is_(None)
    ).count()
    
    if remaining_bad == 0:
        print("✓ All faculty/external requests are now correct!")
    else:
        print(f"⚠ Warning: {remaining_bad} requests still have incorrect status")
    
    # Show current status of all faculty/external requests
    print("\n=== CURRENT FACULTY/EXTERNAL REQUESTS ===")
    all_faculty_requests = ProjectRequest.query.join(
        User, ProjectRequest.user_id == User.id
    ).filter(
        User.role.in_([RoleEnum.faculty, RoleEnum.external])
    ).all()
    
    for req in all_faculty_requests:
        print(f"Request #{req.id}: {req.project_title[:40]:40} | User: {req.user.full_name:20} | Status: {req.status.value}")
