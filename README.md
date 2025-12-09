# patient-360-dashboard-6122-6131

This workspace contains the Patient 360 Portal backend (FastAPI).

Quick start:
- Install deps: pip install -r patient_portal_backend/requirements.txt
- Run server: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 3001 (from patient_portal_backend directory)
- Generate OpenAPI file: python -m src.api.generate_openapi (from patient_portal_backend directory)
- Run tests: pytest (from patient_portal_backend directory)

Environment:
- Copy patient_portal_backend/.env.example to .env and set:
  - BACKEND_DB_URL=<database URL>
  - GEMINI_API_KEY=<api key> (optional)
  - GEMINI_MODEL=gemini-1.5-flash
