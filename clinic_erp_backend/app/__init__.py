from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from datetime import timedelta

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Load configuration
    if test_config is None:
        app.config.from_pyfile('config.py')
    else:
        app.config.update(test_config)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Import and register blueprints
    from .routes.patients import patients_bp
    from .routes.appointments import appointments_bp
    from .routes.medicines import medicines_bp
    from .routes.prescriptions import prescriptions_bp
    from .routes.diagnoses import diagnoses_bp
    from .routes.statistics import statistics_bp
    from .routes.notes import notes_bp
    from .routes.doctors import doctors_bp
    
    app.register_blueprint(patients_bp, url_prefix='/api')
    app.register_blueprint(appointments_bp, url_prefix='/api')
    app.register_blueprint(medicines_bp, url_prefix='/api')
    app.register_blueprint(prescriptions_bp, url_prefix='/api')
    app.register_blueprint(diagnoses_bp, url_prefix='/api')
    app.register_blueprint(statistics_bp, url_prefix='/api')
    app.register_blueprint(notes_bp, url_prefix='/api')
    app.register_blueprint(doctors_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app