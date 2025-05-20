import json
import pytest

def test_get_diagnoses(client, auth_headers, diagnosis):
    """Test getting list of diagnoses"""
    response = client.get('/api/diagnoses', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'diagnoses' in data
    assert len(data['diagnoses']) > 0
    assert data['pagination']['total'] > 0

def test_get_diagnosis(client, auth_headers, diagnosis):
    """Test getting a specific diagnosis"""
    response = client.get(f'/api/diagnoses/{diagnosis.uuid}', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['id'] == diagnosis.uuid
    assert data['name'] == 'Test Diagnosis'
    assert data['icd_code'] == 'A00.0'

def test_create_diagnosis(client, auth_headers):
    """Test creating a new diagnosis"""
    response = client.post('/api/diagnoses', json={
        'name': 'New Diagnosis',
        'description': 'A new test diagnosis',
        'icd_code': 'B99.9',
        'category': 'Test Category'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert 'diagnosis' in data
    assert data['diagnosis']['name'] == 'New Diagnosis'

def test_update_diagnosis(client, auth_headers, diagnosis):
    """Test updating a diagnosis"""
    response = client.put(f'/api/diagnoses/{diagnosis.uuid}', json={
        'description': 'Updated description',
        'category': 'Updated Category'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    
    # Verify diagnosis was updated
    check_response = client.get(f'/api/diagnoses/{diagnosis.uuid}', headers=auth_headers)
    check_data = json.loads(check_response.data)
    assert check_data['description'] == 'Updated description'
    assert check_data['category'] == 'Updated Category'

def test_delete_diagnosis(client, auth_headers, diagnosis):
    """Test deleting a diagnosis"""
    response = client.delete(f'/api/diagnoses/{diagnosis.uuid}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify diagnosis is deleted
    check_response = client.get(f'/api/diagnoses/{diagnosis.uuid}', headers=auth_headers)
    assert check_response.status_code == 404

def test_search_diagnoses(client, auth_headers, diagnosis):
    """Test searching diagnoses for autocomplete"""
    # Add another diagnosis for search test
    client.post('/api/diagnoses', json={
        'name': 'Search Test Diagnosis',
        'icd_code': 'C00.1'
    }, headers=auth_headers)
    
    response = client.get('/api/diagnoses/search?q=Test', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'results' in data
    assert len(data['results']) >= 1

def test_patient_diagnoses(client, auth_headers, patient, diagnosis):
    """Test adding and retrieving patient diagnoses"""
    # Add diagnosis to patient
    response = client.post(f'/api/patients/{patient.uuid}/diagnoses', json={
        'diagnosis_id': diagnosis.uuid,
        'status': 'active',
        'notes': 'Test diagnosis notes'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert 'patient_diagnosis' in data
    patient_diagnosis_id = data['patient_diagnosis']['id']
    
    # Get patient diagnoses
    response = client.get(f'/api/patients/{patient.uuid}/diagnoses', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'diagnoses' in data
    assert len(data['diagnoses']) > 0
    
    # Update patient diagnosis
    response = client.put(f'/api/patients/diagnoses/{patient_diagnosis_id}', json={
        'status': 'resolved',
        'notes': 'Updated notes'
    }, headers=auth_headers)
    
    assert response.status_code == 200
    
    # Delete patient diagnosis
    response = client.delete(f'/api/patients/diagnoses/{patient_diagnosis_id}', headers=auth_headers)
    
    assert response.status_code == 200