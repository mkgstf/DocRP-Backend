import json
import pytest
from datetime import date

def test_get_patients(client, auth_headers, patient):
    """Test getting list of patients"""
    response = client.get('/api/patients', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'patients' in data
    assert len(data['patients']) > 0
    assert data['pagination']['total'] > 0

def test_get_patient(client, auth_headers, patient):
    """Test getting a specific patient"""
    response = client.get(f'/api/patients/{patient.uuid}', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['id'] == patient.uuid
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'Patient'
    assert data['email'] == 'patient@test.com'

def test_create_patient(client, auth_headers):
    """Test creating a new patient"""
    response = client.post('/api/patients', json={
        'first_name': 'New',
        'last_name': 'Patient',
        'date_of_birth': '1990-05-15',
        'gender': 'female',
        'email': 'newpatient@test.com',
        'phone': '987-654-3210'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert 'patient' in data
    assert data['patient']['first_name'] == 'New'
    assert data['patient']['last_name'] == 'Patient'

def test_update_patient(client, auth_headers, patient):
    """Test updating a patient"""
    response = client.put(f'/api/patients/{patient.uuid}', json={
        'first_name': 'Updated',
        'medical_history': 'New medical history',
        'insurance_info': 'Insurance XYZ'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['patient']['first_name'] == 'Updated'

def test_delete_patient(client, auth_headers, patient):
    """Test deleting a patient"""
    response = client.delete(f'/api/patients/{patient.uuid}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify patient is deleted
    check_response = client.get(f'/api/patients/{patient.uuid}', headers=auth_headers)
    assert check_response.status_code == 404

def test_search_patients(client, auth_headers, patient):
    """Test searching for patients"""
    # Add a second patient to test search
    client.post('/api/patients', json={
        'first_name': 'Jane',
        'last_name': 'Doe',
        'date_of_birth': '1985-10-20',
        'gender': 'female',
        'email': 'jane@example.com'
    }, headers=auth_headers)
    
    # Search for original patient
    response = client.get('/api/patients/search?q=Test', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'results' in data
    assert len(data['results']) > 0
    
    # Test results contain our patient
    found = False
    for result in data['results']:
        if result['id'] == patient.uuid:
            found = True
            break
    
    assert found, "Original patient not found in search results"