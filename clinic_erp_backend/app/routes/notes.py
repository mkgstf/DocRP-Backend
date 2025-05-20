from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Note, Tag, NoteTag, Doctor, Patient, Appointment
from app import db
from app.db import add_to_db, commit_changes, delete_from_db, get_paginated_results
from sqlalchemy import or_, and_
from datetime import datetime
import uuid

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET'])
@jwt_required()
def get_notes():
    """
    Get all notes for the current doctor with optional filtering and pagination
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    patient_uuid = request.args.get('patient_id')
    category = request.args.get('category')
    tag_id = request.args.get('tag_id')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = Note.query.filter_by(doctor_id=doctor.id)
    
    # Apply filters if provided
    if patient_uuid:
        patient = Patient.query.filter_by(uuid=patient_uuid, doctor_id=doctor.id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({"msg": "Patient not found"}), 404
    
    if category:
        query = query.filter_by(category=category)
    
    if tag_id:
        query = query.join(NoteTag).filter(NoteTag.tag_id == tag_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Note.title.ilike(search_term),
                Note.content.ilike(search_term)
            )
        )
    
    # Order by creation date (newest first)
    query = query.order_by(Note.created_at.desc())
    
    # Get paginated results
    pagination = get_paginated_results(query, page, per_page)
    
    # Format results
    notes = []
    for note in pagination.items:
        patient = Patient.query.get(note.patient_id)
        
        note_data = {
            "id": note.uuid,
            "title": note.title,
            "content": note.content,
            "category": note.category,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
            "patient": {
                "id": patient.uuid,
                "name": f"{patient.first_name} {patient.last_name}"
            },
            "tags": []
        }
        
        # Add tags
        for note_tag in note.tags:
            tag = Tag.query.get(note_tag.tag_id)
            note_data["tags"].append({
                "id": tag.id,
                "name": tag.name,
                "color": tag.color
            })
        
        notes.append(note_data)
    
    return jsonify({
        "notes": notes,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200

@notes_bp.route('/notes/<string:note_uuid>', methods=['GET'])
@jwt_required()
def get_note(note_uuid):
    """
    Get a specific note by UUID
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    note = Note.query.filter_by(uuid=note_uuid, doctor_id=doctor.id).first()
    
    if not note:
        return jsonify({"msg": "Note not found"}), 404
    
    patient = Patient.query.get(note.patient_id)
    
    # Format note data
    note_data = {
        "id": note.uuid,
        "title": note.title,
        "content": note.content,
        "category": note.category,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
        "patient": {
            "id": patient.uuid,
            "name": f"{patient.first_name} {patient.last_name}"
        },
        "tags": []
    }
    
    # Add appointment if exists
    if note.appointment_id:
        appointment = Appointment.query.get(note.appointment_id)
        note_data["appointment"] = {
            "id": appointment.uuid,
            "date": appointment.date.strftime('%Y-%m-%d')
        }
    
    # Add tags
    for note_tag in note.tags:
        tag = Tag.query.get(note_tag.tag_id)
        note_data["tags"].append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color
        })
    
    return jsonify(note_data), 200

@notes_bp.route('/notes', methods=['POST'])
@jwt_required()
def create_note():
    """
    Create a new note
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
    
    if 'content' not in data:
        return jsonify({"msg": "Missing content"}), 400
    
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
    
    # Create new note
    new_note = Note(
        uuid=str(uuid.uuid4()),
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_id=appointment_id,
        title=data.get('title', ''),
        content=data['content'],
        category=data.get('category')
    )
    
    # Add to database
    if not add_to_db(new_note):
        return jsonify({"msg": "Error creating note"}), 500
    
    # Add tags if provided
    if 'tags' in data and isinstance(data['tags'], list):
        for tag_data in data['tags']:
            # Find or create tag
            tag = None
            
            if isinstance(tag_data, dict) and 'name' in tag_data:
                tag_name = tag_data['name']
                tag = Tag.query.filter(Tag.name.ilike(tag_name)).first()
                
                if not tag:
                    # Create new tag
                    tag = Tag(
                        name=tag_name,
                        color=tag_data.get('color', '#cccccc')
                    )
                    db.session.add(tag)
                    db.session.flush()
            elif isinstance(tag_data, int):
                # Tag ID provided
                tag = Tag.query.get(tag_data)
            
            if tag:
                # Create note tag association
                note_tag = NoteTag(
                    note_id=new_note.id,
                    tag_id=tag.id
                )
                db.session.add(note_tag)
    
    # Commit all changes
    if commit_changes():
        return jsonify({
            "msg": "Note created successfully",
            "note": {
                "id": new_note.uuid,
                "title": new_note.title
            }
        }), 201
    
    return jsonify({"msg": "Error creating note"}), 500

@notes_bp.route('/notes/<string:note_uuid>', methods=['PUT'])
@jwt_required()
def update_note(note_uuid):
    """
    Update an existing note
    """
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    note = Note.query.filter_by(uuid=note_uuid, doctor_id=doctor.id).first()
    
    if not note:
        return jsonify({"msg": "Note not found"}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'title' in data:
        note.title = data['title']
    
    if 'content' in data:
        note.content = data['content']
    
    if 'category' in data:
        note.category = data['category']
    
    # Update tags if provided
    if 'tags' in data and isinstance(data['tags'], list):
        # Remove existing tags
        NoteTag.query.filter_by(note_id=note.id).delete()
        
        # Add new tags
        for tag_data in data['tags']:
            # Find or create tag
            tag = None
            
            if isinstance(tag_data, dict) and 'name' in tag_data:
                tag_name = tag_data['name']
                tag = Tag.query.filter(Tag.name.ilike(tag_name)).first()
                
                if not tag:
                    # Create new tag
                    tag = Tag(
                        name=tag_name,
                        color=tag_data.get('color', '#cccccc')
                    )
                    db.session.add(tag)
                    db.session.flush()
            elif isinstance(tag_data, int):
                # Tag ID provided
                tag = Tag.query.get(tag_data)
            
            if tag:
                # Create note tag association
                note_tag = NoteTag(
                    note_id=note.id,
                    tag_id=tag.id
                )
                db.session.add(note_tag)
    
    # Commit changes
    if commit_changes():
        return jsonify({
            "msg": "Note updated successfully",
            "note": {
                "id": note.uuid,
                "title": note.title
            }
        }), 200
    
    return jsonify({"msg": "Error updating note"}), 500

@notes_bp.route('/notes/<string:note_uuid>', methods=['DELETE'])
@jwt_required()
def delete_note(note_uuid):
    """
    Delete a note
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    note = Note.query.filter_by(uuid=note_uuid, doctor_id=doctor.id).first()
    
    if not note:
        return jsonify({"msg": "Note not found"}), 404
    
    # Delete note (cascade will delete note_tags)
    if delete_from_db(note):
        return jsonify({"msg": "Note deleted successfully"}), 200
    
    return jsonify({"msg": "Error deleting note"}), 500

@notes_bp.route('/tags', methods=['GET'])
@jwt_required()
def get_tags():
    """
    Get all tags
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get all tags
    tags = Tag.query.order_by(Tag.name).all()
    
    # Format results
    tag_list = []
    for tag in tags:
        tag_list.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color
        })
    
    return jsonify({"tags": tag_list}), 200

@notes_bp.route('/tags', methods=['POST'])
@jwt_required()
def create_tag():
    """
    Create a new tag
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
    
    # Check if tag already exists
    existing_tag = Tag.query.filter(Tag.name.ilike(data['name'])).first()
    if existing_tag:
        return jsonify({"msg": "Tag with this name already exists"}), 409
    
    # Create new tag
    new_tag = Tag(
        name=data['name'],
        color=data.get('color', '#cccccc')
    )
    
    # Add to database
    if add_to_db(new_tag):
        return jsonify({
            "msg": "Tag created successfully",
            "tag": {
                "id": new_tag.id,
                "name": new_tag.name,
                "color": new_tag.color
            }
        }), 201
    
    return jsonify({"msg": "Error creating tag"}), 500