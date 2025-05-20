import json
import pytest
from datetime import date, datetime, timedelta

def test_get_appointments(client, auth_headers, appointment):
    """Test getting list of appointments"""
    response = client.get('/api/appointments', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'appointments' in data
    assert len(data['appointments']) > 0
    assert data['pagination']['total'] > 0

def test_get_appointment(client, auth_headers, appointment):
    """Test getting a specific appointment"""
    response = client.get(f'/api/appointments/{appointment.uuid}', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['id'] == appointment.uuid
    assert data['status'] == 'scheduled'
    assert data['reason'] == 'Test appointment'

def test_create_appointment(client, auth_headers, patient):
    """Test creating a new appointment"""
    tomorrow = date.today() + timedelta(days=1)
    response = client.post('/api/appointments', json={
        'patient_id': patient.uuid,
        'date': tomorrow.strftime('%Y-%m-%d'),
        'start_time': '09:00',
        'end_time': '09:30',
        'reason': 'Follow-up visit',
        'status': 'scheduled'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert 'appointment' in data
    assert data['appointment']['date'] == tomorrow.strftime('%Y-%m-%d')
    assert data['appointment']['start_time'] == '09:00'

def test_update_appointment(client, auth_headers, appointment):
    """Test updating an appointment"""
    response = client.put(f'/api/appointments/{appointment.uuid}', json={
        'status': 'completed',
        'notes': 'Patient was on time. Checkup completed.'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    
    # Verify appointment was updated
    check_response = client.get(f'/api/appointments/{appointment.uuid}', headers=auth_headers)
    check_data = json.loads(check_response.data)
    assert check_data['status'] == 'completed'

def test_delete_appointment(client, auth_headers, appointment):
    """Test deleting an appointment"""
    response = client.delete(f'/api/appointments/{appointment.uuid}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify appointment is deleted
    check_response = client.get(f'/api/appointments/{appointment.uuid}', headers=auth_headers)
    assert check_response.status_code == 404

def test_calendar(client, auth_headers, appointment):
    """Test getting calendar view of appointments"""
    today = date.today()
    start_date = today - timedelta(days=today.weekday())  # This week's Monday
    end_date = start_date + timedelta(days=6)  # Sunday
    
    response = client.get(
        f'/api/calendar?start_date={start_date.strftime("%Y-%m-%d")}&end_date={end_date.strftime("%Y-%m-%d")}',
        headers=auth_headers
    )
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'calendar' in data
    assert 'range' in data
    
    today_str = today.strftime('%Y-%m-%d')
    assert today_str in data['calendar']
    assert len(data['calendar'][today_str]) > 0