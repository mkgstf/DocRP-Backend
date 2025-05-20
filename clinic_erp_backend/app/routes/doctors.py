from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from app.models.models import Doctor
from app import db
from app.db import add_to_db, commit_changes
from werkzeug.security import check_password_hash
import datetime
import uuid

doctors_bp = Blueprint('doctors', __name__)

@doctors_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint for doctor login
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    
    doctor = Doctor.query.filter_by(username=username).first()
    
    if doctor and doctor.check_password(password):
        if not doctor.active:
            return jsonify({"msg": "Account is deactivated"}), 401
        
        # Create tokens
        access_token = create_access_token(identity=doctor.uuid)
        refresh_token = create_refresh_token(identity=doctor.uuid)
        
        return jsonify({
            "msg": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "doctor": {
                "id": doctor.uuid,
                "username": doctor.username,
                "email": doctor.email,
                "first_name": doctor.first_name,
                "last_name": doctor.last_name,
                "specialization": doctor.specialization
            }
        }), 200
    
    return jsonify({"msg": "Bad username or password"}), 401

@doctors_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor or not doctor.active:
        return jsonify({"msg": "User not found or inactive"}), 401
        
    access_token = create_access_token(identity=current_user_uuid)
    return jsonify({"access_token": access_token}), 200

@doctors_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new doctor - this would typically be restricted to admin users
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    data = request.get_json()
    
    # Check required fields
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing {field}"}), 400
    
    # Check if username or email already exists
    if Doctor.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 409
    
    if Doctor.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already exists"}), 409
    
    # Create new doctor
    new_doctor = Doctor(
        uuid=str(uuid.uuid4()),
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        specialization=data.get('specialization', None),
        phone=data.get('phone', None)
    )
    
    # Set password
    new_doctor.set_password(data['password'])
    
    # Add to database
    if add_to_db(new_doctor):
        return jsonify({
            "msg": "Doctor registered successfully",
            "doctor": {
                "id": new_doctor.uuid,
                "username": new_doctor.username,
                "email": new_doctor.email
            }
        }), 201
    
    return jsonify({"msg": "Error registering doctor"}), 500

@doctors_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current doctor's profile
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    return jsonify({
        "id": doctor.uuid,
        "username": doctor.username,
        "email": doctor.email,
        "first_name": doctor.first_name,
        "last_name": doctor.last_name,
        "specialization": doctor.specialization,
        "phone": doctor.phone
    }), 200

@doctors_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update current doctor's profile
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    data = request.get_json()
    
    # Update fields
    updateable_fields = ['first_name', 'last_name', 'specialization', 'phone']
    for field in updateable_fields:
        if field in data:
            setattr(doctor, field, data[field])
    
    # Update email if provided and not already in use
    if 'email' in data and data['email'] != doctor.email:
        if Doctor.query.filter_by(email=data['email']).first():
            return jsonify({"msg": "Email already in use"}), 409
        doctor.email = data['email']
    
    # Update password if provided
    if 'password' in data and data['password']:
        doctor.set_password(data['password'])
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Profile updated successfully",
            "doctor": {
                "id": doctor.uuid,
                "username": doctor.username,
                "email": doctor.email,
                "first_name": doctor.first_name,
                "last_name": doctor.last_name,
                "specialization": doctor.specialization,
                "phone": doctor.phone
            }
        }), 200
    
    return jsonify({"msg": "Error updating profile"}), 500