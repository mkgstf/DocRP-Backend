from datetime import datetime, date, timedelta

def check_appointment_overlap(appointment, db_session):
    """Check if an appointment overlaps with existing appointments"""
    from app.models import Appointment, AppointmentStatus
    
    end_time = appointment.scheduled_at + timedelta(minutes=appointment.duration)
    overlapping = db_session.query(Appointment).filter(
        Appointment.id != appointment.id,
        Appointment.status == AppointmentStatus.SCHEDULED.value,
        Appointment.scheduled_at < end_time,
        (Appointment.scheduled_at + timedelta(minutes=Appointment.duration)) > appointment.scheduled_at
    ).first()
    return overlapping is not None

def is_medicine_low_stock(current_stock, minimum_stock):
    """Check if medicine stock is low"""
    return current_stock <= minimum_stock

def is_medicine_expired(expiry_date):
    """Check if medicine is expired"""
    if not expiry_date:
        return False
    return expiry_date <= date.today()

def calculate_age(birth_date):
    """Calculate age from date of birth"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_bill_total(consultation_fee, medicine_charges=0):
    """Calculate total bill amount"""
    return consultation_fee + (medicine_charges or 0)

def validate_time_range(start_time, end_time):
    """Validate that end time is after start time"""
    if start_time and end_time and end_time <= start_time:
        raise ValueError("End time must be after start time")
    return True

def validate_date_range(start_date, end_date):
    """Validate that end date is after start date"""
    if start_date and end_date and end_date < start_date:
        raise ValueError("End date must be after start date")
    return True

def validate_future_date(check_date):
    """Validate that a date is not in the past"""
    if check_date < datetime.now():
        raise ValueError("Date cannot be in the past")
    return True 