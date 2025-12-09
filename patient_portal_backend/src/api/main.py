import os
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from starlette.responses import JSONResponse

# PUBLIC_INTERFACE
def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with a default."""
    return os.getenv(name, default)


# Simple in-memory token store for demo. In real world use JWT or session store.
_FAKE_TOKENS: Dict[str, str] = {}  # token -> username

# Simple in-memory "database" fallback if BACKEND_DB_URL is not configured.
_INMEMORY_PATIENTS: Dict[str, Dict[str, Any]] = {}


class AppSettings(BaseModel):
    """Application settings loaded from environment variables."""
    app_name: str = "Patient 360 Backend"
    app_version: str = "0.1.0"
    backend_db_url: Optional[str] = Field(default_factory=lambda: get_env("BACKEND_DB_URL"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: get_env("GEMINI_API_KEY"))
    gemini_model: Optional[str] = Field(default_factory=lambda: get_env("GEMINI_MODEL", "gemini-1.5-flash"))


settings = AppSettings()

openapi_tags = [
    {"name": "Health", "description": "Service health and metadata."},
    {"name": "Auth", "description": "Authentication and user session management."},
    {"name": "Patients", "description": "Patient CRUD and profile management."},
    {"name": "Chatbot", "description": "Gemini chatbot integration for medical Q&A."},
]

app = FastAPI(
    title=settings.app_name,
    description="REST APIs for Patient 360 Portal (auth, patients, chatbot).",
    version=settings.app_version,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Access token to authorize subsequent requests.")
    token_type: str = Field(default="bearer", description="Token type (bearer).")


class UserProfile(BaseModel):
    username: str = Field(..., description="Unique username of the user.")
    email: EmailStr = Field(..., description="Email for the user.")


class AuthSuccess(BaseModel):
    token: TokenResponse = Field(..., description="Authentication token response.")
    profile: UserProfile = Field(..., description="Basic user profile for the authenticated user.")


class AuthStatus(BaseModel):
    authenticated: bool = Field(..., description="Indicates whether the token is valid.")
    username: Optional[str] = Field(None, description="Username tied to the token.")


class PatientCreate(BaseModel):
    first_name: str = Field(..., description="Patient first name")
    last_name: str = Field(..., description="Patient last name")
    email: EmailStr = Field(..., description="Patient contact email")
    age: Optional[int] = Field(None, description="Patient age in years", ge=0)
    conditions: List[str] = Field(default_factory=list, description="Known medical conditions")


class Patient(BaseModel):
    id: str = Field(..., description="Patient unique identifier")
    first_name: str = Field(..., description="Patient first name")
    last_name: str = Field(..., description="Patient last name")
    email: EmailStr = Field(..., description="Patient contact email")
    age: Optional[int] = Field(None, description="Patient age in years", ge=0)
    conditions: List[str] = Field(default_factory=list, description="Known medical conditions")


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, description="Patient first name")
    last_name: Optional[str] = Field(None, description="Patient last name")
    email: Optional[EmailStr] = Field(None, description="Patient contact email")
    age: Optional[int] = Field(None, description="Patient age in years", ge=0)
    conditions: Optional[List[str]] = Field(None, description="Known medical conditions")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Message from the user to the chatbot.")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context for the chatbot to use.")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Chatbot reply to the message.")
    model: str = Field(..., description="Gemini model used to generate the reply.")


# Utilities
def _ensure_demo_data():
    if not _INMEMORY_PATIENTS:
        _INMEMORY_PATIENTS["p-1"] = {
            "id": "p-1",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "age": 36,
            "conditions": ["diabetes"],
        }
        _INMEMORY_PATIENTS["p-2"] = {
            "id": "p-2",
            "first_name": "Alan",
            "last_name": "Turing",
            "email": "alan@example.com",
            "age": 41,
            "conditions": ["hypertension"],
        }


# PUBLIC_INTERFACE
def get_db_url() -> Optional[str]:
    """Return the configured database URL from environment variable BACKEND_DB_URL."""
    return settings.backend_db_url


# Dependency for auth
# PUBLIC_INTERFACE
def get_current_username(authorization: Optional[str] = Header(default=None)) -> str:
    """Parse Authorization header and validate token for protected endpoints.

    Expects header: Authorization: Bearer <token>
    Returns the associated username if valid, otherwise raises 401.
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    username = _FAKE_TOKENS.get(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return username


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """Simple health check endpoint.

    Returns:
        JSON object with message and optional database connectivity information.
    """
    msg = {"message": "Healthy"}
    db_url = get_db_url()
    msg["db_connected"] = bool(db_url)  # We don't actually connect here to keep demo simple
    return msg


# Auth routes
# PUBLIC_INTERFACE
@app.post(
    "/auth/login",
    tags=["Auth"],
    summary="User login",
    response_model=AuthSuccess,
    responses={
        200: {"description": "Login successful"},
        400: {"description": "Invalid credentials"},
    },
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user with username/password.

    Parameters:
      - form_data: OAuth2 form with 'username' and 'password'
    Returns:
      AuthSuccess containing bearer token and basic profile.
    Notes:
      This demo accepts any non-empty username/password.
    """
    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    # Issue a simple token based on username for demo only.
    token = f"token-{form_data.username}"
    _FAKE_TOKENS[token] = form_data.username
    profile = UserProfile(username=form_data.username, email=f"{form_data.username}@example.com")
    return AuthSuccess(token=TokenResponse(access_token=token), profile=profile)


# PUBLIC_INTERFACE
@app.get(
    "/auth/status",
    tags=["Auth"],
    summary="Check auth status",
    response_model=AuthStatus,
)
def auth_status(authorization: Optional[str] = Header(default=None)):
    """Check whether an Authorization token is valid.

    Parameters:
      - Authorization: Bearer <token>
    Returns:
      AuthStatus indicating authentication state.
    """
    if not authorization:
        return AuthStatus(authenticated=False)
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return AuthStatus(authenticated=False)
    username = _FAKE_TOKENS.get(token)
    return AuthStatus(authenticated=bool(username), username=username)


# Patients routes
# PUBLIC_INTERFACE
@app.get(
    "/patients",
    tags=["Patients"],
    summary="List patients",
    response_model=List[Patient],
)
def list_patients(username: str = Depends(get_current_username)):
    """List all patients.

    Requires Authorization header. Uses in-memory storage for demo.
    """
    _ensure_demo_data()
    return list(_INMEMORY_PATIENTS.values())


# PUBLIC_INTERFACE
@app.post(
    "/patients",
    tags=["Patients"],
    summary="Create patient",
    response_model=Patient,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(payload: PatientCreate, username: str = Depends(get_current_username)):
    """Create a new patient record."""
    _ensure_demo_data()
    new_id = f"p-{len(_INMEMORY_PATIENTS) + 1}"
    patient = Patient(id=new_id, **payload.model_dump())
    _INMEMORY_PATIENTS[new_id] = patient.model_dump()
    return patient


# PUBLIC_INTERFACE
@app.get(
    "/patients/{patient_id}",
    tags=["Patients"],
    summary="Get patient by id",
    response_model=Patient,
)
def get_patient(patient_id: str, username: str = Depends(get_current_username)):
    """Get a single patient by id."""
    _ensure_demo_data()
    data = _INMEMORY_PATIENTS.get(patient_id)
    if not data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return data


# PUBLIC_INTERFACE
@app.put(
    "/patients/{patient_id}",
    tags=["Patients"],
    summary="Update patient",
    response_model=Patient,
)
def update_patient(patient_id: str, payload: PatientUpdate, username: str = Depends(get_current_username)):
    """Update a patient record."""
    _ensure_demo_data()
    if patient_id not in _INMEMORY_PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")
    stored = _INMEMORY_PATIENTS[patient_id]
    update = payload.model_dump(exclude_none=True)
    stored.update(update)
    _INMEMORY_PATIENTS[patient_id] = stored
    return stored


# PUBLIC_INTERFACE
@app.delete(
    "/patients/{patient_id}",
    tags=["Patients"],
    summary="Delete patient",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "Patient deleted"}},
)
def delete_patient(patient_id: str, username: str = Depends(get_current_username)):
    """Delete a patient record."""
    _ensure_demo_data()
    if patient_id not in _INMEMORY_PATIENTS:
        raise HTTPException(status_code=404, detail="Patient not found")
    del _INMEMORY_PATIENTS[patient_id]
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


# Chatbot routes
def _fake_gemini_reply(message: str) -> str:
    """Local fallback reply for chatbot when no Gemini credentials are configured."""
    if not message.strip():
        return "Please provide a message so I can help."
    return f"[Demo Gemini] You said: {message}"


# PUBLIC_INTERFACE
@app.post(
    "/chatbot/send",
    tags=["Chatbot"],
    summary="Send a message to chatbot",
    response_model=ChatResponse,
)
def chatbot_send(payload: ChatRequest, username: str = Depends(get_current_username)):
    """Send a message to the chatbot and get a response.

    If GEMINI_API_KEY is set, this is where the real Gemini call would be made.
    For this implementation, we return a deterministic demo response while
    surfacing the configured model name from the environment.
    """
    model = settings.gemini_model or "gemini-1.5-flash"
    # If GEMINI_API_KEY were configured, here we'd call Gemini APIs using httpx.
    reply = _fake_gemini_reply(payload.message)
    return ChatResponse(reply=reply, model=model)
