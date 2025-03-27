from app import db
from .base import BaseModel
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import validates

class AppointmentStatus(str, Enum):
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    NO_SHOW = 'no-show'

class AppointmentType(str, Enum):
    REGULAR = 'regular'
    FOLLOW_UP = 'follow-up'
    EMERGENCY = 'emergency'

class ConsultationType(str, Enum):
    CLINIC = 'clinic'
    HOME = 'home'
    ONLINE = 'online'

class Appointment(BaseModel):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, default=30)  # in minutes
    status = db.Column(db.String(20), nullable=False, default=AppointmentStatus.SCHEDULED.value)
    appointment_type = db.Column(db.String(50), nullable=False, default=AppointmentType.REGULAR.value)
    consultation_place_id = db.Column(db.Integer, db.ForeignKey('consultation_places.id'))
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    consultation_fee = db.Column(db.Float)  # Fee for the consultation
    
    # Relationships
    patient = db.relationship('Patient', backref='appointments')
    consultation_place = db.relationship('ConsultationPlace', backref='appointments')

    @validates('status')
    def validate_status(self, key, value):
        if value not in [status.value for status in AppointmentStatus]:
            raise ValueError(f"Invalid status. Must be one of: {[status.value for status in AppointmentStatus]}")
        return value

    @validates('appointment_type')
    def validate_appointment_type(self, key, value):
        if value not in [apt_type.value for apt_type in AppointmentType]:
            raise ValueError(f"Invalid appointment type. Must be one of: {[apt_type.value for apt_type in AppointmentType]}")
        return value

    @validates('scheduled_at')
    def validate_scheduled_at(self, key, value):
        if value < datetime.now():
            raise ValueError("Cannot schedule appointments in the past")
        return value

    def check_overlap(self, db_session):
        """Check if this appointment overlaps with other appointments"""
        end_time = self.scheduled_at + timedelta(minutes=self.duration)
        overlapping = db_session.query(Appointment).filter(
            Appointment.id != self.id,
            Appointment.status == AppointmentStatus.SCHEDULED.value,
            Appointment.scheduled_at < end_time,
            (Appointment.scheduled_at + timedelta(minutes=Appointment.duration)) > self.scheduled_at
        ).first()
        return overlapping is not None

class ConsultationPlace(BaseModel):
    __tablename__ = 'consultation_places'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    place_type = db.Column(db.String(50), nullable=False)  # clinic, home, online
    base_fee = db.Column(db.Float, default=0.0)  # Base consultation fee for this place
    
    # For clinic locations
    room_number = db.Column(db.String(20))
    floor = db.Column(db.String(10))
    
    # For home visits
    address = db.Column(db.Text)
    area = db.Column(db.String(100))
    landmark = db.Column(db.String(255))
    
    # For online consultations
    platform = db.Column(db.String(50))  # zoom, google-meet, custom-portal
    meeting_link = db.Column(db.String(255))
    
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

    @validates('place_type')
    def validate_place_type(self, key, value):
        if value not in [place_type.value for place_type in ConsultationType]:
            raise ValueError(f"Invalid place type. Must be one of: {[place_type.value for place_type in ConsultationType]}")
        return value

    def get_location_details(self):
        if self.place_type == ConsultationType.CLINIC.value:
            return f"Room {self.room_number}, Floor {self.floor}"
        elif self.place_type == ConsultationType.HOME.value:
            return f"{self.address}, Near {self.landmark}, {self.area}"
        else:  # online
            return f"{self.platform}: {self.meeting_link}"

class Schedule(BaseModel):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    break_start = db.Column(db.Time)
    break_end = db.Column(db.Time)
    is_available = db.Column(db.Boolean, default=True)
    consultation_type = db.Column(db.String(50), nullable=False)  # clinic, home, online
    max_appointments = db.Column(db.Integer, default=0)  # 0 means no limit
    notes = db.Column(db.Text)  # For any schedule-specific notes

    @validates('day_of_week')
    def validate_day_of_week(self, key, value):
        if not 0 <= value <= 6:
            raise ValueError("Day of week must be between 0 (Monday) and 6 (Sunday)")
        return value

    @validates('consultation_type')
    def validate_consultation_type(self, key, value):
        if value not in [cons_type.value for cons_type in ConsultationType]:
            raise ValueError(f"Invalid consultation type. Must be one of: {[cons_type.value for cons_type in ConsultationType]}")
        return value

    @validates('end_time')
    def validate_end_time(self, key, value):
        if hasattr(self, 'start_time') and self.start_time and value <= self.start_time:
            raise ValueError("End time must be after start time")
        return value

    @validates('break_end')
    def validate_break_end(self, key, value):
        if value and self.break_start and value <= self.break_start:
            raise ValueError("Break end time must be after break start time")
        return value 