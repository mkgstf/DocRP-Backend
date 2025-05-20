# 🏥 Clinic ERP Backend API – Blueprint

This project is a backend API for an ERP-like system used by doctors who own clinics. It provides endpoints for managing patients, appointments, medicines, prescriptions, diagnoses, statistics, and notes.

---

## 📁 Project Structure

```plaintext
clinic_erp_backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── models/
│   │   └── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── patients.py
│   │   ├── appointments.py
│   │   ├── medicines.py
│   │   ├── prescriptions.py
│   │   ├── diagnoses.py
│   │   ├── statistics.py
│   │   ├── notes.py
│   │   └── doctors.py
│   ├── services/
│   │   ├── recommendation.py
│   │   └── utils.py
├── migrations/
├── tests/
├── run.py
├── requirements.txt
└── README.md
```

---

## 🔑 Key Features

* Multi-doctor support with JWT authentication
* Patient and appointment management
* Dynamic medicine, diagnosis, and patient entry with recommendations
* Notes and prescription generation
* Statistical insights
* Modular and scalable Flask Blueprints

---

## 📦 Blueprints Overview

Each functional domain is separated into its own blueprint inside the `routes/` directory.

### `routes/patients.py`

```python
from flask import Blueprint

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/patients', methods=['GET'])
def get_patients():
    return "List of patients"
```

### `routes/appointments.py`

```python
from flask import Blueprint

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments', methods=['POST'])
def create_appointment():
    return "Create an appointment"
```

### `routes/medicines.py`

```python
from flask import Blueprint

medicines_bp = Blueprint('medicines', __name__)

@medicines_bp.route('/medicines/search', methods=['GET'])
def search_medicines():
    return "Autocomplete medicine names"
```

*Repeat similarly for prescriptions, diagnoses, statistics, and notes.*

---

## 🚀 Initialization (`app/__init__.py`)

```python
from flask import Flask
from .routes.patients import patients_bp
from .routes.appointments import appointments_bp
# ... import other blueprints

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(patients_bp, url_prefix='/api')
    app.register_blueprint(appointments_bp, url_prefix='/api')
    # ... register other blueprints

    return app
```

---

## 📊 Quality-of-Life Features

* Autocomplete for medicines, diagnoses, patients
* Auto-save custom inputs to DB
* Export prescription/statistics as PDF/CSV
* Search and filters
* Tagging and note categorization
* Logging and activity history
* Optional: AI-based suggestions, voice notes

---

## 🛡️ Security

* JWT for doctor authentication
* Role-based access control
* Input validation and XSS/CSRF protection
* HTTPS with secure headers

---

## ✅ Example API Endpoints

| Method | Endpoint                   | Description                |
| ------ | -------------------------- | -------------------------- |
| `POST` | `/api/login`               | Doctor login               |
| `GET`  | `/api/patients`            | List all patients          |
| `POST` | `/api/appointments`        | Schedule an appointment    |
| `GET`  | `/api/medicines/search?q=` | Autocomplete medicine name |
| `POST` | `/api/prescriptions`       | Create a new prescription  |
| `GET`  | `/api/stats/overview`      | Get clinic statistics      |

---