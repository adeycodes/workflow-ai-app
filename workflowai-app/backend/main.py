from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import secrets
import hashlib

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from database import engine, Base, get_db
from models import User, Workflow, ExecutionLog, Template
from auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from pydantic import BaseModel
from workflows import router as workflows_router
from templates import router as templates_router
from logs import router as logs_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WorkflowAI API", description="Business automation tool for Nigerian SMEs")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(workflows_router, prefix="/api", dependencies=[Depends(get_current_active_user)])
app.include_router(templates_router, prefix="/api")
app.include_router(logs_router, prefix="/api", dependencies=[Depends(get_current_active_user)])

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str = None

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    
    class Config:
        orm_mode = True

# Root endpoint - make sure this is at the top level
@app.get("/")
def read_root():
    return {"message": "Welcome to WorkflowAI API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add these constants (you'll need to get these from Google Cloud Console)
GOOGLE_CLIENT_ID = "your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
GOOGLE_REDIRECT_URI = "https://fantastic-halibut-v9xx69w6vwqfxv7x-8000.app.github.dev/auth/google/callback"

@app.get("/auth/google/login")
async def google_login():
    """Initiate Google OAuth login"""
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    
    # In a real app, you'd store this state in a session or database
    # For now, we'll pass it in the URL
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope=email profile"
        f"&response_type=code"
        f"&state={state}"
    )
    
    return RedirectResponse(google_auth_url)

@app.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code
    }
    
    # In a real implementation, you'd make the actual request to Google
    # For now, let's create a simplified version
    
    # Get user info from Google (simplified)
    # In reality, you'd validate the token and get user info
    
    # Create or get user
    # This is a simplified example - you'd need to implement the actual Google token validation
    
    return {"message": "Google authentication would be implemented here"}
