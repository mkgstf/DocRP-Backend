from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class Doctor(db.Model):
    """Doctor model representing clinic doctors/users"""
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    patients = db.relationship('Patient', backref='doctor', lazy=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    notes = db.relationship('Note', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Doctor {self.username}>'


class Patient(db.Model):
    """Patient model representing clinic patients"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    medical_history = db.Column(db.Text)
    insurance_info = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)
    diagnoses = db.relationship('PatientDiagnosis', backref='patient', lazy=True)
    notes = db.relationship('Note', backref='patient', lazy=True)
    
    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'


class Appointment(db.Model):
    """Appointment model for scheduling patient visits"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, canceled, no-show
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prescription = db.relationship('Prescription', backref='appointment', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.date} {self.start_time}>'


class Medicine(db.Model):
    """Medicine model representing medications that can be prescribed"""
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    dosage_form = db.Column(db.String(50))  # tablet, capsule, syrup, etc.
    strength = db.Column(db.String(50))  # 500mg, 10ml, etc.
    manufacturer = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prescription_items = db.relationship('PrescriptionItem', backref='medicine', lazy=True)
    
    def __repr__(self):
        return f'<Medicine {self.name}>'


class Diagnosis(db.Model):
    """Diagnosis model representing medical diagnoses that can be assigned to patients"""
    __tablename__ = 'diagnoses'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    icd_code = db.Column(db.String(20))  # International Classification of Diseases code
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient_diagnoses = db.relationship('PatientDiagnosis', backref='diagnosis', lazy=True)
    
    def __repr__(self):
        return f'<Diagnosis {self.name}>'


class PatientDiagnosis(db.Model):
    """Association table between patients and diagnoses with additional attributes"""
    __tablename__ = 'patient_diagnoses'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    diagnosis_id = db.Column(db.Integer, db.ForeignKey('diagnoses.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    date_diagnosed = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, resolved, chronic, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PatientDiagnosis {self.id}>'


class Prescription(db.Model):
    """Prescription model representing a collection of medicines prescribed to a patient"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    issue_date = db.Column(db.Date, default=datetime.utcnow)
    expiry_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('PrescriptionItem', backref='prescription', lazy=True)
    diagnoses = db.relationship('PatientDiagnosis', backref='prescription', lazy=True)
    
    def __repr__(self):
        return f'<Prescription {self.id}>'


class PrescriptionItem(db.Model):
    """Items within a prescription with specific instructions"""
    __tablename__ = 'prescription_items'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)  # e.g., "1 tablet"
    frequency = db.Column(db.String(100), nullable=False)  # e.g., "3 times a day"
    duration = db.Column(db.String(100))  # e.g., "7 days", "2 weeks"
    instructions = db.Column(db.Text)  # e.g., "Take after meals"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PrescriptionItem {self.id}>'


class Note(db.Model):
    """Notes model for doctor's clinical notes"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # clinical, administrative, follow-up, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('NoteTag', backref='note', lazy=True)
    
    def __repr__(self):
        return f'<Note {self.id}>'


class Tag(db.Model):
    """Tags for categorizing notes"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7))  # Hex color code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    note_tags = db.relationship('NoteTag', backref='tag', lazy=True)
    
    def __repr__(self):
        return f'<Tag {self.name}>'


class NoteTag(db.Model):
    """Association table between notes and tags"""
    __tablename__ = 'note_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NoteTag {self.id}>'


class ActivityLog(db.Model):
    """Log of user activities for auditing purposes"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # patient, appointment, prescription, etc.
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    doctor = db.relationship('Doctor', backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.id}>'