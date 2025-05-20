from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Diagnosis, Doctor, PatientDiagnosis, Patient
from app import db
from app.db import add_to_db, commit_changes, delete_from_db, get_paginated_results
from sqlalchemy import or_
import uuid

diagnoses_bp = Blueprint('diagnoses', __name__)

@diagnoses_bp.route('/diagnoses', methods=['GET'])
@jwt_required()
def get_diagnoses():
    """
    Get all diagnoses with optional filtering and pagination
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    search = request.args.get('search', '')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = Diagnosis.query
    
    # Apply filters if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Diagnosis.name.ilike(search_term),
                Diagnosis.description.ilike(search_term),
                Diagnosis.icd_code.ilike(search_term)
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    # Order by name
    query = query.order_by(Diagnosis.name)
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    diagnoses = []
    for diagnosis in pagination.items:
        diagnoses.append({
            "id": diagnosis.uuid,
            "name": diagnosis.name,
            "description": diagnosis.description,
            "icd_code": diagnosis.icd_code,
            "category": diagnosis.category
        })
    
    return jsonify({
        "diagnoses": diagnoses,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

@diagnoses_bp.route('/diagnoses/<string:diagnosis_uuid>', methods=['GET'])
@jwt_required()
def get_diagnosis(diagnosis_uuid):
    """
    Get a specific diagnosis by UUID
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    diagnosis = Diagnosis.query.filter_by(uuid=diagnosis_uuid).first()
    
    if not diagnosis:
        return jsonify({"msg": "Diagnosis not found"}), 404
    
    # Format diagnosis data
    diagnosis_data = {
        "id": diagnosis.uuid,
        "name": diagnosis.name,
        "description": diagnosis.description,
        "icd_code": diagnosis.icd_code,
        "category": diagnosis.category,
        "created_at": diagnosis.created_at.isoformat(),
        "updated_at": diagnosis.updated_at.isoformat()
    }
    
    return jsonify(diagnosis_data), 200

@diagnoses_bp.route('/diagnoses', methods=['POST'])
@jwt_required()
def create_diagnosis():
    """
    Create a new diagnosis
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    data = request.get_json()
    
    # Check required fields
    if 'name' not in data:
        return jsonify({"msg": "Missing name"}), 400
    
    # Check if diagnosis already exists
    existing_diagnosis = Diagnosis.query.filter(Diagnosis.name.ilike(data['name'])).first()
    if existing_diagnosis:
        return jsonify({"msg": "Diagnosis with this name already exists"}), 409
    
    # Create new diagnosis
    new_diagnosis = Diagnosis(
        uuid=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description'),
        icd_code=data.get('icd_code'),
        category=data.get('category')
    )
    
    # Add to database
    if add_to_db(new_diagnosis):
        return jsonify({
            "msg": "Diagnosis created successfully",
            "diagnosis": {
                "id": new_diagnosis.uuid,
                "name": new_diagnosis.name
            }
        }), 201
    
    return jsonify({"msg": "Error creating diagnosis"}), 500

@diagnoses_bp.route('/diagnoses/<string:diagnosis_uuid>', methods=['PUT'])
@jwt_required()
def update_diagnosis(diagnosis_uuid):
    """
    Update an existing diagnosis
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    diagnosis = Diagnosis.query.filter_by(uuid=diagnosis_uuid).first()
    
    if not diagnosis:
        return jsonify({"msg": "Diagnosis not found"}), 404
    
    data = request.get_json()
    
    # Update fields
    updateable_fields = ['description', 'icd_code', 'category']
    for field in updateable_fields:
        if field in data:
            setattr(diagnosis, field, data[field])
    
    # Update name if provided and not already in use
    if 'name' in data and data['name'] != diagnosis.name:
        existing_diagnosis = Diagnosis.query.filter(
            Diagnosis.name.ilike(data['name']),
            Diagnosis.id != diagnosis.id
        ).first()
        
        if existing_diagnosis:
            return jsonify({"msg": "Diagnosis with this name already exists"}), 409
        
        diagnosis.name = data['name']
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Diagnosis updated successfully",
            "diagnosis": {
                "id": diagnosis.uuid,
                "name": diagnosis.name
            }
        }), 200
    
    return jsonify({"msg": "Error updating diagnosis"}), 500

@diagnoses_bp.route('/diagnoses/<string:diagnosis_uuid>', methods=['DELETE'])
@jwt_required()
def delete_diagnosis(diagnosis_uuid):
    """
    Delete a diagnosis
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    diagnosis = Diagnosis.query.filter_by(uuid=diagnosis_uuid).first()
    
    if not diagnosis:
        return jsonify({"msg": "Diagnosis not found"}), 404
    
    # Check if diagnosis is in use
    if diagnosis.patient_diagnoses:
        return jsonify({"msg": "Cannot delete diagnosis that is in use by patients"}), 409
    
    # Delete diagnosis
    if delete_from_db(diagnosis):
        return jsonify({"msg": "Diagnosis deleted successfully"}), 200
    
    return jsonify({"msg": "Error deleting diagnosis"}), 500

@diagnoses_bp.route('/diagnoses/search', methods=['GET'])
@jwt_required()
def search_diagnoses():
    """
    Search diagnoses for autocomplete
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
    
    diagnoses = Diagnosis.query.filter(
        or_(
            Diagnosis.name.ilike(search_term),
            Diagnosis.icd_code.ilike(search_term)
        )
    ).order_by(Diagnosis.name).limit(limit).all()
    
    results = []
    for diagnosis in diagnoses:
        result = {
            "id": diagnosis.uuid,
            "name": diagnosis.name
        }
        
        if diagnosis.icd_code:
            result["icd_code"] = diagnosis.icd_code
            
        if diagnosis.category:
            result["category"] = diagnosis.category
            
        results.append(result)
    
    return jsonify({"results": results}), 200

@diagnoses_bp.route('/patients/<string:patient_uuid>/diagnoses', methods=['GET'])
@jwt_required()
def get_patient_diagnoses(patient_uuid):
    """
    Get all diagnoses for a specific patient
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
    
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    # Get patient diagnoses
    patient_diagnoses = PatientDiagnosis.query.filter_by(
        patient_id=patient.id
    ).order_by(PatientDiagnosis.date_diagnosed.desc()).all()
    
    # Format results
    diagnoses = []
    for patient_diagnosis in patient_diagnoses:
        diagnosis = Diagnosis.query.get(patient_diagnosis.diagnosis_id)
        diagnoses.append({
            "id": patient_diagnosis.id,
            "diagnosis": {
                "id": diagnosis.uuid,
                "name": diagnosis.name,
                "icd_code": diagnosis.icd_code
            },
            "date_diagnosed": patient_diagnosis.date_diagnosed.strftime('%Y-%m-%d'),
            "status": patient_diagnosis.status,
            "notes": patient_diagnosis.notes
        })
    
    return jsonify({"diagnoses": diagnoses}), 200

@diagnoses_bp.route('/patients/<string:patient_uuid>/diagnoses', methods=['POST'])
@jwt_required()
def add_patient_diagnosis(patient_uuid):
    """
    Add a diagnosis to a patient
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
    
    # Check required fields
    diagnosis = None
    
    if 'diagnosis_id' in data:
        diagnosis = Diagnosis.query.filter_by(uuid=data['diagnosis_id']).first()
    elif 'diagnosis_name' in data:
        # Try to find by name or create a new one
        diagnosis = Diagnosis.query.filter(Diagnosis.name.ilike(data['diagnosis_name'])).first()
        
        if not diagnosis:
            # Create new diagnosis
            diagnosis = Diagnosis(
                uuid=str(uuid.uuid4()),
                name=data['diagnosis_name'],
                icd_code=data.get('icd_code')
            )
            db.session.add(diagnosis)
            db.session.flush()
    else:
        return jsonify({"msg": "Either diagnosis_id or diagnosis_name is required"}), 400
    
    if not diagnosis:
        return jsonify({"msg": "Diagnosis not found"}), 404
    
    # Create patient diagnosis
    new_patient_diagnosis = PatientDiagnosis(
        patient_id=patient.id,
        diagnosis_id=diagnosis.id,
        date_diagnosed=data.get('date_diagnosed', db.func.current_date()),
        status=data.get('status', 'active'),
        notes=data.get('notes')
    )
    
    # Add to database
    if add_to_db(new_patient_diagnosis):
        return jsonify({
            "msg": "Diagnosis added to patient successfully",
            "patient_diagnosis": {
                "id": new_patient_diagnosis.id,
                "diagnosis_name": diagnosis.name
            }
        }), 201
    
    return jsonify({"msg": "Error adding diagnosis to patient"}), 500

@diagnoses_bp.route('/patients/diagnoses/<int:patient_diagnosis_id>', methods=['PUT'])
@jwt_required()
def update_patient_diagnosis(patient_diagnosis_id):
    """
    Update a patient's diagnosis
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Find the patient diagnosis and verify access
    patient_diagnosis = PatientDiagnosis.query.get(patient_diagnosis_id)
    
    if not patient_diagnosis:
        return jsonify({"msg": "Patient diagnosis not found"}), 404
    
    patient = Patient.query.get(patient_diagnosis.patient_id)
    
    if not patient or patient.doctor_id != doctor.id:
        return jsonify({"msg": "Access denied to this patient diagnosis"}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'status' in data:
        patient_diagnosis.status = data['status']
    
    if 'notes' in data:
        patient_diagnosis.notes = data['notes']
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Patient diagnosis updated successfully"
        }), 200
    
    return jsonify({"msg": "Error updating patient diagnosis"}), 500

@diagnoses_bp.route('/patients/diagnoses/<int:patient_diagnosis_id>', methods=['DELETE'])
@jwt_required()
def delete_patient_diagnosis(patient_diagnosis_id):
    """
    Remove a diagnosis from a patient
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Find the patient diagnosis and verify access
    patient_diagnosis = PatientDiagnosis.query.get(patient_diagnosis_id)
    
    if not patient_diagnosis:
        return jsonify({"msg": "Patient diagnosis not found"}), 404
    
    patient = Patient.query.get(patient_diagnosis.patient_id)
    
    if not patient or patient.doctor_id != doctor.id:
        return jsonify({"msg": "Access denied to this patient diagnosis"}), 403
    
    # Delete patient diagnosis
    if delete_from_db(patient_diagnosis):
        return jsonify({"msg": "Patient diagnosis removed successfully"}), 200
    
    return jsonify({"msg": "Error removing patient diagnosis"}), 500