import json
import pytest

def test_doctor_login(client, doctor):
    """Test doctor login endpoint"""
    response = client.post('/api/login', json={
        'username': 'testdoctor',
        'password': 'password123'
    })
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['doctor']['username'] == 'testdoctor'

def test_doctor_login_invalid(client, doctor):
    """Test doctor login with invalid credentials"""
    response = client.post('/api/login', json={
        'username': 'testdoctor',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401

def test_doctor_register(client):
    """Test doctor registration endpoint"""
    response = client.post('/api/register', json={
        'username': 'newdoctor',
        'email': 'newdoctor@test.com',
        'password': 'password123',
        'first_name': 'New',
        'last_name': 'Doctor',
        'specialization': 'Pediatrics'
    })
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert data['doctor']['username'] == 'newdoctor'
    assert data['doctor']['email'] == 'newdoctor@test.com'

def test_get_profile(client, auth_headers):
    """Test getting doctor profile"""
    response = client.get('/api/profile', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['username'] == 'testdoctor'
    assert data['email'] == 'doctor@test.com'

def test_update_profile(client, auth_headers):
    """Test updating doctor profile"""
    response = client.put('/api/profile', json={
        'first_name': 'Updated',
        'last_name': 'Doctor',
        'specialization': 'Cardiology'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['doctor']['first_name'] == 'Updated'
    assert data['doctor']['specialization'] == 'Cardiology'

def test_refresh_token(client, doctor):
    """Test refreshing access token"""
    # First login to get refresh token
    login_response = client.post('/api/login', json={
        'username': 'testdoctor',
        'password': 'password123'
    })
    login_data = json.loads(login_response.data)
    refresh_token = login_data['refresh_token']
    
    # Use refresh token to get new access token
    response = client.post('/api/refresh', headers={
        'Authorization': f'Bearer {refresh_token}'
    })
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'access_token' in data