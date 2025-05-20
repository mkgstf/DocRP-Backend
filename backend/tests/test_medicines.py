import json
import pytest

def test_get_medicines(client, auth_headers, medicine):
    """Test getting list of medicines"""
    response = client.get('/api/medicines', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'medicines' in data
    assert len(data['medicines']) > 0
    assert data['pagination']['total'] > 0

def test_get_medicine(client, auth_headers, medicine):
    """Test getting a specific medicine"""
    response = client.get(f'/api/medicines/{medicine.uuid}', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['id'] == medicine.uuid
    assert data['name'] == 'Test Medicine'
    assert data['dosage_form'] == 'tablet'
    assert data['strength'] == '500mg'

def test_create_medicine(client, auth_headers):
    """Test creating a new medicine"""
    response = client.post('/api/medicines', json={
        'name': 'New Medicine',
        'description': 'A new test medicine',
        'dosage_form': 'capsule',
        'strength': '250mg',
        'manufacturer': 'Test Pharma Inc.'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert 'medicine' in data
    assert data['medicine']['name'] == 'New Medicine'

def test_update_medicine(client, auth_headers, medicine):
    """Test updating a medicine"""
    response = client.put(f'/api/medicines/{medicine.uuid}', json={
        'description': 'Updated description',
        'manufacturer': 'Updated Pharma'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'medicine' in data
    
    # Verify medicine was updated
    check_response = client.get(f'/api/medicines/{medicine.uuid}', headers=auth_headers)
    check_data = json.loads(check_response.data)
    assert check_data['description'] == 'Updated description'
    assert check_data['manufacturer'] == 'Updated Pharma'

def test_delete_medicine(client, auth_headers, medicine):
    """Test deleting a medicine"""
    # First ensure the medicine has no prescription items
    response = client.delete(f'/api/medicines/{medicine.uuid}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify medicine is deleted
    check_response = client.get(f'/api/medicines/{medicine.uuid}', headers=auth_headers)
    assert check_response.status_code == 404

def test_search_medicines(client, auth_headers, medicine):
    """Test searching medicines for autocomplete"""
    # Add another medicine for search test
    client.post('/api/medicines', json={
        'name': 'Search Test Medicine',
        'dosage_form': 'syrup'
    }, headers=auth_headers)
    
    response = client.get('/api/medicines/search?q=Test', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'results' in data
    assert len(data['results']) >= 1
    
    # Check if our original medicine is in results
    found = False
    for result in data['results']:
        if result['id'] == medicine.uuid:
            found = True
            break
    
    assert found, "Original medicine not found in search results"