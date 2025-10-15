import os
from flask import Flask, send_from_directory, render_template
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from backend.config import Config
from backend.models import db, login_manager

csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    app = Flask(
        __name__,
        static_folder='REG_LOG_DASH',
        template_folder='REG_LOG_DASH',
        static_url_path=''
    )
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
    from backend.blueprints.auth.routes import auth_bp
    from backend.blueprints.projects.routes import projects_bp
    from backend.blueprints.approvals.routes import approvals_bp
    from backend.blueprints.admin.routes import admin_bp
    from backend.blueprints.admin.request_routes import request_bp
    from backend.blueprints.admin.export_routes import export_bp
    from backend.blueprints.user_dashboard.routes import user_dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(approvals_bp, url_prefix='/approvals')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(request_bp, url_prefix='/admin')
    app.register_blueprint(export_bp, url_prefix='/admin')
    app.register_blueprint(user_dashboard_bp, url_prefix='/user')

    # Exempt JSON auth endpoints from CSRF (frontend uses fetch without CSRF token)
    csrf.exempt(auth_bp)
    csrf.exempt(projects_bp)
    csrf.exempt(user_dashboard_bp)
    csrf.exempt(approvals_bp)
    csrf.exempt(admin_bp)
    csrf.exempt(request_bp)
    csrf.exempt(export_bp)

    # Import models to ensure they are registered with SQLAlchemy
    from backend.models import User, ProjectRequest, NDA, Approval, AuditLog

    # Ensure tables exist to avoid OperationalError (e3q8) on first run
    # This complements migrations for environments where CLI is unavailable
    with app.app_context():
        # Set SQLite pragmas to reduce locking and improve performance
        try:
            from sqlalchemy import text
            # Only set essential pragmas that don't require exclusive access
            pragmas = [
                'PRAGMA busy_timeout=60000',  # 60 seconds
                'PRAGMA synchronous=NORMAL',
                'PRAGMA cache_size=10000',
                'PRAGMA temp_store=MEMORY'
            ]
            for pragma in pragmas:
                try:
                    db.session.execute(text(pragma))
                except Exception as e:
                    print(f"Warning: Could not set {pragma}: {e}")
            db.session.commit()
        except Exception as e:
            print(f"Warning: Could not set SQLite pragmas: {e}")
        
        # Create tables with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.create_all()
                print("Database tables created successfully")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print("Failed to create database tables after all retries")
                else:
                    import time
                    time.sleep(1)  # Wait 1 second before retry

    # Register error handlers
    from backend.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    @app.route('/')
    def index():
        return render_template('metislab.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('user_dash.html')

    # Serve all files from REG_LOG_DASH at root paths
    @app.route('/<path:filename>')
    def serve_page(filename):
        return send_from_directory(app.static_folder, filename)

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        # Allow inline handlers and CDN assets needed by REG_LOG_DASH (Bootstrap/jQuery)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self' data:; "
            "img-src 'self' data:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' data: https:;"
        )
        return response

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
