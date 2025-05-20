import os
import sys
import pytest
from datetime import datetime, date
import uuid

# Add application to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.models import Doctor, Patient, Medicine, Diagnosis, Appointment, Tag, Note, Prescription, PrescriptionItem

@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-jwt-key',
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def doctor(app):
    """Create a test doctor."""
    with app.app_context():
        doctor = Doctor(
            uuid=str(uuid.uuid4()),
            username='testdoctor',
            email='doctor@test.com',
            first_name='Test',
            last_name='Doctor',
            specialization='General Practice'
        )
        doctor.set_password('password123')
        db.session.add(doctor)
        db.session.commit()
        return doctor

@pytest.fixture(scope='function')
def auth_headers(client, doctor):
    """Get authentication headers for test doctor."""
    response = client.post('/api/login', json={
        'username': 'testdoctor',
        'password': 'password123'
    })
    data = response.get_json()
    token = data['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture(scope='function')
def patient(app, doctor):
    """Create a test patient."""
    with app.app_context():
        patient = Patient(
            uuid=str(uuid.uuid4()),
            doctor_id=doctor.id,
            first_name='Test',
            last_name='Patient',
            date_of_birth=date(1980, 1, 1),
            gender='male',
            email='patient@test.com',
            phone='123-456-7890'
        )
        db.session.add(patient)
        db.session.commit()
        return patient

@pytest.fixture(scope='function')
def medicine(app):
    """Create a test medicine."""
    with app.app_context():
        medicine = Medicine(
            uuid=str(uuid.uuid4()),
            name='Test Medicine',
            description='Test description',
            dosage_form='tablet',
            strength='500mg'
        )
        db.session.add(medicine)
        db.session.commit()
        return medicine

@pytest.fixture(scope='function')
def diagnosis(app):
    """Create a test diagnosis."""
    with app.app_context():
        diagnosis = Diagnosis(
            uuid=str(uuid.uuid4()),
            name='Test Diagnosis',
            description='Test description',
            icd_code='A00.0'
        )
        db.session.add(diagnosis)
        db.session.commit()
        return diagnosis

@pytest.fixture(scope='function')
def appointment(app, doctor, patient):
    """Create a test appointment."""
    with app.app_context():
        appointment = Appointment(
            uuid=str(uuid.uuid4()),
            doctor_id=doctor.id,
            patient_id=patient.id,
            date=date.today(),
            start_time=datetime.now().time(),
            end_time=datetime(datetime.now().year, datetime.now().month, 
                             datetime.now().day, datetime.now().hour + 1).time(),
            status='scheduled',
            reason='Test appointment'
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment