from app import db
from .base import BaseModel
from datetime import datetime
from sqlalchemy.dialects.postgresql import ENUM
from app.utils.validators import is_medicine_low_stock, is_medicine_expired

medicine_type_enum = ENUM('tablet', 'capsule', 'syrup', 'injection', 'cream', 'ointment', 'drops', 'inhaler', 'other', 
                         name='medicine_type_enum', create_type=False)
route_enum = ENUM('oral', 'topical', 'injection', 'inhalation', 'drops', 'other', 
                 name='route_enum', create_type=False)

class Medicine(BaseModel):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    generic_name = db.Column(db.String(100), index=True)
    brand_name = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    
    # Medicine Details
    medicine_type = db.Column(medicine_type_enum, nullable=False)
    dosage_form = db.Column(db.String(50))  # e.g., 500mg, 5ml, etc.
    strength = db.Column(db.String(50))  # e.g., 500mg, 50mg/5ml
    route = db.Column(route_enum)
    description = db.Column(db.Text)
    
    # Usage Information
    indications = db.Column(db.Text)  # What it's used for
    contraindications = db.Column(db.Text)  # When not to use
    side_effects = db.Column(db.Text)
    precautions = db.Column(db.Text)
    storage_instructions = db.Column(db.Text)
    
    # Inventory Management
    stock_quantity = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=10)
    unit_price = db.Column(db.Numeric(10, 2))  # Price per unit
    expiry_date = db.Column(db.Date)
    batch_number = db.Column(db.String(50))
    location_in_clinic = db.Column(db.String(100))  # Physical storage location
    
    # Prescription Requirements
    requires_prescription = db.Column(db.Boolean, default=True, server_default='true')
    max_dosage_per_day = db.Column(db.String(50))  # Maximum recommended dosage
    
    # Timestamps for inventory
    last_restock_date = db.Column(db.DateTime(timezone=True))
    last_stock_check = db.Column(db.DateTime(timezone=True))

    def is_low_stock(self):
        return is_medicine_low_stock(self.stock_quantity, self.minimum_stock)

    def is_expired(self):
        return is_medicine_expired(self.expiry_date)

class Prescription(BaseModel):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id', ondelete='SET NULL'))
    prescription_date = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    notes = db.Column(db.Text)
    diagnosis = db.Column(db.Text)  # Reason for prescription
    follow_up_date = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    items = db.relationship('PrescriptionItem', backref='prescription', lazy='dynamic', cascade='all, delete-orphan')
    medical_record = db.relationship('MedicalRecord', backref='prescriptions')

class PrescriptionItem(BaseModel):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'), nullable=False)
    
    # Dosage Instructions
    dosage = db.Column(db.String(50), nullable=False)  # e.g., "1 tablet"
    frequency = db.Column(db.String(50), nullable=False)  # e.g., "twice daily"
    duration = db.Column(db.String(50))  # e.g., "7 days"
    timing = db.Column(db.String(100))  # e.g., "After meals", "Before bedtime"
    instructions = db.Column(db.Text)  # Additional instructions
    quantity = db.Column(db.Integer, nullable=False)
    
    # Special Instructions
    take_with_food = db.Column(db.Boolean, default=False, server_default='false')
    take_on_empty_stomach = db.Column(db.Boolean, default=False, server_default='false')
    special_notes = db.Column(db.Text)  # Any warnings or special considerations
    
    # Relationships
    medicine = db.relationship('Medicine', backref='prescription_items')

class MedicineInventory(BaseModel):
    __tablename__ = 'medicine_inventory'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100))
    invoice_number = db.Column(db.String(50))
    
    # Relationships
    medicine = db.relationship('Medicine', backref='inventory_records')

class MedicineCategory(BaseModel):
    __tablename__ = 'medicine_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('medicine_categories.id'))
    
    # Self-referential relationship for hierarchical categories
    subcategories = db.relationship(
        'MedicineCategory',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    ) 