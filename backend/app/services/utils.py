import os
import uuid
import csv
import json
from datetime import datetime, date, time
from flask import current_app
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, date, time, and UUID objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

def save_uploaded_file(file, base_dir=None):
    """Save an uploaded file and return the path"""
    if file.filename == '':
        return None
    
    if base_dir is None:
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    # Create directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Secure the filename and generate a unique name
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(base_dir, unique_filename)
    
    try:
        file.save(file_path)
        return file_path
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return None

def generate_csv(data, headers):
    """Generate CSV from data"""
    if not data:
        return None
    
    try:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for row in data:
                writer.writerow(row)
                
        return file_path
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        return None

def format_phone_number(phone):
    """Format a phone number consistently"""
    if not phone:
        return None
        
    # Remove all non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Apply formatting based on length
    if len(digits) == 10:  # US number without country code
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':  # US number with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # Simple formatting for international numbers
        if len(digits) > 10:
            return f"+{digits[:len(digits)-10]} {digits[-10:-7]} {digits[-7:-4]} {digits[-4:]}"
        else:
            return phone  # Return original if we can't determine format

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
        
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def log_activity(doctor_id, action, entity_type=None, entity_id=None, details=None, request=None):
    """Log user activity"""
    from app.models.models import ActivityLog
    from app import db
    
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string if request.user_agent else None
        
        activity = ActivityLog(
            doctor_id=doctor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(activity)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        db.session.rollback()
        return False

def is_valid_uuid(val):
    """Check if a string is a valid UUID"""
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError):
        return False

def paginate_query(query, page, per_page):
    """Paginate a query with error handling"""
    try:
        page = max(1, int(page))
        per_page = min(100, max(1, int(per_page)))  # Limit to 100 items max
        return query.paginate(page=page, per_page=per_page, error_out=False)
    except (ValueError, TypeError):
        return query.paginate(page=1, per_page=20, error_out=False)

def sanitize_search(search_term):
    """Sanitize a search term for SQL LIKE queries"""
    if not search_term:
        return '%'
        
    # Escape SQL LIKE special characters
    for char in ['\\', '%', '_']:
        search_term = search_term.replace(char, f'\\{char}')
        
    return f'%{search_term}%'