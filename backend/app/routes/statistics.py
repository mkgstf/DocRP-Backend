from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Doctor, Patient, Appointment, Prescription, PrescriptionItem, Medicine, Diagnosis, PatientDiagnosis
from app.extensions import db
from sqlalchemy import func, extract, cast, Integer, case, desc
from datetime import datetime, date, timedelta

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/stats/overview', methods=['GET'])
@jwt_required()
def get_overview_statistics():
    """
    Get overview statistics for the current doctor
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Today's date
    today = date.today()
    
    # Get patient statistics
    total_patients = Patient.query.filter_by(doctor_id=doctor.id).count()
    new_patients_this_month = Patient.query.filter(
        Patient.doctor_id == doctor.id,
        extract('month', Patient.created_at) == today.month,
        extract('year', Patient.created_at) == today.year
    ).count()
    
    # Get appointment statistics
    total_appointments = Appointment.query.filter_by(doctor_id=doctor.id).count()
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date == today
    ).count()
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date > today,
        Appointment.date <= today + timedelta(days=7)  # Next 7 days
    ).count()
    completed_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'completed'
    ).count()
    
    # Get prescription statistics
    total_prescriptions = Prescription.query.filter_by(doctor_id=doctor.id).count()
    prescriptions_this_month = Prescription.query.filter(
        Prescription.doctor_id == doctor.id,
        extract('month', Prescription.issue_date) == today.month,
        extract('year', Prescription.issue_date) == today.year
    ).count()
    
    # Get diagnosis statistics
    patient_diagnoses = db.session.query(PatientDiagnosis.diagnosis_id, func.count(PatientDiagnosis.id).label('count')) \
        .join(Patient, PatientDiagnosis.patient_id == Patient.id) \
        .filter(Patient.doctor_id == doctor.id) \
        .group_by(PatientDiagnosis.diagnosis_id) \
        .order_by(desc('count')) \
        .limit(5) \
        .all()
    
    top_diagnoses = []
    for diag_id, count in patient_diagnoses:
        diagnosis = Diagnosis.query.get(diag_id)
        top_diagnoses.append({
            "name": diagnosis.name,
            "count": count
        })
    
    return jsonify({
        "patients": {
            "total": total_patients,
            "new_this_month": new_patients_this_month
        },
        "appointments": {
            "total": total_appointments,
            "today": today_appointments,
            "upcoming": upcoming_appointments,
            "completed": completed_appointments
        },
        "prescriptions": {
            "total": total_prescriptions,
            "this_month": prescriptions_this_month
        },
        "top_diagnoses": top_diagnoses
    }), 200

@statistics_bp.route('/stats/appointments', methods=['GET'])
@jwt_required()
def get_appointment_statistics():
    """
    Get detailed appointment statistics
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters for date range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to current month if not specified
    today = date.today()
    if not start_date_str:
        start_date = date(today.year, today.month, 1)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if not end_date_str:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    # Get total appointments in date range
    total_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= start_date,
        Appointment.date <= end_date
    ).count()
    
    # Get appointments by status
    status_counts = db.session.query(
        Appointment.status, func.count(Appointment.id)
    ).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= start_date,
        Appointment.date <= end_date
    ).group_by(Appointment.status).all()
    
    by_status = [{"status": status, "count": count} for status, count in status_counts]
    
    # Get appointments by day
    day_counts = db.session.query(
        Appointment.date, func.count(Appointment.id)
    ).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= start_date,
        Appointment.date <= end_date
    ).group_by(Appointment.date).all()
    
    by_day = [{"date": day.strftime('%Y-%m-%d'), "count": count} for day, count in day_counts]
    
    return jsonify({
        "appointments": {
            "total": total_appointments,
            "date_range": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            }
        },
        "by_status": by_status,
        "by_day": by_day
    }), 200

@statistics_bp.route('/stats/patients', methods=['GET'])
@jwt_required()
def get_patient_statistics():
    """
    Get detailed patient statistics
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get total patients
    total_patients = Patient.query.filter_by(doctor_id=doctor.id).count()
    
    # Get patients by gender
    gender_counts = db.session.query(
        Patient.gender, func.count(Patient.id)
    ).filter(
        Patient.doctor_id == doctor.id
    ).group_by(Patient.gender).all()
    
    by_gender = [{"gender": gender or "Not specified", "count": count} for gender, count in gender_counts]
    
    # Get patients by age group
    today = date.today()
    age_groups = [
        {'name': '0-10', 'min': 0, 'max': 10},
        {'name': '11-20', 'min': 11, 'max': 20},
        {'name': '21-30', 'min': 21, 'max': 30},
        {'name': '31-40', 'min': 31, 'max': 40},
        {'name': '41-50', 'min': 41, 'max': 50},
        {'name': '51-60', 'min': 51, 'max': 60},
        {'name': '61-70', 'min': 61, 'max': 70},
        {'name': '71+', 'min': 71, 'max': 200}
    ]
    
    by_age_group = []
    for group in age_groups:
        min_date = date(today.year - group['max'] - 1, today.month, today.day) + timedelta(days=1)
        max_date = date(today.year - group['min'], today.month, today.day)
        
        count = Patient.query.filter(
            Patient.doctor_id == doctor.id,
            Patient.date_of_birth >= min_date,
            Patient.date_of_birth <= max_date
        ).count()
        
        if count > 0:
            by_age_group.append({"group": group['name'], "count": count})
    
    # Get new patients by month for the last 12 months
    new_patients = []
    for i in range(12):
        month = (today.month - i - 1) % 12 + 1
        year = today.year - ((i + (today.month - 1)) // 12)
        
        count = Patient.query.filter(
            Patient.doctor_id == doctor.id,
            extract('month', Patient.created_at) == month,
            extract('year', Patient.created_at) == year
        ).count()
        
        new_patients.append({
            "month": datetime(year, month, 1).strftime('%Y-%m'),
            "count": count
        })
    
    new_patients.reverse()  # Show oldest to newest
    
    return jsonify({
        "patients": {
            "total": total_patients
        },
        "by_gender": by_gender,
        "by_age_group": by_age_group,
        "new_patients": new_patients
    }), 200

@statistics_bp.route('/stats/prescriptions', methods=['GET'])
@jwt_required()
def get_prescription_statistics():
    """
    Get detailed prescription statistics
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get total prescriptions
    total_prescriptions = Prescription.query.filter_by(doctor_id=doctor.id).count()
    
    # Get recent prescriptions (last 30 days)
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    
    recent_count = Prescription.query.filter(
        Prescription.doctor_id == doctor.id,
        Prescription.issue_date >= thirty_days_ago
    ).count()
    
    # Get prescriptions by month for the last 12 months
    prescriptions_by_month = []
    for i in range(12):
        month = (today.month - i - 1) % 12 + 1
        year = today.year - ((i + (today.month - 1)) // 12)
        
        count = Prescription.query.filter(
            Prescription.doctor_id == doctor.id,
            extract('month', Prescription.issue_date) == month,
            extract('year', Prescription.issue_date) == year
        ).count()
        
        prescriptions_by_month.append({
            "month": datetime(year, month, 1).strftime('%Y-%m'),
            "count": count
        })
    
    prescriptions_by_month.reverse()  # Show oldest to newest
    
    # Get top prescribed medicines
    top_medicines_query = db.session.query(
        Medicine.name, func.count(PrescriptionItem.id).label('count')
    ).join(
        PrescriptionItem, Medicine.id == PrescriptionItem.medicine_id
    ).join(
        Prescription, PrescriptionItem.prescription_id == Prescription.id
    ).filter(
        Prescription.doctor_id == doctor.id
    ).group_by(
        Medicine.name
    ).order_by(
        desc('count')
    ).limit(10).all()
    
    top_medicines = [{"name": name, "count": count} for name, count in top_medicines_query]
    
    return jsonify({
        "prescriptions": {
            "total": total_prescriptions,
            "recent": recent_count
        },
        "by_month": prescriptions_by_month,
        "top_medicines": top_medicines
    }), 200