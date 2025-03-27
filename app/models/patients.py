from app import db
from .base import BaseModel

class Patient(BaseModel):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))
    
    # Medical Information
    blood_group = db.Column(db.String(5))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    insurance_provider = db.Column(db.String(100))
    insurance_id = db.Column(db.String(50))
    
    # Relationships
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class MedicalRecord(BaseModel):
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime)
    
    # Relationships
    documents = db.relationship('MedicalDocument', backref='medical_record', lazy='dynamic')

class MedicalDocument(BaseModel):
    __tablename__ = 'medical_documents'

    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # e.g., X-ray, Lab Report, etc.
    file_url = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text) 