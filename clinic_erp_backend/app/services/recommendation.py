from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_
from app.models.models import Patient, Diagnosis, PatientDiagnosis, Medicine, PrescriptionItem, Prescription, Doctor

class RecommendationService:
    """
    Service for providing intelligent recommendations based on historical data
    """
    
    @staticmethod
    def get_similar_patients(patient_id, doctor_id, limit=5):
        """
        Find similar patients based on diagnosis history
        """
        # Get the patient's diagnoses
        patient_diagnoses = PatientDiagnosis.query.join(
            Patient, Patient.id == PatientDiagnosis.patient_id
        ).filter(
            PatientDiagnosis.patient_id == patient_id,
            Patient.doctor_id == doctor_id
        ).all()
        
        if not patient_diagnoses:
            return []
        
        # Extract diagnosis IDs
        diagnosis_ids = [pd.diagnosis_id for pd in patient_diagnoses]
        
        # Find patients with similar diagnoses
        similar_patients = Patient.query.join(
            PatientDiagnosis, Patient.id == PatientDiagnosis.patient_id
        ).filter(
            Patient.id != patient_id,
            Patient.doctor_id == doctor_id,
            PatientDiagnosis.diagnosis_id.in_(diagnosis_ids)
        ).group_by(
            Patient.id
        ).order_by(
            func.count(PatientDiagnosis.id).desc()
        ).limit(limit).all()
        
        return similar_patients
    
    @staticmethod
    def get_medicine_recommendations(diagnosis_id, limit=5):
        """
        Recommend medicines based on diagnosis
        """
        # Find most commonly prescribed medicines for this diagnosis
        recommended_medicines = Medicine.query.join(
            PrescriptionItem, Medicine.id == PrescriptionItem.medicine_id
        ).join(
            Prescription, Prescription.id == PrescriptionItem.prescription_id
        ).join(
            PatientDiagnosis, PatientDiagnosis.prescription_id == Prescription.id
        ).filter(
            PatientDiagnosis.diagnosis_id == diagnosis_id
        ).group_by(
            Medicine.id
        ).order_by(
            func.count(PrescriptionItem.id).desc()
        ).limit(limit).all()
        
        return recommended_medicines
    
    @staticmethod
    def get_diagnosis_suggestions(symptoms, limit=5):
        """
        Suggest diagnoses based on symptoms
        """
        # Simple keyword-based matching for symptoms in diagnosis descriptions
        if not symptoms:
            return []
            
        # Create search conditions for each symptom
        search_conditions = []
        for symptom in symptoms:
            search_term = f"%{symptom}%"
            search_conditions.append(or_(
                Diagnosis.name.ilike(search_term),
                Diagnosis.description.ilike(search_term)
            ))
            
        # Find diagnoses that match any of the symptoms
        suggested_diagnoses = Diagnosis.query.filter(
            or_(*search_conditions)
        ).order_by(
            Diagnosis.name
        ).limit(limit).all()
        
        return suggested_diagnoses
    
    @staticmethod
    def predict_appointment_duration(patient_id, doctor_id):
        """
        Predict appointment duration based on patient history
        """
        from app.models.models import Appointment
        
        # Get average appointment duration for this patient
        patient_appointments = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id,
            Appointment.status == 'completed'
        ).all()
        
        if patient_appointments:
            total_minutes = 0
            count = 0
            
            for appt in patient_appointments:
                # Calculate duration in minutes
                start = datetime.combine(datetime.today(), appt.start_time)
                end = datetime.combine(datetime.today(), appt.end_time)
                duration = (end - start).total_seconds() / 60
                
                total_minutes += duration
                count += 1
            
            if count > 0:
                return round(total_minutes / count)
        
        # If no patient history, return clinic average
        clinic_average = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == 'completed'
        ).limit(100).all()
        
        if clinic_average:
            total_minutes = 0
            count = 0
            
            for appt in clinic_average:
                start = datetime.combine(datetime.today(), appt.start_time)
                end = datetime.combine(datetime.today(), appt.end_time)
                duration = (end - start).total_seconds() / 60
                
                total_minutes += duration
                count += 1
            
            if count > 0:
                return round(total_minutes / count)
        
        # Default duration if no data available
        return 30
    
    @staticmethod
    def get_followup_recommendation(patient_id, diagnosis_id=None):
        """
        Recommend follow-up appointment time based on diagnosis and patient history
        """
        from app.models.models import Appointment
        
        # Default follow-up times by diagnosis type (in days)
        followup_defaults = {
            'acute': 7,       # Acute conditions
            'chronic': 30,    # Chronic conditions
            'preventive': 90, # Preventive care
            'default': 14     # Default if no match
        }
        
        if diagnosis_id:
            # Get diagnosis category
            diagnosis = Diagnosis.query.get(diagnosis_id)
            if diagnosis and diagnosis.category:
                days = followup_defaults.get(diagnosis.category.lower(), followup_defaults['default'])
                return datetime.now() + timedelta(days=days)
        
        # If no specific diagnosis, use patient's average follow-up time
        follow_ups = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'scheduled'
        ).order_by(
            Appointment.date.desc()
        ).limit(5).all()
        
        if follow_ups and len(follow_ups) >= 2:
            # Calculate average time between appointments
            intervals = []
            for i in range(1, len(follow_ups)):
                interval = (follow_ups[i-1].date - follow_ups[i].date).days
                if interval > 0:
                    intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                return datetime.now() + timedelta(days=round(avg_interval))
        
        # Default to 14 days if no better data
        return datetime.now() + timedelta(days=followup_defaults['default'])
    
    @staticmethod
    def get_frequent_medicines(doctor_id, limit=10):
        """
        Get most frequently prescribed medicines by this doctor
        """
        frequent_medicines = Medicine.query.join(
            PrescriptionItem, Medicine.id == PrescriptionItem.medicine_id
        ).join(
            Prescription, Prescription.id == PrescriptionItem.prescription_id
        ).filter(
            Prescription.doctor_id == doctor_id
        ).group_by(
            Medicine.id
        ).order_by(
            func.count(PrescriptionItem.id).desc()
        ).limit(limit).all()
        
        return frequent_medicines
    
    @staticmethod
    def get_frequent_diagnoses(doctor_id, limit=10):
        """
        Get most frequently used diagnoses by this doctor
        """
        frequent_diagnoses = Diagnosis.query.join(
            PatientDiagnosis, Diagnosis.id == PatientDiagnosis.diagnosis_id
        ).join(
            Patient, Patient.id == PatientDiagnosis.patient_id
        ).filter(
            Patient.doctor_id == doctor_id
        ).group_by(
            Diagnosis.id
        ).order_by(
            func.count(PatientDiagnosis.id).desc()
        ).limit(limit).all()
        
        return frequent_diagnoses
    
    @staticmethod
    def get_dosage_recommendation(medicine_id, patient_id=None):
        """
        Recommend dosage based on common prescriptions
        """
        # Get most common dosage for this medicine
        common_dosage = PrescriptionItem.query.filter(
            PrescriptionItem.medicine_id == medicine_id
        ).group_by(
            PrescriptionItem.dosage
        ).order_by(
            func.count(PrescriptionItem.id).desc()
        ).first()
        
        if common_dosage:
            return {
                "dosage": common_dosage.dosage,
                "frequency": common_dosage.frequency,
                "duration": common_dosage.duration,
                "instructions": common_dosage.instructions
            }
        
        # If no data available, return None
        return None