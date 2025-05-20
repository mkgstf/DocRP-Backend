#!/usr/bin/env python
# filepath: /Users/akshitmehta/Development/Projects/Docrp/backend/seed.py

"""
Seed script to populate the database with initial test data.
Run this script with: python seed.py
"""

import sys
import os
import random
from datetime import datetime, date, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create Flask app context
from run import app
from app.models.models import (
    Doctor, Patient, Appointment, Medicine, Diagnosis, 
    PatientDiagnosis, Prescription, PrescriptionItem, Note, Tag, NoteTag
)
from app.extensions import db

# Initialize Faker
fake = Faker()

def seed_all():
    """Seed all database tables with initial data"""
    try:
        print("Using database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
        with app.app_context():
            print("Starting database seeding...")
            
            # Clear existing data
            clear_database()
            
            # Create seed data
            print("Seeding doctors...")
            doctors = seed_doctors()
            print("Seeding patients...")
            patients = seed_patients(doctors)
            print("Seeding appointments...")
            appointments = seed_appointments(doctors, patients)
            print("Seeding medicines...")
            medicines = seed_medicines()
            print("Seeding diagnoses...")
            diagnoses = seed_diagnoses()
            print("Seeding prescriptions...")
            prescriptions = seed_prescriptions(doctors, patients, appointments, medicines, diagnoses)
            print("Seeding tags...")
            tags = seed_tags()
            print("Seeding notes...")
            notes = seed_notes(doctors, patients, appointments, tags)
            
            print("Database seeding completed successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        print("\nIf this is a database connection error, check:")
        print("1. DATABASE_URI in .env file (should be an absolute path like sqlite:////full/path/to/db.file)")
        print("2. Permissions on the database directory")
        print("3. Make sure the instance directory exists")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        raise

def clear_database():
    """Clear all data from the database"""
    try:
        print("Clearing existing data...")
        NoteTag.query.delete()
        Tag.query.delete()
        Note.query.delete()
        PrescriptionItem.query.delete()
        PatientDiagnosis.query.delete()
        Prescription.query.delete()
        Appointment.query.delete()
        Patient.query.delete()
        Diagnosis.query.delete()
        Medicine.query.delete()
        Doctor.query.delete()
        db.session.commit()
        print("Database cleared.")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing database: {e}")
        raise

def seed_doctors(count=5):
    """Create test doctor accounts"""
    print("Creating doctors...")
    doctors = []
    
    # Create an admin doctor
    admin_doctor = Doctor(
        email="admin@docrp.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        specialization="Administration",
        phone="555-ADMIN",
        active=True
    )
    admin_doctor.set_password("adminpass")
    doctors.append(admin_doctor)
    
    # Create other doctors
    specializations = [
        "Family Medicine", "Internal Medicine", "Pediatrics", 
        "Cardiology", "Dermatology", "Neurology", "Orthopedics",
        "Gynecology", "Psychiatry", "Oncology"
    ]
    
    for i in range(1, count):
        doctor = Doctor(
            email=fake.email(),
            username=fake.user_name(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            specialization=random.choice(specializations),
            phone=fake.phone_number(),
            active=True
        )
        doctor.set_password("password")  # Simple password for testing
        doctors.append(doctor)
    
    db.session.add_all(doctors)
    db.session.commit()
    print(f"Created {len(doctors)} doctors")
    return doctors

def seed_patients(doctors, count=20):
    """Create test patient records"""
    print("Creating patients...")
    patients = []
    
    genders = ["Male", "Female", "Other", "Prefer not to say"]
    
    for i in range(count):
        doctor = random.choice(doctors)
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        
        patient = Patient(
            doctor_id=doctor.id,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            date_of_birth=dob,
            gender=random.choice(genders),
            email=fake.email(),
            phone=fake.phone_number(),
            address=fake.address(),
            medical_history=fake.paragraph(nb_sentences=3),
            insurance_info=f"Plan: {fake.word().capitalize()} Insurance #{fake.numerify('###-###-####')}"
        )
        patients.append(patient)
    
    db.session.add_all(patients)
    db.session.commit()
    print(f"Created {len(patients)} patients")
    return patients

def seed_appointments(doctors, patients, count=50):
    """Create test appointments"""
    print("Creating appointments...")
    appointments = []
    
    status_choices = ["scheduled", "completed", "canceled", "no-show"]
    
    # Generate appointment times over the next 30 days
    today = date.today()
    
    for i in range(count):
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        
        # Random date within the next 30 days (or in the past 10 days for completed appointments)
        if random.choice([True, False]):
            # Future appointment
            days_ahead = random.randint(1, 30)
            appt_date = today + timedelta(days=days_ahead)
            status = "scheduled"
        else:
            # Past appointment
            days_ago = random.randint(1, 10)
            appt_date = today - timedelta(days=days_ago)
            status = random.choice(["completed", "canceled", "no-show"])
        
        # Random time between 9 AM and 5 PM
        hour = random.randint(9, 16)
        start_time = datetime.strptime(f"{hour}:00", "%H:%M").time()
        end_time = datetime.strptime(f"{hour+1}:00", "%H:%M").time()
        
        appointment = Appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            date=appt_date,
            start_time=start_time,
            end_time=end_time,
            reason=fake.sentence(nb_words=6),
            status=status,
            notes=fake.paragraph(nb_sentences=2) if random.choice([True, False]) else None
        )
        appointments.append(appointment)
    
    db.session.add_all(appointments)
    db.session.commit()
    print(f"Created {len(appointments)} appointments")
    return appointments

def seed_medicines(count=20):
    """Create test medicines"""
    print("Creating medicines...")
    medicines = []
    
    dosage_forms = ["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Drops"]
    manufacturers = ["PharmaCorp", "MediLife", "HealthRx", "CureAll", "VitaLabs"]
    
    common_medicines = [
        "Amoxicillin", "Ibuprofen", "Paracetamol", "Omeprazole", "Lisinopril",
        "Atorvastatin", "Metformin", "Sertraline", "Levothyroxine", "Amlodipine",
        "Losartan", "Albuterol", "Simvastatin", "Gabapentin", "Hydrochlorothiazide",
        "Cetirizine", "Montelukast", "Prednisone", "Fluoxetine", "Azithromycin"
    ]
    
    for i, name in enumerate(common_medicines[:count]):
        medicine = Medicine(
            name=name,
            description=fake.paragraph(nb_sentences=2),
            dosage_form=random.choice(dosage_forms),
            strength=f"{random.choice(['5', '10', '20', '25', '50', '100', '250', '500'])} {random.choice(['mg', 'mcg', 'ml'])}",
            manufacturer=random.choice(manufacturers)
        )
        medicines.append(medicine)
    
    db.session.add_all(medicines)
    db.session.commit()
    print(f"Created {len(medicines)} medicines")
    return medicines

def seed_diagnoses(count=15):
    """Create test diagnoses"""
    print("Creating diagnoses...")
    diagnoses = []
    
    common_diagnoses = [
        {"name": "Hypertension", "icd_code": "I10", "category": "Cardiovascular"},
        {"name": "Type 2 Diabetes", "icd_code": "E11", "category": "Endocrine"},
        {"name": "Asthma", "icd_code": "J45", "category": "Respiratory"},
        {"name": "Migraine", "icd_code": "G43", "category": "Neurological"},
        {"name": "Depression", "icd_code": "F32", "category": "Mental Health"},
        {"name": "Anxiety Disorder", "icd_code": "F41", "category": "Mental Health"},
        {"name": "Gastroesophageal Reflux Disease", "icd_code": "K21", "category": "Gastrointestinal"},
        {"name": "Osteoarthritis", "icd_code": "M15", "category": "Musculoskeletal"},
        {"name": "Eczema", "icd_code": "L20", "category": "Dermatological"},
        {"name": "Iron Deficiency Anemia", "icd_code": "D50", "category": "Hematological"},
        {"name": "Hypothyroidism", "icd_code": "E03", "category": "Endocrine"},
        {"name": "Allergic Rhinitis", "icd_code": "J30", "category": "Respiratory"},
        {"name": "Urinary Tract Infection", "icd_code": "N39.0", "category": "Urological"},
        {"name": "Acute Upper Respiratory Infection", "icd_code": "J06.9", "category": "Respiratory"},
        {"name": "Vitamin D Deficiency", "icd_code": "E55.9", "category": "Nutritional"}
    ]
    
    for diag_info in common_diagnoses[:count]:
        diagnosis = Diagnosis(
            name=diag_info["name"],
            description=fake.paragraph(nb_sentences=2),
            icd_code=diag_info["icd_code"],
            category=diag_info["category"]
        )
        diagnoses.append(diagnosis)
    
    db.session.add_all(diagnoses)
    db.session.commit()
    print(f"Created {len(diagnoses)} diagnoses")
    return diagnoses

def seed_prescriptions(doctors, patients, appointments, medicines, diagnoses, count=30):
    """Create test prescriptions"""
    print("Creating prescriptions...")
    prescriptions = []
    
    # Only use completed appointments for prescriptions
    completed_appointments = [a for a in appointments if a.status == "completed"]
    
    for i in range(min(count, len(completed_appointments))):
        appointment = completed_appointments[i]
        prescription = Prescription(
            doctor_id=appointment.doctor_id,
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            issue_date=appointment.date,
            expiry_date=appointment.date + timedelta(days=random.randint(30, 90)),
            notes=fake.paragraph(nb_sentences=1) if random.choice([True, False]) else None
        )
        db.session.add(prescription)
        db.session.flush()  # Get ID without committing
        
        # Add prescription items (1-3 medicines per prescription)
        for j in range(random.randint(1, 3)):
            medicine = random.choice(medicines)
            prescription_item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_id=medicine.id,
                dosage=f"{random.randint(1, 3)} {medicine.dosage_form.lower()}",
                frequency=random.choice(["Once daily", "Twice daily", "Three times daily", "Every 4 hours", "Every 6 hours"]),
                duration=f"{random.randint(1, 4)} {random.choice(['week', 'weeks', 'month', 'months'])}",
                instructions=random.choice([
                    "Take with food", 
                    "Take on empty stomach", 
                    "Take at bedtime",
                    None, 
                    None
                ])
            )
            db.session.add(prescription_item)
        
        # Add 1-2 diagnosis per prescription
        for j in range(random.randint(1, 2)):
            diagnosis = random.choice(diagnoses)
            patient_diagnosis = PatientDiagnosis(
                patient_id=appointment.patient_id,
                diagnosis_id=diagnosis.id,
                prescription_id=prescription.id,
                date_diagnosed=appointment.date,
                status=random.choice(["active", "resolved", "chronic"]),
                notes=fake.sentence() if random.choice([True, False]) else None
            )
            db.session.add(patient_diagnosis)
        
        prescriptions.append(prescription)
    
    db.session.commit()
    print(f"Created {len(prescriptions)} prescriptions with items and diagnoses")
    return prescriptions

def seed_tags(count=8):
    """Create tags for notes"""
    print("Creating tags...")
    tags = []
    
    common_tags = [
        {"name": "Urgent", "color": "#FF0000"},  # Red
        {"name": "Follow-up", "color": "#FFA500"},  # Orange
        {"name": "Chronic", "color": "#800080"},  # Purple
        {"name": "Medication", "color": "#0000FF"},  # Blue
        {"name": "Lab Results", "color": "#008000"},  # Green
        {"name": "Consultation", "color": "#4B0082"},  # Indigo
        {"name": "Administrative", "color": "#808080"},  # Gray
        {"name": "Personal", "color": "#FFC0CB"}  # Pink
    ]
    
    for tag_info in common_tags[:count]:
        tag = Tag(
            name=tag_info["name"],
            color=tag_info["color"]
        )
        tags.append(tag)
    
    db.session.add_all(tags)
    db.session.commit()
    print(f"Created {len(tags)} tags")
    return tags

def seed_notes(doctors, patients, appointments, tags, count=40):
    """Create test clinical notes"""
    print("Creating notes...")
    notes = []
    
    note_categories = ["clinical", "administrative", "follow-up", "lab", "procedure"]
    
    for i in range(count):
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        # 50% chance to associate with an appointment
        appointment_id = random.choice(appointments).id if random.choice([True, False]) else None
        
        note = Note(
            doctor_id=doctor.id,
            patient_id=patient.id,
            appointment_id=appointment_id,
            title=fake.sentence(nb_words=5),
            content=fake.paragraph(nb_sentences=random.randint(3, 6)),
            category=random.choice(note_categories)
        )
        db.session.add(note)
        db.session.flush()  # Get ID without committing
        
        # Add 0-2 tags to the note
        for j in range(random.randint(0, 2)):
            tag = random.choice(tags)
            note_tag = NoteTag(
                note_id=note.id,
                tag_id=tag.id
            )
            db.session.add(note_tag)
        
        notes.append(note)
    
    db.session.commit()
    print(f"Created {len(notes)} notes with tags")
    return notes

if __name__ == "__main__":
    seed_all()