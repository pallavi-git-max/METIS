import os
from flask import Flask, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='/static')
    app.config.from_object(Config)

    # Make sure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Import blueprints
    from blueprints.auth.routes import auth_bp
    from blueprints.projects.routes import projects_bp
    from blueprints.approvals.routes import approvals_bp
    from blueprints.admin.routes import admin_bp
    from blueprints.admin.request_routes import request_bp
    from blueprints.admin.export_routes import export_bp
    from blueprints.user_dashboard.routes import user_dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(approvals_bp, url_prefix='/approvals')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(request_bp, url_prefix='/admin')
    app.register_blueprint(export_bp, url_prefix='/admin')
    app.register_blueprint(user_dashboard_bp, url_prefix='/user')

    # Register error handlers
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    @app.route('/')
    def index():
        # Serve login page from backend templates which includes frontend HTML & JS/CSS
        return render_template('college-login-system.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('college-dashboard.html')

    # Serve frontend static files from frontend folder
    @app.route('/css/<path:filename>')
    def css_static(filename):
        return send_from_directory(os.path.join(app.root_path, '../frontend/css'), filename)

    @app.route('/js/<path:filename>')
    def js_static(filename):
        return send_from_directory(os.path.join(app.root_path, '../frontend/js'), filename)

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        return response

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
