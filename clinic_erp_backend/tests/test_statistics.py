import json
import pytest
from datetime import date, timedelta

def test_get_overview_statistics(client, auth_headers, patient, appointment, prescription, medicine):
    """Test getting overview statistics"""
    response = client.get('/api/stats/overview', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'patients' in data
    assert 'appointments' in data
    assert 'today' in data['appointments']
    assert 'upcoming' in data['appointments']
    
    # Verify the counts match what we expect
    assert data['patients']['total'] >= 1  # At least our test patient
    assert data['appointments']['total'] >= 1  # At least our test appointment

def test_get_appointment_statistics(client, auth_headers, appointment):
    """Test getting appointment statistics"""
    # Create additional appointments with different statuses
    today = date.today()
    
    # Get appointment statistics for this month
    first_day = date(today.year, today.month, 1)
    last_day = date(today.year, today.month + 1, 1) - timedelta(days=1) if today.month < 12 else date(today.year + 1, 1, 1) - timedelta(days=1)
    
    response = client.get(
        f'/api/stats/appointments?start_date={first_day.strftime("%Y-%m-%d")}&end_date={last_day.strftime("%Y-%m-%d")}',
        headers=auth_headers
    )
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'appointments' in data
    assert 'by_status' in data
    assert 'by_day' in data
    
    # Verify our appointment is included in the stats
    assert data['appointments']['total'] >= 1

def test_get_patient_statistics(client, auth_headers, patient):
    """Test getting patient statistics"""
    response = client.get('/api/stats/patients', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'patients' in data
    assert 'by_gender' in data
    assert 'by_age_group' in data
    assert 'new_patients' in data
    
    # Verify our patient is included in the stats
    assert data['patients']['total'] >= 1
    
    # Test age distribution (assuming our test patient is 43 years old from DOB 1980-01-01)
    found_age_group = False
    for age_group in data['by_age_group']:
        if age_group['group'] == '41-50' and age_group['count'] >= 1:
            found_age_group = True
            break
    
    assert found_age_group, "Patient age group not found in statistics"

def test_get_prescription_statistics(client, auth_headers, prescription):
    """Test getting prescription statistics"""
    response = client.get('/api/stats/prescriptions', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'prescriptions' in data
    assert 'recent' in data
    assert 'top_medicines' in data
    
    # Verify our prescription is included in the stats
    assert data['prescriptions']['total'] >= 1