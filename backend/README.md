# Clinic ERP Backend API

This is a backend API for an ERP-like system designed for doctors who own clinics. It provides comprehensive endpoints for managing patients, appointments, medicines, prescriptions, diagnoses, statistics, and medical notes.

## Features

* Multi-doctor support with JWT authentication
* Patient and appointment management
* Dynamic medicine, diagnosis, and patient entry with recommendations
* Notes and prescription generation
* Statistical insights
* Modular and scalable Flask Blueprints

## Project Structure

```
clinic_erp_backend/
├── app/
│   ├── __init__.py         # Application factory
│   ├── config.py           # Configuration settings
│   ├── db.py               # Database utilities
│   ├── models/
│   │   └── models.py       # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── patients.py     # Patient management endpoints
│   │   ├── appointments.py # Appointment scheduling
│   │   ├── medicines.py    # Medicine database
│   │   ├── prescriptions.py # Prescription generation
│   │   ├── diagnoses.py    # Diagnosis management
│   │   ├── statistics.py   # Analytics and reporting
│   │   ├── notes.py        # Clinical notes
│   │   └── doctors.py      # Doctor/user management
│   ├── services/
│   │   ├── recommendation.py # Recommendation engine
│   │   └── utils.py        # Utility functions
├── migrations/             # Database migrations
├── tests/                  # Test suite
├── run.py                  # Application entry point
├── requirements.txt        # Dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL (recommended) or SQLite
- pip

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd clinic_erp_backend
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
FLASK_APP=run.py
FLASK_DEBUG=True
DATABASE_URI=postgresql://username:password@localhost/clinic_erp
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

5. Initialize the database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application
```bash
flask run
```

## API Endpoints

### Authentication
- `POST /api/login` - Login for doctors
- `POST /api/refresh` - Refresh JWT token

### Patients
- `GET /api/patients` - List all patients
- `POST /api/patients` - Create a new patient
- `GET /api/patients/<id>` - Get patient details
- `PUT /api/patients/<id>` - Update patient information
- `DELETE /api/patients/<id>` - Remove a patient
- `GET /api/patients/search` - Search patients (autocomplete)

### Appointments
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Schedule an appointment
- `GET /api/appointments/<id>` - Get appointment details
- `PUT /api/appointments/<id>` - Update an appointment
- `DELETE /api/appointments/<id>` - Cancel an appointment
- `GET /api/calendar` - Get calendar view of appointments

### Medicines
- `GET /api/medicines` - List medicines
- `POST /api/medicines` - Add a new medicine
- `GET /api/medicines/search` - Search medicines (autocomplete)

### Prescriptions
- `GET /api/prescriptions` - List prescriptions
- `POST /api/prescriptions` - Create a prescription
- `GET /api/prescriptions/<id>` - Get prescription details
- `PUT /api/prescriptions/<id>` - Update a prescription
- `GET /api/prescriptions/export/<id>` - Export prescription as PDF

### Diagnoses
- `GET /api/diagnoses` - List diagnoses
- `GET /api/diagnoses/search` - Search diagnoses (autocomplete)
- `GET /api/patients/<id>/diagnoses` - Get patient diagnoses

### Statistics
- `GET /api/stats/overview` - Get clinic overview statistics
- `GET /api/stats/appointments` - Get appointment statistics
- `GET /api/stats/diagnoses` - Get diagnosis statistics
- `GET /api/stats/prescriptions` - Get prescription statistics
- `GET /api/stats/export` - Export statistics as CSV

### Notes
- `GET /api/notes` - List clinical notes
- `POST /api/notes` - Create a note
- `GET /api/notes/<id>` - Get note details
- `PUT /api/notes/<id>` - Update a note
- `GET /api/tags` - Get all tags for notes

## Security

This API implements several security measures:

- JWT authentication
- Password hashing
- Input validation
- CSRF protection
- Role-based access control

## Testing

Run the test suite:

```bash
pytest
```

## License

This project is licensed under the MIT License.