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
    doctor_uuid = str(uuid.uuid4())
    with app.app_context():
        doctor = Doctor(
            uuid=doctor_uuid,
            username='testdoctor',
            email='doctor@test.com',
            first_name='Test',
            last_name='Doctor',
            specialization='General Practice'
        )
        doctor.set_password('password123')
        db.session.add(doctor)
        db.session.commit()
        # Get a fresh copy from the database before returning
        return db.session.query(Doctor).filter_by(uuid=doctor_uuid).first()

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
    patient_uuid = str(uuid.uuid4())
    with app.app_context():
        # Need to get a fresh doctor object within this app context
        fresh_doctor = db.session.merge(doctor)
        
        patient = Patient(
            uuid=patient_uuid,
            doctor_id=fresh_doctor.id,
            first_name='Test',
            last_name='Patient',
            date_of_birth=date(1980, 1, 1),
            gender='male',
            email='patient@test.com',
            phone='123-456-7890'
        )
        db.session.add(patient)
        db.session.commit()
        return db.session.query(Patient).filter_by(uuid=patient_uuid).first()

@pytest.fixture(scope='function')
def medicine(app):
    """Create a test medicine."""
    medicine_uuid = str(uuid.uuid4())
    with app.app_context():
        medicine = Medicine(
            uuid=medicine_uuid,
            name='Test Medicine',
            description='Test description',
            dosage_form='tablet',
            strength='500mg'
        )
        db.session.add(medicine)
        db.session.commit()
        return db.session.query(Medicine).filter_by(uuid=medicine_uuid).first()

@pytest.fixture(scope='function')
def diagnosis(app):
    """Create a test diagnosis."""
    diagnosis_uuid = str(uuid.uuid4())
    with app.app_context():
        diagnosis = Diagnosis(
            uuid=diagnosis_uuid,
            name='Test Diagnosis',
            description='Test description',
            icd_code='A00.0'
        )
        db.session.add(diagnosis)
        db.session.commit()
        return db.session.query(Diagnosis).filter_by(uuid=diagnosis_uuid).first()

@pytest.fixture(scope='function')
def appointment(app, doctor, patient):
    """Create a test appointment."""
    appointment_uuid = str(uuid.uuid4())
    with app.app_context():
        # Get fresh objects within this app context
        fresh_doctor = db.session.merge(doctor)
        fresh_patient = db.session.merge(patient)
        
        appointment = Appointment(
            uuid=appointment_uuid,
            doctor_id=fresh_doctor.id,
            patient_id=fresh_patient.id,
            date=date.today(),
            start_time=datetime.now().time(),
            end_time=datetime(datetime.now().year, datetime.now().month, 
                             datetime.now().day, datetime.now().hour + 1).time(),
            status='scheduled',
            reason='Test appointment'
        )
        db.session.add(appointment)
        db.session.commit()
        return db.session.query(Appointment).filter_by(uuid=appointment_uuid).first()

@pytest.fixture(scope='function')
def prescription(app, doctor, patient, medicine):
    """Create a test prescription."""
    prescription_uuid = str(uuid.uuid4())
    with app.app_context():
        # Get fresh objects within this app context
        fresh_doctor = db.session.merge(doctor)
        fresh_patient = db.session.merge(patient)
        fresh_medicine = db.session.merge(medicine)
        
        prescription = Prescription(
            uuid=prescription_uuid,
            doctor_id=fresh_doctor.id,
            patient_id=fresh_patient.id,
            issue_date=date.today(),
            notes="Test prescription"
        )
        db.session.add(prescription)
        db.session.commit()
        
        # Create a prescription item
        item = PrescriptionItem(
            prescription_id=prescription.id,
            medicine_id=fresh_medicine.id,
            dosage="1 tablet",
            frequency="twice daily",
            duration="7 days"
        )
        db.session.add(item)
        db.session.commit()
        
        return db.session.query(Prescription).filter_by(uuid=prescription_uuid).first()