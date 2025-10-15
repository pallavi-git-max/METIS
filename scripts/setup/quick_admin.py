import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from backend.models import db, User, RoleEnum

app = create_app()
with app.app_context():
    db.create_all()
    admin = User(email='guide@metislab.edu', first_name='Guide', last_name='Admin', role=RoleEnum.admin, student_id='GUIDE001', phone='9876543210', designation='Project Guide', is_active=True)
    admin.set_password('Guide@2024!')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created: guide@metislab.edu / Guide@2024!")

