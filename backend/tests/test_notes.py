import json
import pytest
import uuid

@pytest.fixture(scope='function')
def note(app, doctor, patient):
    """Create a test note."""
    note_uuid = str(uuid.uuid4())
    with app.app_context():
        from app.models.models import Note
        from app.extensions import db
        
        note = Note(
            uuid=note_uuid,
            doctor_id=doctor.id,
            patient_id=patient.id,
            title='Test Note',
            content='This is a test note content.',
            category='clinical'
        )
        db.session.add(note)
        db.session.commit()
        
        # Store the UUID to use in tests
        note_uuid = note.uuid
        
    # Return the values we need to use in the tests
    return type('NoteInfo', (), {
        'uuid': note_uuid,
        'title': 'Test Note',
        'content': 'This is a test note content.',
        'category': 'clinical'
    })

def test_get_notes(client, auth_headers, note):
    """Test getting list of notes"""
    response = client.get('/api/notes', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'notes' in data
    assert len(data['notes']) > 0
    assert data['pagination']['total'] > 0

def test_get_note(client, auth_headers, note):
    """Test getting a specific note"""
    response = client.get(f'/api/notes/{note.uuid}', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['id'] == note.uuid
    assert data['title'] == 'Test Note'
    assert data['content'] == 'This is a test note content.'
    assert data['category'] == 'clinical'

def test_create_note(client, auth_headers, patient):
    """Test creating a new note"""
    response = client.post('/api/notes', json={
        'patient_id': patient.uuid,
        'title': 'New Note',
        'content': 'This is a new test note content.',
        'category': 'administrative',
        'tags': [{'name': 'important', 'color': '#ff0000'}]
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert 'note' in data
    assert data['note']['title'] == 'New Note'

def test_update_note(client, auth_headers, note):
    """Test updating a note"""
    response = client.put(f'/api/notes/{note.uuid}', json={
        'content': 'Updated content',
        'category': 'follow-up',
        'tags': [{'name': 'review', 'color': '#00ff00'}]
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    
    # Verify note was updated
    check_response = client.get(f'/api/notes/{note.uuid}', headers=auth_headers)
    check_data = json.loads(check_response.data)
    assert check_data['content'] == 'Updated content'
    assert check_data['category'] == 'follow-up'

def test_delete_note(client, auth_headers, note):
    """Test deleting a note"""
    response = client.delete(f'/api/notes/{note.uuid}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verify note is deleted
    check_response = client.get(f'/api/notes/{note.uuid}', headers=auth_headers)
    assert check_response.status_code == 404

def test_tags_crud(client, auth_headers):
    """Test tag operations"""
    # Create tag
    response = client.post('/api/tags', json={
        'name': 'Test Tag',
        'color': '#0000ff'
    }, headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 201
    assert data['tag']['name'] == 'Test Tag'
    assert data['tag']['color'] == '#0000ff'
    
    # Get tags
    response = client.get('/api/tags', headers=auth_headers)
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert 'tags' in data
    assert len(data['tags']) > 0
    
    # Verify our tag is in the list
    found = False
    for tag in data['tags']:
        if tag['name'] == 'Test Tag':
            found = True
            break
    
    assert found, "Created tag not found in tags list"