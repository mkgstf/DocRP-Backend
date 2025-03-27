# DocRP - Doctor Resource Planning System

A comprehensive resource planning system for healthcare facilities, built with Flask.

## Features

- User Management & Authentication
- Patient Management
- Appointment Management
- Resource Management
- Billing and Finance
- Dashboard and Analytics
- Communication System

## Tech Stack

- Backend: Flask (Python)
- Database: PostgreSQL
- Task Queue: Celery with Redis
- Frontend: HTML, CSS, JavaScript
- Authentication: JWT + Flask-Login

## Project Structure

```
docrp/
├── app/
│   ├── static/          # Static files (CSS, JS, images)
│   ├── templates/       # HTML templates
│   ├── models/         # Database models
│   ├── controllers/    # Route handlers
│   ├── services/       # Business logic
│   └── utils/          # Helper functions
├── config/            # Configuration files
├── tests/            # Test cases
├── docs/             # Documentation
├── requirements.txt  # Python dependencies
├── .env.example     # Environment variables template
├── .gitignore       # Git ignore rules
└── run.py           # Application entry point
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd docrp
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   flask run
   ```

## Development

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed

## Testing

Run tests using pytest:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
