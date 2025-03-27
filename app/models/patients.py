from app import db
from .base import BaseModel
from datetime import date
from sqlalchemy.dialects.postgresql import ENUM
from app.utils.validators import calculate_age

gender_enum = ENUM('male', 'female', 'other', name='gender_enum', create_type=False)
blood_group_enum = ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='blood_group_enum', create_type=False)
document_type_enum = ENUM('prescription', 'lab_report', 'xray', 'scan', 'other', name='document_type_enum', create_type=False)

class Patient(BaseModel):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(gender_enum)
    
    # Medical Information
    blood_group = db.Column(blood_group_enum)
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
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        return calculate_age(self.date_of_birth)

class MedicalRecord(BaseModel):
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    visit_date = db.Column(db.DateTime(timezone=True), nullable=False)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    documents = db.relationship('MedicalDocument', backref='medical_record', lazy='dynamic', cascade='all, delete-orphan')

class MedicalDocument(BaseModel):
    __tablename__ = 'medical_documents'

    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id', ondelete='CASCADE'), nullable=False)
    document_type = db.Column(document_type_enum, nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now()) 