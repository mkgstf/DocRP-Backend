from app import db
from .base import BaseModel

class Bill(BaseModel):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    bill_date = db.Column(db.DateTime, nullable=False)
    consultation_fee = db.Column(db.Float, nullable=False)
    medicine_charges = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), nullable=False)  # paid, pending
    payment_method = db.Column(db.String(50))  # cash, card, upi
    notes = db.Column(db.Text)
    
    # Relationships
    patient = db.relationship('Patient', backref='bills')
    appointment = db.relationship('Appointment', backref='bill')

class BillItem(BaseModel):
    __tablename__ = 'bill_items'

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # consultation, medicine, procedure, lab_test
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    
    # Optional references
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))

class Payment(BaseModel):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, card, insurance, bank_transfer
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False)  # success, pending, failed
    notes = db.Column(db.Text)

class Insurance(BaseModel):
    __tablename__ = 'insurance'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    provider = db.Column(db.String(100), nullable=False)
    policy_number = db.Column(db.String(50), nullable=False)
    coverage_type = db.Column(db.String(50))
    coverage_limit = db.Column(db.Float)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))  # active, expired, cancelled
    
    # Relationships
    patient = db.relationship('Patient', backref='insurance_policies')

class PriceList(BaseModel):
    __tablename__ = 'price_list'

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # consultation, procedure, lab_test
    base_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True) 