from app import create_app
from backend.models import db
from backend.models.user import User, RoleEnum


def upsert_user(email: str, first_name: str, last_name: str, role: RoleEnum, password: str, **extra_fields):
    user = User.query.filter_by(email=email).first()
    created = False
    if not user:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            **extra_fields
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        created = True
    return created, user


def main():
    app = create_app()
    with app.app_context():
        created_admin, admin = upsert_user(
            email="admin@metislab.edu",
            first_name="Admin",
            last_name="User",
            role=RoleEnum.admin,
            password="Admin@123456",
        )

        created_student, student = upsert_user(
            email="student1@metislab.edu",
            first_name="Student",
            last_name="One",
            role=RoleEnum.student,
            password="Student@123456",
            student_id="S123456",
            phone="9999999999",
        )

        created_faculty, faculty = upsert_user(
            email="faculty1@metislab.edu",
            first_name="Faculty",
            last_name="One",
            role=RoleEnum.faculty,
            password="Faculty@123456",
            designation="Faculty",
        )

        # Create additional admin users
        created_guide, guide = upsert_user(
            email="guide@metislab.edu",
            first_name="Guide",
            last_name="Admin",
            role=RoleEnum.admin,
            password="Guide@2024!",
            student_id="GUIDE001",
            phone="9876543210",
            designation="Project Guide"
        )

        created_hod, hod = upsert_user(
            email="hod@metislab.edu",
            first_name="HOD",
            last_name="Admin",
            role=RoleEnum.admin,
            password="HOD@2024!",
            student_id="HOD001",
            phone="9876543211",
            designation="Head of Department"
        )

        created_itservice, itservice = upsert_user(
            email="itservice@metislab.edu",
            first_name="IT",
            last_name="Service",
            role=RoleEnum.admin,
            password="ITService@2024!",
            student_id="IT001",
            phone="9876543212",
            designation="IT Service Manager"
        )

        created_metisincharge, metisincharge = upsert_user(
            email="metisincharge@metislab.edu",
            first_name="METIS",
            last_name="Incharge",
            role=RoleEnum.admin,
            password="METIS@2024!",
            student_id="METIS001",
            phone="9876543213",
            designation="METIS Lab Incharge"
        )

        print({
            "admin": {"created": created_admin, "email": admin.email, "password": "Admin@123456"},
            "student": {"created": created_student, "email": student.email, "password": "Student@123456"},
            "faculty": {"created": created_faculty, "email": faculty.email, "password": "Faculty@123456"},
            "guide": {"created": created_guide, "email": guide.email, "password": "Guide@2024!"},
            "hod": {"created": created_hod, "email": hod.email, "password": "HOD@2024!"},
            "itservice": {"created": created_itservice, "email": itservice.email, "password": "ITService@2024!"},
            "metisincharge": {"created": created_metisincharge, "email": metisincharge.email, "password": "METIS@2024!"},
        })


if __name__ == "__main__":
    main()


