# METIS Lab Admin Dashboard - Installation Guide

## Prerequisites

Before installing the METIS Lab Admin Dashboard backend, ensure you have the following:

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 2GB RAM
- **Storage**: At least 1GB free space

### Required Software
1. **Python 3.8+**: Download from [python.org](https://python.org)
2. **Git**: For version control (optional)
3. **PostgreSQL**: For production database (optional, SQLite is used by default)

## Quick Installation (Recommended)

### For Windows Users
1. Open Command Prompt or PowerShell
2. Navigate to the backend directory:
   ```cmd
   cd E:\Downloads\final_project\metislab\backend
   ```
3. Run the setup script:
   ```cmd
   setup.bat
   ```

### For Unix/Linux/Mac Users
1. Open Terminal
2. Navigate to the backend directory:
   ```bash
   cd /path/to/metislab/backend
   ```
3. Make the setup script executable and run it:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

## Manual Installation

If you prefer to install manually or the automated setup fails:

### Step 1: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Upgrade Pip
```bash
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Environment File
Create a `.env` file in the backend directory with the following content:
```env
# METIS Lab Admin Dashboard Configuration

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///metis_portal.db
# For PostgreSQL: DATABASE_URL=postgresql://username:password@localhost/metis_portal

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Security Configuration
REMEMBER_COOKIE_DURATION=3600

# Logging Configuration
LOG_LEVEL=INFO
```

### Step 5: Create Directories
```bash
mkdir uploads logs migrations
```

### Step 6: Initialize Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Dependencies Explained

### Core Flask Framework
- **Flask**: Web framework
- **Werkzeug**: WSGI toolkit

### Flask Extensions
- **Flask-Login**: User session management
- **Flask-WTF**: Form handling and CSRF protection
- **Flask-Migrate**: Database migrations
- **Flask-SQLAlchemy**: Database ORM
- **Flask-CORS**: Cross-Origin Resource Sharing

### Database
- **SQLAlchemy**: Database toolkit and ORM
- **psycopg2-binary**: PostgreSQL adapter
- **alembic**: Database migration tool

### Forms and Validation
- **WTForms**: Form handling
- **email-validator**: Email validation

### Security
- **bcrypt**: Password hashing
- **cryptography**: Cryptographic recipes

### Data Processing
- **pandas**: Data analysis library
- **numpy**: Numerical computing

### Development and Testing
- **pytest**: Testing framework
- **pytest-flask**: Flask testing utilities
- **pytest-cov**: Coverage reporting
- **black**: Code formatter
- **flake8**: Linting tool

### Production
- **gunicorn**: WSGI HTTP server

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///metis_portal.db` |
| `UPLOAD_FOLDER` | File upload directory | `uploads` |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | `16777216` (16MB) |
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Debug mode | `True` |

### Database Configuration

#### SQLite (Default)
```env
DATABASE_URL=sqlite:///metis_portal.db
```

#### PostgreSQL
```env
DATABASE_URL=postgresql://username:password@localhost:5432/metis_portal
```

#### MySQL
```env
DATABASE_URL=mysql://username:password@localhost:3306/metis_portal
```

## Running the Application

### Development Mode
```bash
python run.py
```

### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=backend
```

### Run Specific Test File
```bash
pytest tests/test_admin_routes.py
```

## Development Tools

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

## Troubleshooting

### Common Issues

#### 1. Python Version Error
**Error**: `Python 3.8 or higher is required`
**Solution**: Install Python 3.8+ from [python.org](https://python.org)

#### 2. Virtual Environment Issues
**Error**: `venv\Scripts\activate` not found
**Solution**: 
```bash
python -m venv venv
# Then activate manually
```

#### 3. Database Connection Error
**Error**: `sqlalchemy.exc.OperationalError`
**Solution**: Check DATABASE_URL in .env file

#### 4. Import Errors
**Error**: `ModuleNotFoundError`
**Solution**: Ensure virtual environment is activated and dependencies are installed

#### 5. Permission Errors
**Error**: Permission denied
**Solution**: Run with appropriate permissions or use `sudo` (Unix/Linux)

### Getting Help

1. Check the logs in the `logs` directory
2. Verify all dependencies are installed: `pip list`
3. Check Python version: `python --version`
4. Verify virtual environment is activated
5. Check .env file configuration

## Production Deployment

### Security Considerations
1. Change the `SECRET_KEY` in production
2. Set `FLASK_DEBUG=False`
3. Use a production database (PostgreSQL recommended)
4. Configure proper logging
5. Set up SSL/TLS certificates
6. Use environment variables for sensitive data

### Performance Optimization
1. Use a production WSGI server (Gunicorn)
2. Configure database connection pooling
3. Set up caching (Redis recommended)
4. Use a reverse proxy (Nginx)
5. Enable compression

### Monitoring
1. Set up application monitoring
2. Configure log aggregation
3. Set up health checks
4. Monitor database performance

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check the implementation summary
4. Create an issue in the project repository

## License

This project is licensed under the MIT License.
