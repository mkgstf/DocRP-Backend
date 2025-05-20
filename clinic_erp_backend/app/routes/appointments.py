from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Appointment, Doctor, Patient
from app import db
from app.db import add_to_db, commit_changes, delete_from_db, get_paginated_results
from sqlalchemy import or_, and_
from datetime import datetime, date, time, timedelta
import uuid

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """
    Get all appointments for the current doctor with optional filtering and pagination
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    patient_uuid = request.args.get('patient_id')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    
    # Apply filters if provided
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Appointment.date >= start)
        except ValueError:
            return jsonify({"msg": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Appointment.date <= end)
        except ValueError:
            return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    if patient_uuid:
        patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({"msg": "Patient not found"}), 404
    
    if status:
        query = query.filter_by(status=status)
    
    # Order by date and time
    query = query.order_by(Appointment.date, Appointment.start_time)
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    appointments = []
    for appointment in pagination.items:
        patient = Patient.query.get(appointment.patient_id)
        appointments.append({
            "id": appointment.uuid,
            "date": appointment.date.strftime('%Y-%m-%d'),
            "start_time": appointment.start_time.strftime('%H:%M'),
            "end_time": appointment.end_time.strftime('%H:%M'),
            "status": appointment.status,
            "reason": appointment.reason,
            "notes": appointment.notes,
            "patient": {
                "id": patient.uuid,
                "name": f"{patient.first_name} {patient.last_name}"
            }
        })
    
    return jsonify({
        "appointments": appointments,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

@appointments_bp.route('/appointments/<string:appointment_uuid>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_uuid):
    """
    Get a specific appointment by UUID
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    appointment = Appointment.query.filter_by(uuid=appointment_uuid, doctor_id=doctor.id).first()
    
    if not appointment:
        return jsonify({"msg": "Appointment not found"}), 404
    
    patient = Patient.query.get(appointment.patient_id)
    
    # Format appointment data
    appointment_data = {
        "id": appointment.uuid,
        "date": appointment.date.strftime('%Y-%m-%d'),
        "start_time": appointment.start_time.strftime('%H:%M'),
        "end_time": appointment.end_time.strftime('%H:%M'),
        "status": appointment.status,
        "reason": appointment.reason,
        "notes": appointment.notes,
        "created_at": appointment.created_at.isoformat(),
        "updated_at": appointment.updated_at.isoformat(),
        "patient": {
            "id": patient.uuid,
            "name": f"{patient.first_name} {patient.last_name}",
            "dob": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None
        }
    }
    
    return jsonify(appointment_data), 200

@appointments_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    """
    Create a new appointment
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    data = request.get_json()
    
    # Check required fields
    required_fields = ['patient_id', 'date', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing {field}"}), 400
    
    # Check if patient exists
    patient = Patient.query.filter_by(uuid=data['patient_id'], doctor_id=doctor.id).first()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    # Parse date and times
    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    except ValueError:
        return jsonify({"msg": "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for times"}), 400
    
    # Validate times
    if start_time >= end_time:
        return jsonify({"msg": "End time must be after start time"}), 400
    
    # Check for conflicting appointments
    conflicts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date == appointment_date,
        or_(
            and_(Appointment.start_time <= start_time, Appointment.end_time > start_time),
            and_(Appointment.start_time < end_time, Appointment.end_time >= end_time),
            and_(Appointment.start_time >= start_time, Appointment.end_time <= end_time)
        )
    ).all()
    
    if conflicts:
        return jsonify({"msg": "This time slot conflicts with an existing appointment"}), 409
    
    # Create new appointment
    new_appointment = Appointment(
        uuid=str(uuid.uuid4()),
        doctor_id=doctor.id,
        patient_id=patient.id,
        date=appointment_date,
        start_time=start_time,
        end_time=end_time,
        reason=data.get('reason'),
        status=data.get('status', 'scheduled'),
        notes=data.get('notes')
    )
    
    # Add to database
    if add_to_db(new_appointment):
        return jsonify({
            "msg": "Appointment created successfully",
            "appointment": {
                "id": new_appointment.uuid,
                "date": new_appointment.date.strftime('%Y-%m-%d'),
                "start_time": new_appointment.start_time.strftime('%H:%M')
            }
        }), 201
    
    return jsonify({"msg": "Error creating appointment"}), 500

@appointments_bp.route('/appointments/<string:appointment_uuid>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_uuid):
    """
    Update an existing appointment
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    appointment = Appointment.query.filter_by(uuid=appointment_uuid, doctor_id=doctor.id).first()
    
    if not appointment:
        return jsonify({"msg": "Appointment not found"}), 404
    
    data = request.get_json()
    
    # Store original values for conflict checking
    original_date = appointment.date
    original_start = appointment.start_time
    original_end = appointment.end_time
    
    # Update patient if provided
    if 'patient_id' in data:
        patient = Patient.query.filter_by(uuid=data['patient_id'], doctor_id=doctor.id).first()
        if not patient:
            return jsonify({"msg": "Patient not found"}), 404
        appointment.patient_id = patient.id
    
    # Update date if provided
    if 'date' in data:
        try:
            appointment.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Update times if provided
    if 'start_time' in data:
        try:
            appointment.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify({"msg": "Invalid start_time format. Use HH:MM"}), 400
    
    if 'end_time' in data:
        try:
            appointment.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({"msg": "Invalid end_time format. Use HH:MM"}), 400
    
    # Validate times
    if appointment.start_time >= appointment.end_time:
        return jsonify({"msg": "End time must be after start time"}), 400
    
    # Check for conflicts only if date or times changed
    if (appointment.date != original_date or
        appointment.start_time != original_start or
        appointment.end_time != original_end):
        
        conflicts = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date == appointment.date,
            Appointment.id != appointment.id,
            or_(
                and_(Appointment.start_time <= appointment.start_time, Appointment.end_time > appointment.start_time),
                and_(Appointment.start_time < appointment.end_time, Appointment.end_time >= appointment.end_time),
                and_(Appointment.start_time >= appointment.start_time, Appointment.end_time <= appointment.end_time)
            )
        ).all()
        
        if conflicts:
            return jsonify({"msg": "This time slot conflicts with an existing appointment"}), 409
    
    # Update other fields
    if 'status' in data:
        appointment.status = data['status']
    
    if 'reason' in data:
        appointment.reason = data['reason']
    
    if 'notes' in data:
        appointment.notes = data['notes']
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Appointment updated successfully",
            "appointment": {
                "id": appointment.uuid,
                "date": appointment.date.strftime('%Y-%m-%d'),
                "start_time": appointment.start_time.strftime('%H:%M')
            }
        }), 200
    
    return jsonify({"msg": "Error updating appointment"}), 500

@appointments_bp.route('/appointments/<string:appointment_uuid>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_uuid):
    """
    Delete an appointment
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    appointment = Appointment.query.filter_by(uuid=appointment_uuid, doctor_id=doctor.id).first()
    
    if not appointment:
        return jsonify({"msg": "Appointment not found"}), 404
    
    # Delete appointment
    if delete_from_db(appointment):
        return jsonify({"msg": "Appointment deleted successfully"}), 200
    
    return jsonify({"msg": "Error deleting appointment"}), 500

@appointments_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar():
    """
    Get calendar view of appointments for a specific date range
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to current week if not specified
    if not start_date:
        today = date.today()
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')  # Monday
    
    if not end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = (start + timedelta(days=6)).strftime('%Y-%m-%d')  # Sunday
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Get appointments in date range
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= start,
        Appointment.date <= end
    ).order_by(Appointment.date, Appointment.start_time).all()
    
    # Format results by date
    calendar = {}
    for appointment in appointments:
        date_str = appointment.date.strftime('%Y-%m-%d')
        
        if date_str not in calendar:
            calendar[date_str] = []
        
        patient = Patient.query.get(appointment.patient_id)
        calendar[date_str].append({
            "id": appointment.uuid,
            "start_time": appointment.start_time.strftime('%H:%M'),
            "end_time": appointment.end_time.strftime('%H:%M'),
            "status": appointment.status,
            "reason": appointment.reason,
            "patient": {
                "id": patient.uuid,
                "name": f"{patient.first_name} {patient.last_name}"
            }
        })
    
    return jsonify({
        "calendar": calendar,
        "range": {
            "start": start_date,
            "end": end_date
        }
    }), 200