"""Debug script to check project requests and user IDs"""
from app import create_app
from backend.models import db
from backend.models.project_request import ProjectRequest
from backend.models.user import User

app = create_app()

with app.app_context():
    print("\n=== ALL USERS ===")
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}, Name: {user.full_name}, Role: {user.role}")
    
    print("\n=== ALL PROJECT REQUESTS ===")
    requests = ProjectRequest.query.all()
    for req in requests:
        user = User.query.get(req.user_id)
        print(f"Request ID: {req.id}, User ID: {req.user_id}, User: {user.full_name if user else 'Unknown'}, Title: {req.project_title}, Status: {req.status}")
    
    print("\n=== USER 'Pallavi H' DETAILS ===")
    pallavi = User.query.filter((User.first_name == 'Pallavi') | (User.email.like('%pallavi%'))).first()
    if pallavi:
        print(f"Found user: ID={pallavi.id}, Email={pallavi.email}, Name={pallavi.full_name}")
        print(f"\nRequests for this user:")
        user_requests = ProjectRequest.query.filter_by(user_id=pallavi.id).all()
        for req in user_requests:
            print(f"  Request ID: {req.id}, Title: {req.project_title}")
    else:
        print("User 'Pallavi H' not found")
