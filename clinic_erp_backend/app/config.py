import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///clinic_erp.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Application configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

# JWT configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')

# File storage configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

# Email configuration
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

# Pagination settings
ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))

# Security configurations
PASSWORD_SALT = os.getenv('PASSWORD_SALT', 'dev-salt')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
REMEMBER_COOKIE_SECURE = os.getenv('REMEMBER_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')