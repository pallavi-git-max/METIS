from app import create_app
from backend.models import db
from backend.models.user import User
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    engine = db.engine
    insp = inspect(engine)
    print("DB URI:", app.config.get('SQLALCHEMY_DATABASE_URI'))
    print("Tables:", insp.get_table_names())
    print("Users count:", db.session.query(User).count())


