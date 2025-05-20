from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Medicine, Doctor
from app import db
from app.db_utils import add_to_db, commit_changes, delete_from_db, get_paginated_results
from sqlalchemy import or_
import uuid

medicines_bp = Blueprint('medicines', __name__)

@medicines_bp.route('/medicines', methods=['GET'])
@jwt_required()
def get_medicines():
    """
    Get all medicines with optional filtering and pagination
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
    query = Medicine.query
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Medicine.name.ilike(search_term),
                Medicine.description.ilike(search_term),
                Medicine.dosage_form.ilike(search_term),
                Medicine.manufacturer.ilike(search_term)
            )
        )
    
    # Order by name
    query = query.order_by(Medicine.name)
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    medicines = []
    for medicine in pagination.items:
        medicines.append({
            "id": medicine.uuid,
            "name": medicine.name,
            "description": medicine.description,
            "dosage_form": medicine.dosage_form,
            "strength": medicine.strength,
            "manufacturer": medicine.manufacturer
        })
    
    return jsonify({
        "medicines": medicines,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

@medicines_bp.route('/medicines/<string:medicine_uuid>', methods=['GET'])
@jwt_required()
def get_medicine(medicine_uuid):
    """
    Get a specific medicine by UUID
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    medicine = Medicine.query.filter_by(uuid=medicine_uuid).first()
    
    if not medicine:
        return jsonify({"msg": "Medicine not found"}), 404
    
    # Format medicine data
    medicine_data = {
        "id": medicine.uuid,
        "name": medicine.name,
        "description": medicine.description,
        "dosage_form": medicine.dosage_form,
        "strength": medicine.strength,
        "manufacturer": medicine.manufacturer,
        "created_at": medicine.created_at.isoformat(),
        "updated_at": medicine.updated_at.isoformat()
    }
    
    return jsonify(medicine_data), 200

@medicines_bp.route('/medicines', methods=['POST'])
@jwt_required()
def create_medicine():
    """
    Create a new medicine
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
    
    # Check if medicine already exists
    existing_medicine = Medicine.query.filter(Medicine.name.ilike(data['name'])).first()
    if existing_medicine:
        return jsonify({"msg": "Medicine with this name already exists"}), 409
    
    # Create new medicine
    new_medicine = Medicine(
        uuid=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description'),
        dosage_form=data.get('dosage_form'),
        strength=data.get('strength'),
        manufacturer=data.get('manufacturer')
    )
    
    # Add to database
    if add_to_db(new_medicine):
        return jsonify({
            "msg": "Medicine created successfully",
            "medicine": {
                "id": new_medicine.uuid,
                "name": new_medicine.name
            }
        }), 201
    
    return jsonify({"msg": "Error creating medicine"}), 500

@medicines_bp.route('/medicines/<string:medicine_uuid>', methods=['PUT'])
@jwt_required()
def update_medicine(medicine_uuid):
    """
    Update an existing medicine
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    medicine = Medicine.query.filter_by(uuid=medicine_uuid).first()
    
    if not medicine:
        return jsonify({"msg": "Medicine not found"}), 404
    
    data = request.get_json()
    
    # Update fields
    updateable_fields = ['description', 'dosage_form', 'strength', 'manufacturer']
    for field in updateable_fields:
        if field in data:
            setattr(medicine, field, data[field])
    
    # Update name if provided and not already in use
    if 'name' in data and data['name'] != medicine.name:
        existing_medicine = Medicine.query.filter(
            Medicine.name.ilike(data['name']),
            Medicine.id != medicine.id
        ).first()
        
        if existing_medicine:
            return jsonify({"msg": "Medicine with this name already exists"}), 409
        
        medicine.name = data['name']
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Medicine updated successfully",
            "medicine": {
                "id": medicine.uuid,
                "name": medicine.name
            }
        }), 200
    
    return jsonify({"msg": "Error updating medicine"}), 500

@medicines_bp.route('/medicines/<string:medicine_uuid>', methods=['DELETE'])
@jwt_required()
def delete_medicine(medicine_uuid):
    """
    Delete a medicine
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    medicine = Medicine.query.filter_by(uuid=medicine_uuid).first()
    
    if not medicine:
        return jsonify({"msg": "Medicine not found"}), 404
    
    # Check if medicine is in use
    if medicine.prescription_items:
        return jsonify({"msg": "Cannot delete medicine that is in use in prescriptions"}), 409
    
    # Delete medicine
    if delete_from_db(medicine):
        return jsonify({"msg": "Medicine deleted successfully"}), 200
    
    return jsonify({"msg": "Error deleting medicine"}), 500

@medicines_bp.route('/medicines/search', methods=['GET'])
@jwt_required()
def search_medicines():
    """
    Search medicines for autocomplete
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
    
    medicines = Medicine.query.filter(
        Medicine.name.ilike(search_term)
    ).order_by(Medicine.name).limit(limit).all()
    
    results = []
    for medicine in medicines:
        result = {
            "id": medicine.uuid,
            "name": medicine.name
        }
        
        if medicine.dosage_form:
            result["dosage_form"] = medicine.dosage_form
            
        if medicine.strength:
            result["strength"] = medicine.strength
            
        results.append(result)
    
    return jsonify({"results": results}), 200