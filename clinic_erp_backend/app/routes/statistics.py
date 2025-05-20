from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Doctor, Patient, Appointment, Prescription, PatientDiagnosis, Diagnosis
from app import db
from sqlalchemy import func, extract, desc
from datetime import datetime, timedelta, date
import calendar

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/stats/overview', methods=['GET'])
@jwt_required()
def get_overview_stats():
    """
    Get overview statistics for the current doctor
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Count total patients
    total_patients = Patient.query.filter_by(doctor_id=doctor.id).count()
    
    # Count new patients in the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_patients = Patient.query.filter_by(doctor_id=doctor.id).filter(
        Patient.created_at >= thirty_days_ago
    ).count()
    
    # Count upcoming appointments
    today = date.today()
    upcoming_appointments = Appointment.query.filter_by(doctor_id=doctor.id).filter(
        Appointment.date >= today,
        Appointment.status == 'scheduled'
    ).count()
    
    # Count today's appointments
    today_appointments = Appointment.query.filter_by(doctor_id=doctor.id).filter(
        Appointment.date == today
    ).count()
    
    # Count total prescriptions
    total_prescriptions = Prescription.query.filter_by(doctor_id=doctor.id).count()
    
    # Return formatted statistics
    return jsonify({
        "total_patients": total_patients,
        "new_patients_30d": new_patients,
        "upcoming_appointments": upcoming_appointments,
        "today_appointments": today_appointments,
        "total_prescriptions": total_prescriptions
    }), 200

@statistics_bp.route('/stats/appointments', methods=['GET'])
@jwt_required()
def get_appointment_stats():
    """
    Get appointment statistics for the current doctor
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    period = request.args.get('period', 'month')  # day, week, month, year
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Parse date range
    today = date.today()
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    else:
        # Default start date based on period
        if period == 'day':
            start = today
        elif period == 'week':
            start = today - timedelta(days=7)
        elif period == 'month':
            start = today.replace(day=1)
        else:  # year
            start = today.replace(month=1, day=1)
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    else:
        end = today
    
    # Count appointments by status
    status_counts = db.session.query(
        Appointment.status, func.count(Appointment.id)
    ).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date.between(start, end)
    ).group_by(Appointment.status).all()
    
    # Format status counts
    status_stats = {}
    for status, count in status_counts:
        status_stats[status] = count
    
    # Count appointments by day
    if period == 'day':
        time_series = db.session.query(
            func.date_trunc('hour', func.concat(Appointment.date, ' ', Appointment.start_time).cast(db.DateTime)).label('hour'),
            func.count(Appointment.id)
        ).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date == today
        ).group_by('hour').order_by('hour').all()
        
        # Format time series data
        time_data = {}
        for hour, count in time_series:
            time_data[hour.strftime('%H:00')] = count
    else:
        # Count by day for other periods
        time_series = db.session.query(
            Appointment.date, func.count(Appointment.id)
        ).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date.between(start, end)
        ).group_by(Appointment.date).order_by(Appointment.date).all()
        
        # Format time series data
        time_data = {}
        for day, count in time_series:
            time_data[day.strftime('%Y-%m-%d')] = count
    
    # Return formatted statistics
    return jsonify({
        "period": period,
        "start_date": start.strftime('%Y-%m-%d'),
        "end_date": end.strftime('%Y-%m-%d'),
        "by_status": status_stats,
        "time_series": time_data
    }), 200

@statistics_bp.route('/stats/diagnoses', methods=['GET'])
@jwt_required()
def get_diagnosis_stats():
    """
    Get diagnosis statistics for the current doctor
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    limit = request.args.get('limit', 10, type=int)
    
    # Get patients for this doctor
    patient_ids = [p.id for p in Patient.query.filter_by(doctor_id=doctor.id).all()]
    
    if not patient_ids:
        return jsonify({
            "top_diagnoses": [],
            "by_status": {},
            "by_month": {}
        }), 200
    
    # Get top diagnoses
    top_diagnoses = db.session.query(
        Diagnosis.name, func.count(PatientDiagnosis.id).label('count')
    ).join(
        PatientDiagnosis, PatientDiagnosis.diagnosis_id == Diagnosis.id
    ).filter(
        PatientDiagnosis.patient_id.in_(patient_ids)
    ).group_by(Diagnosis.name).order_by(desc('count')).limit(limit).all()
    
    # Format top diagnoses
    top_diagnosis_data = {}
    for name, count in top_diagnoses:
        top_diagnosis_data[name] = count
    
    # Get diagnoses by status
    status_counts = db.session.query(
        PatientDiagnosis.status, func.count(PatientDiagnosis.id)
    ).filter(
        PatientDiagnosis.patient_id.in_(patient_ids)
    ).group_by(PatientDiagnosis.status).all()
    
    # Format status counts
    status_data = {}
    for status, count in status_counts:
        status_data[status] = count
    
    # Get diagnoses by month (last 12 months)
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    month_data = {}
    for i in range(12):
        month = ((current_month - i - 1) % 12) + 1
        year = current_year - ((current_month - month) // 12)
        
        count = db.session.query(func.count(PatientDiagnosis.id)).filter(
            PatientDiagnosis.patient_id.in_(patient_ids),
            extract('month', PatientDiagnosis.date_diagnosed) == month,
            extract('year', PatientDiagnosis.date_diagnosed) == year
        ).scalar()
        
        month_name = calendar.month_name[month]
        month_data[f"{month_name} {year}"] = count or 0
    
    # Return formatted statistics
    return jsonify({
        "top_diagnoses": top_diagnosis_data,
        "by_status": status_data,
        "by_month": month_data
    }), 200

@statistics_bp.route('/stats/prescriptions', methods=['GET'])
@jwt_required()
def get_prescription_stats():
    """
    Get prescription statistics for the current doctor
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    period = request.args.get('period', 'year')  # month, year, all
    
    # Set date range based on period
    today = date.today()
    
    if period == 'month':
        start_date = today.replace(day=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # 'all'
        start_date = date(2000, 1, 1)  # arbitrary past date
    
    # Get total prescriptions in period
    total_prescriptions = Prescription.query.filter(
        Prescription.doctor_id == doctor.id,
        Prescription.issue_date >= start_date
    ).count()
    
    # Get prescriptions by month
    if period == 'year' or period == 'all':
        month_counts = db.session.query(
            extract('month', Prescription.issue_date).label('month'),
            extract('year', Prescription.issue_date).label('year'),
            func.count(Prescription.id).label('count')
        ).filter(
            Prescription.doctor_id == doctor.id,
            Prescription.issue_date >= start_date
        ).group_by('month', 'year').order_by('year', 'month').all()
        
        # Format month data
        months_data = {}
        for month_num, year, count in month_counts:
            month_name = calendar.month_name[int(month_num)]
            months_data[f"{month_name} {int(year)}"] = count
    else:
        # Get prescriptions by day for current month
        day_counts = db.session.query(
            Prescription.issue_date,
            func.count(Prescription.id).label('count')
        ).filter(
            Prescription.doctor_id == doctor.id,
            Prescription.issue_date >= start_date
        ).group_by(Prescription.issue_date).order_by(Prescription.issue_date).all()
        
        # Format day data
        months_data = {}
        for day, count in day_counts:
            months_data[day.strftime('%Y-%m-%d')] = count
    
    # Get top prescribed medicines
    top_medicines = db.session.query(
        func.count(PrescriptionItem.id).label('count')
    ).join(
        Prescription, Prescription.id == PrescriptionItem.prescription_id
    ).filter(
        Prescription.doctor_id == doctor.id,
        Prescription.issue_date >= start_date
    ).scalar() or 0
    
    # Return formatted statistics
    return jsonify({
        "period": period,
        "total_prescriptions": total_prescriptions,
        "total_medicine_items": top_medicines,
        "time_series": months_data
    }), 200

@statistics_bp.route('/stats/export', methods=['GET'])
@jwt_required()
def export_statistics():
    """
    Export statistics as CSV (placeholder)
    In a real implementation, this would generate a CSV and return it
    """
    current_user_uuid = get_jwt_identity()
    doctor = Doctor.query.filter_by(uuid=current_user_uuid).first()
    
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # Get query parameters
    report_type = request.args.get('type', 'appointments')  # appointments, diagnoses, prescriptions
    
    # This would be replaced with actual CSV generation
    return jsonify({
        "msg": "CSV export capability would be implemented here",
        "report_type": report_type
    }), 200