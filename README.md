# patient-360-dashboard-6122-6131

This workspace contains the Patient 360 Portal backend (FastAPI).

Backend quick start:
- Create env file:
  cp patient_portal_backend/.env.example patient_portal_backend/.env
- Install deps:
  pip install -r patient_portal_backend/requirements.txt
- Run server (from patient_portal_backend):
  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 3001
- Generate OpenAPI (from patient_portal_backend):
  python -m src.api.generate_openapi
- Run tests (from patient_portal_backend):
  pytest

Backend Environment (.env):
- BACKEND_DB_URL=<database URL> (optional; if omitted, demo in-memory store is used)
- GEMINI_API_KEY=<api key> (optional; if omitted, chatbot returns deterministic demo response)
- GEMINI_MODEL=gemini-1.5-flash

Frontend quick start (separate workspace patient-360-dashboard-6122-6133):
- Create env file:
  cp patient_portal_frontend/.env.example patient_portal_frontend/.env
- Ensure backend URL is set in frontend .env:
  REACT_APP_BACKEND_URL=http://localhost:3001
- Start frontend dev server (from patient_portal_frontend):
  npm install
  npm start

Light smoke checks (no runtime here, for reference):
- Health: GET http://localhost:3001/ should return {"message":"Healthy","db_connected":<bool>}
- Auth: POST /auth/login with form username/password returns token, then GET /auth/status with Authorization: Bearer <token>
- Patients: With Authorization header, GET /patients returns list; POST/PUT/DELETE routes work with in-memory store
- Chatbot: With Authorization header, POST /chatbot/send {"message":"Hello"} returns {"reply": "...Hello...", "model":"<from env or default>"}

Notes:
- Do not hardcode ports. Configure via env only:
  - Backend runs typically on 3001
  - Database service (if used) might run on 5000/5001; set BACKEND_DB_URL accordingly
- OpenAPI spec is output to patient_portal_backend/interfaces/openapi.json
