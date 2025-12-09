# Patient 360 Backend (FastAPI)

Quick start:
- cp .env.example .env
- pip install -r requirements.txt
- uvicorn src.api.main:app --reload --host 0.0.0.0 --port 3001

Environment (.env):
- BACKEND_DB_URL=<database URL> (optional; when unset, in-memory store is used)
- GEMINI_API_KEY=<api key> (optional; when unset, chatbot returns deterministic demo response)
- GEMINI_MODEL=gemini-1.5-flash

OpenAPI:
- Generate and write to interfaces/openapi.json
  python -m src.api.generate_openapi

Smoke checks:
- Health: GET / returns {"message":"Healthy","db_connected": true|false}
- Auth: POST /auth/login -> token; then GET /auth/status with Authorization: Bearer <token>
- Patients: Protected endpoints under /patients use in-memory store if BACKEND_DB_URL not provided
- Chatbot: POST /chatbot/send returns {"reply": "...", "model": "<from env or default>"}

Notes:
- Do not hardcode ports; use env to configure services (e.g., database on 5000/5001 via BACKEND_DB_URL).
