from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Patient, Doctor
from app import db
from app.db_utils import add_to_db, commit_changes, delete_from_db, get_paginated_results
from sqlalchemy import or_
from datetime import datetime
import uuid

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    """
    Get all patients for the current doctor with optional filtering and pagination
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = Patient.query.filter_by(doctor_id=doctor.id)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.email.ilike(search_term),
                Patient.phone.ilike(search_term)
            )
        )
    
    # Order by last name then first name
    query = query.order_by(Patient.last_name, Patient.first_name)
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    patients = []
    for patient in pagination.items:
        patients.append({
            "id": patient.uuid,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
            "gender": patient.gender,
            "email": patient.email,
            "phone": patient.phone,
            "created_at": patient.created_at.isoformat()
        })
    
    return jsonify({
        "patients": patients,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

@patients_bp.route('/patients/<string:patient_uuid>', methods=['GET'])
@jwt_required()
def get_patient(patient_uuid):
    """
    Get a specific patient by UUID
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
    
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    # Format patient data
    patient_data = {
        "id": patient.uuid,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
        "gender": patient.gender,
        "email": patient.email,
        "phone": patient.phone,
        "address": patient.address,
        "medical_history": patient.medical_history,
        "insurance_info": patient.insurance_info,
        "created_at": patient.created_at.isoformat(),
        "updated_at": patient.updated_at.isoformat()
    }
    
    return jsonify(patient_data), 200

@patients_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    """
    Create a new patient
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    data = request.get_json()
    
    # Check required fields
    required_fields = ['first_name', 'last_name', 'date_of_birth']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing {field}"}), 400
    
    # Parse date_of_birth
    try:
        date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid date_of_birth format. Use YYYY-MM-DD"}), 400
    
    # Create new patient
    new_patient = Patient(
        uuid=str(uuid.uuid4()),
        doctor_id=doctor.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=date_of_birth,
        gender=data.get('gender'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        medical_history=data.get('medical_history'),
        insurance_info=data.get('insurance_info')
    )
    
    # Add to database
    if add_to_db(new_patient):
        return jsonify({
            "msg": "Patient created successfully",
            "patient": {
                "id": new_patient.uuid,
                "first_name": new_patient.first_name,
                "last_name": new_patient.last_name
            }
        }), 201
    
    return jsonify({"msg": "Error creating patient"}), 500

@patients_bp.route('/patients/<string:patient_uuid>', methods=['PUT'])
@jwt_required()
def update_patient(patient_uuid):
    """
    Update an existing patient
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
    
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    data = request.get_json()
    
    # Update fields
    updateable_fields = [
        'first_name', 'last_name', 'gender', 'email', 'phone',
        'address', 'medical_history', 'insurance_info'
    ]
    
    for field in updateable_fields:
        if field in data:
            setattr(patient, field, data[field])
    
    # Update date_of_birth if provided
    if 'date_of_birth' in data:
        try:
            patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid date_of_birth format. Use YYYY-MM-DD"}), 400
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Patient updated successfully",
            "patient": {
                "id": patient.uuid,
                "first_name": patient.first_name,
                "last_name": patient.last_name
            }
        }), 200
    
    return jsonify({"msg": "Error updating patient"}), 500

@patients_bp.route('/patients/<string:patient_uuid>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_uuid):
    """
    Delete a patient
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
    
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    # Delete patient
    if delete_from_db(patient):
        return jsonify({"msg": "Patient deleted successfully"}), 200
    
    return jsonify({"msg": "Error deleting patient"}), 500

@patients_bp.route('/patients/search', methods=['GET'])
@jwt_required()
def search_patients():
    """
    Search patients for autocomplete
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify({"results": []}), 200
    
    search_term = f"%{query}%"
    
    patients = Patient.query.filter_by(doctor_id=doctor.id).filter(
        or_(
            Patient.first_name.ilike(search_term),
            Patient.last_name.ilike(search_term),
            db.func.concat(Patient.first_name, ' ', Patient.last_name).ilike(search_term)
        )
    ).limit(limit).all()
    
    results = []
    for patient in patients:
        results.append({
            "id": patient.uuid,
            "name": f"{patient.first_name} {patient.last_name}",
            "dob": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None
        })
    
    return jsonify({"results": results}), 200