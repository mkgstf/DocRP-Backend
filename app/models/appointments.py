from app import db
from .base import BaseModel
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import validates
from sqlalchemy.dialects.postgresql import ENUM
from app.utils.validators import check_appointment_overlap, validate_time_range, validate_future_date

# Create PostgreSQL native ENUMs
appointment_status_enum = ENUM('scheduled', 'completed', 'cancelled', 'no-show', name='appointment_status_enum', create_type=False)
appointment_type_enum = ENUM('regular', 'follow-up', 'emergency', name='appointment_type_enum', create_type=False)
consultation_type_enum = ENUM('clinic', 'home', 'online', name='consultation_type_enum', create_type=False)

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
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=False)
    duration = db.Column(db.Integer, default=30)
    status = db.Column(appointment_status_enum, nullable=False, default=AppointmentStatus.SCHEDULED.value)
    appointment_type = db.Column(appointment_type_enum, nullable=False, default=AppointmentType.REGULAR.value)
    consultation_place_id = db.Column(db.Integer, db.ForeignKey('consultation_places.id', ondelete='SET NULL'))
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    consultation_fee = db.Column(db.Numeric(10, 2))
    
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
        validate_future_date(value)
        return value

    def check_overlap(self, db_session):
        return check_appointment_overlap(self, db_session)

class ConsultationPlace(BaseModel):
    __tablename__ = 'consultation_places'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    place_type = db.Column(consultation_type_enum, nullable=False)
    base_fee = db.Column(db.Numeric(10, 2), default=0.0)
    
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
    day_of_week = db.Column(db.SmallInteger, nullable=False)
    start_time = db.Column(db.Time(timezone=True), nullable=False)
    end_time = db.Column(db.Time(timezone=True), nullable=False)
    break_start = db.Column(db.Time(timezone=True))
    break_end = db.Column(db.Time(timezone=True))
    is_available = db.Column(db.Boolean, default=True, server_default='true')
    consultation_type = db.Column(consultation_type_enum, nullable=False)
    max_appointments = db.Column(db.SmallInteger, default=0)
    notes = db.Column(db.Text)

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
        validate_time_range(self.start_time, value)
        return value

    @validates('break_end')
    def validate_break_end(self, key, value):
        if value and self.break_start:
            validate_time_range(self.break_start, value)
        return value 