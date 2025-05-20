from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Prescription, PrescriptionItem, Doctor, Patient, Medicine, PatientDiagnosis, Diagnosis, Appointment
from app import db
from app.db_utils import add_to_db, commit_changes, delete_from_db, get_paginated_results
from sqlalchemy import or_, and_
from datetime import datetime, date, timedelta
import uuid

prescriptions_bp = Blueprint('prescriptions', __name__)

@prescriptions_bp.route('/prescriptions', methods=['GET'])
@jwt_required()
def get_prescriptions():
    """
    Get all prescriptions for the current doctor with optional filtering and pagination
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    patient_uuid = request.args.get('patient_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = Prescription.query.filter_by(doctor_id=doctor.id)
    
    # Apply filters if provided
    if patient_uuid:
        patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({"msg": "Patient not found"}), 404
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Prescription.issue_date >= start)
        except ValueError:
            return jsonify({"msg": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Prescription.issue_date <= end)
        except ValueError:
            return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    # Order by issue date (newest first)
    query = query.order_by(Prescription.issue_date.desc())
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    prescriptions = []
    for prescription in pagination.items:
        patient = Patient.query.get(prescription.patient_id)
        
        prescription_data = {
            "id": prescription.uuid,
            "issue_date": prescription.issue_date.strftime('%Y-%m-%d'),
            "patient": {
                "id": patient.uuid,
                "name": f"{patient.first_name} {patient.last_name}"
            },
            "medicines_count": len(prescription.items),
            "notes": prescription.notes
        }
        
        if prescription.expiry_date:
            prescription_data["expiry_date"] = prescription.expiry_date.strftime('%Y-%m-%d')
        
        prescriptions.append(prescription_data)
    
    return jsonify({
        "prescriptions": prescriptions,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

@prescriptions_bp.route('/prescriptions/<string:prescription_uuid>', methods=['GET'])
@jwt_required()
def get_prescription(prescription_uuid):
    """
    Get a specific prescription by UUID with detailed information
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    prescription = Prescription.query.filter_by(uuid=prescription_uuid, doctor_id=doctor.id).first()
    
    if not prescription:
        return jsonify({"msg": "Prescription not found"}), 404
    
    patient = Patient.query.get(prescription.patient_id)
    
    # Format prescription data
    prescription_data = {
        "id": prescription.uuid,
        "issue_date": prescription.issue_date.strftime('%Y-%m-%d'),
        "expiry_date": prescription.expiry_date.strftime('%Y-%m-%d') if prescription.expiry_date else None,
        "notes": prescription.notes,
        "created_at": prescription.created_at.isoformat(),
        "updated_at": prescription.updated_at.isoformat(),
        "patient": {
            "id": patient.uuid,
            "name": f"{patient.first_name} {patient.last_name}",
            "dob": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
            "gender": patient.gender
        },
        "items": [],
        "diagnoses": []
    }
    
    # Get appointment if exists
    if prescription.appointment_id:
        appointment = Appointment.query.get(prescription.appointment_id)
        prescription_data["appointment"] = {
            "id": appointment.uuid,
            "date": appointment.date.strftime('%Y-%m-%d')
        }
    
    # Add prescription items (medicines)
    for item in prescription.items:
        medicine = Medicine.query.get(item.medicine_id)
        prescription_data["items"].append({
            "id": item.id,
            "medicine": {
                "id": medicine.uuid,
                "name": medicine.name,
                "dosage_form": medicine.dosage_form,
                "strength": medicine.strength
            },
            "dosage": item.dosage,
            "frequency": item.frequency,
            "duration": item.duration,
            "instructions": item.instructions
        })
    
    # Add diagnoses
    for diagnosis in prescription.diagnoses:
        diag = Diagnosis.query.get(diagnosis.diagnosis_id)
        prescription_data["diagnoses"].append({
            "id": diagnosis.id,
            "name": diag.name,
            "icd_code": diag.icd_code,
            "status": diagnosis.status,
            "notes": diagnosis.notes
        })
    
    return jsonify(prescription_data), 200

@prescriptions_bp.route('/prescriptions', methods=['POST'])
@jwt_required()
def create_prescription():
    """
    Create a new prescription with items and diagnoses
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    data = request.get_json()
    
    # Check required fields
    if 'patient_id' not in data:
        return jsonify({"msg": "Missing patient_id"}), 400
    
    if 'items' not in data or not data['items']:
        return jsonify({"msg": "Prescription must have at least one medicine"}), 400
    
    # Check if patient exists
    patient = Patient.query.filter_by(uuid=data['patient_id'], doctor_id=doctor.id).first()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    # Check appointment if provided
    appointment_id = None
    if 'appointment_id' in data and data['appointment_id']:
        appointment = Appointment.query.filter_by(
            uuid=data['appointment_id'], 
            doctor_id=doctor.id,
            patient_id=patient.id
        ).first()
        
        if not appointment:
            return jsonify({"msg": "Appointment not found or does not belong to this patient"}), 404
        
        appointment_id = appointment.id
    
    # Parse dates
    issue_date = date.today()
    if 'issue_date' in data and data['issue_date']:
        try:
            issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid issue_date format. Use YYYY-MM-DD"}), 400
    
    expiry_date = None
    if 'expiry_date' in data and data['expiry_date']:
        try:
            expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            if expiry_date < issue_date:
                return jsonify({"msg": "Expiry date cannot be before issue date"}), 400
        except ValueError:
            return jsonify({"msg": "Invalid expiry_date format. Use YYYY-MM-DD"}), 400
    
    # Create new prescription
    new_prescription = Prescription(
        uuid=str(uuid.uuid4()),
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_id=appointment_id,
        issue_date=issue_date,
        expiry_date=expiry_date,
        notes=data.get('notes')
    )
    
    # Add to database
    if not add_to_db(new_prescription):
        return jsonify({"msg": "Error creating prescription"}), 500
    
    # Add prescription items
    for item_data in data['items']:
        # Check required fields for each item
        if 'medicine_id' not in item_data:
            return jsonify({"msg": "Medicine ID is required for each prescription item"}), 400
        
        if 'dosage' not in item_data or 'frequency' not in item_data:
            return jsonify({"msg": "Dosage and frequency are required for each prescription item"}), 400
        
        # Check if medicine exists
        medicine = Medicine.query.filter_by(uuid=item_data['medicine_id']).first()
        if not medicine:
            return jsonify({"msg": f"Medicine not found: {item_data['medicine_id']}"}), 404
        
        # Create prescription item
        new_item = PrescriptionItem(
            prescription_id=new_prescription.id,
            medicine_id=medicine.id,
            dosage=item_data['dosage'],
            frequency=item_data['frequency'],
            duration=item_data.get('duration'),
            instructions=item_data.get('instructions')
        )
        
        db.session.add(new_item)
    
    # Add diagnoses if provided
    if 'diagnoses' in data and data['diagnoses']:
        for diag_data in data['diagnoses']:
            # Check if diagnosis exists
            diagnosis = None
            
            if 'diagnosis_id' in diag_data:
                diagnosis = Diagnosis.query.filter_by(uuid=diag_data['diagnosis_id']).first()
            elif 'diagnosis_name' in diag_data:
                # Try to find by name or create a new one
                diagnosis = Diagnosis.query.filter(Diagnosis.name.ilike(diag_data['diagnosis_name'])).first()
                
                if not diagnosis:
                    # Create new diagnosis
                    diagnosis = Diagnosis(
                        uuid=str(uuid.uuid4()),
                        name=diag_data['diagnosis_name'],
                        icd_code=diag_data.get('icd_code')
                    )
                    db.session.add(diagnosis)
                    db.session.flush()
            else:
                continue
            
            if diagnosis:
                # Create patient diagnosis
                new_patient_diagnosis = PatientDiagnosis(
                    patient_id=patient.id,
                    diagnosis_id=diagnosis.id,
                    prescription_id=new_prescription.id,
                    date_diagnosed=issue_date,
                    status=diag_data.get('status', 'active'),
                    notes=diag_data.get('notes')
                )
                
                db.session.add(new_patient_diagnosis)
    
    # Commit all changes
    if commit_changes():
        return jsonify({
            "msg": "Prescription created successfully",
            "prescription": {
                "id": new_prescription.uuid,
                "issue_date": new_prescription.issue_date.strftime('%Y-%m-%d')
            }
        }), 201
    
    return jsonify({"msg": "Error creating prescription"}), 500

@prescriptions_bp.route('/prescriptions/<string:prescription_uuid>', methods=['PUT'])
@jwt_required()
def update_prescription(prescription_uuid):
    """
    Update an existing prescription
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    prescription = Prescription.query.filter_by(uuid=prescription_uuid, doctor_id=doctor.id).first()
    
    if not prescription:
        return jsonify({"msg": "Prescription not found"}), 404
    
    data = request.get_json()
    
    # Update dates if provided
    if 'issue_date' in data:
        try:
            prescription.issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid issue_date format. Use YYYY-MM-DD"}), 400
    
    if 'expiry_date' in data:
        if data['expiry_date']:
            try:
                expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                if expiry_date < prescription.issue_date:
                    return jsonify({"msg": "Expiry date cannot be before issue date"}), 400
                prescription.expiry_date = expiry_date
            except ValueError:
                return jsonify({"msg": "Invalid expiry_date format. Use YYYY-MM-DD"}), 400
        else:
            prescription.expiry_date = None
    
    # Update notes if provided
    if 'notes' in data:
        prescription.notes = data['notes']
    
    # Update items if provided
    if 'items' in data and isinstance(data['items'], list):
        # Get current items
        current_items = {item.id: item for item in prescription.items}
        new_items = []
        
        for item_data in data['items']:
            # Check if item has an ID (existing item)
            if 'id' in item_data and item_data['id'] in current_items:
                item = current_items[item_data['id']]
                
                # Update fields
                if 'dosage' in item_data:
                    item.dosage = item_data['dosage']
                
                if 'frequency' in item_data:
                    item.frequency = item_data['frequency']
                
                if 'duration' in item_data:
                    item.duration = item_data['duration']
                
                if 'instructions' in item_data:
                    item.instructions = item_data['instructions']
                
                # Remove from current_items dict to track what was processed
                del current_items[item.id]
                new_items.append(item)
            else:
                # This is a new item to add
                if 'medicine_id' not in item_data or 'dosage' not in item_data or 'frequency' not in item_data:
                    continue
                
                medicine = Medicine.query.filter_by(uuid=item_data['medicine_id']).first()
                if not medicine:
                    continue
                
                new_item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_id=medicine.id,
                    dosage=item_data['dosage'],
                    frequency=item_data['frequency'],
                    duration=item_data.get('duration'),
                    instructions=item_data.get('instructions')
                )
                
                db.session.add(new_item)
                new_items.append(new_item)
        
        # Delete items that were not updated or kept
        for item in current_items.values():
            db.session.delete(item)
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Prescription updated successfully",
            "prescription": {
                "id": prescription.uuid,
                "issue_date": prescription.issue_date.strftime('%Y-%m-%d')
            }
        }), 200
    
    return jsonify({"msg": "Error updating prescription"}), 500

@prescriptions_bp.route('/prescriptions/<string:prescription_uuid>', methods=['DELETE'])
@jwt_required()
def delete_prescription(prescription_uuid):
    """
    Delete a prescription
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    prescription = Prescription.query.filter_by(uuid=prescription_uuid, doctor_id=doctor.id).first()
    
    if not prescription:
        return jsonify({"msg": "Prescription not found"}), 404
    
    # Delete prescription (cascade will delete items)
    if delete_from_db(prescription):
        return jsonify({"msg": "Prescription deleted successfully"}), 200
    
    return jsonify({"msg": "Error deleting prescription"}), 500

@prescriptions_bp.route('/prescriptions/export/<string:prescription_uuid>', methods=['GET'])
@jwt_required()
def export_prescription(prescription_uuid):
    """
    Export prescription as PDF (placeholder)
    In a real implementation, this would generate a PDF and return it
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    prescription = Prescription.query.filter_by(uuid=prescription_uuid, doctor_id=doctor.id).first()
    
    if not prescription:
        return jsonify({"msg": "Prescription not found"}), 404
    
    # This would be replaced with actual PDF generation
    return jsonify({
        "msg": "PDF export capability would be implemented here",
        "prescription_id": prescription.uuid
    }), 200

@prescriptions_bp.route('/patients/<string:patient_uuid>/prescriptions', methods=['GET'])
@jwt_required()
def patient_prescriptions(patient_uuid):
    """
    Get all prescriptions for a specific patient
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Check if patient exists and belongs to the doctor
    patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404
    
    # Get query parameters for pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query for patient's prescriptions
    query = Prescription.query.filter_by(patient_id=patient.id, doctor_id=doctor.id)
    
    # Order by issue date (newest first)
    query = query.order_by(Prescription.issue_date.desc())
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    prescriptions = []
    for prescription in pagination.items:
        prescription_data = {
            "id": prescription.uuid,
            "issue_date": prescription.issue_date.strftime('%Y-%m-%d'),
            "expiry_date": prescription.expiry_date.strftime('%Y-%m-%d') if prescription.expiry_date else None,
            "notes": prescription.notes,
            "medicines_count": len(prescription.items),
            "created_at": prescription.created_at.isoformat(),
            "updated_at": prescription.updated_at.isoformat()
        }
        
        # Add items summary
        medicine_names = []
        for item in prescription.items:
            medicine = Medicine.query.get(item.medicine_id)
            if medicine:
                medicine_names.append(medicine.name)
        
        prescription_data["medicines"] = medicine_names
        
        prescriptions.append(prescription_data)
    
    return jsonify({
        "prescriptions": prescriptions,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200