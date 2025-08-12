from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import os
import secrets
import hashlib
import requests
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

# Utility function to get user by email
def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()
from datetime import timedelta
from pydantic import BaseModel
from workflows import router as workflows_router
from templates import router as templates_router
from logs import router as logs_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WorkflowAI API", description="Business automation tool for Nigerian SMEs")

# API routes and OAuth routes go first
@app.get("/auth/google/login")
async def google_login():
    """Start the Google OAuth flow"""
    # Configure OAuth 2.0 params
    from config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI
    
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": secrets.token_urlsafe(32)
    }
    
    # Build authorization URL
    from urllib.parse import urlencode
    authorization_url = f"{google_auth_url}?{urlencode(params)}"
    return RedirectResponse(authorization_url)

@app.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Get the authorization code
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    # Exchange code for tokens
    from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    token_response = requests.post(token_url, data=token_data)
    if not token_response.ok:
        print('Google token error:', token_response.text)
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    token_info = token_response.json()
    access_token = token_info.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain access token")
    
    # Get user info from Google
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    user_info_response = requests.get(user_info_url, params={'access_token': access_token})
    user_info_response.raise_for_status()
    user_info = user_info_response.json()
    
    # Get or create user
    db_user = get_user(db, user_info['email'])
    if not db_user:
        db_user = User(
            email=user_info['email'],
            username=user_info['email'].split('@')[0],
            is_active=True,
            is_admin=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    
    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    # Redirect to dashboard with token
    return RedirectResponse(f"/dashboard.html?access_token={token}")

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


from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

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
    # Get the authorization code from the query parameters
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    # Exchange the authorization code for an access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    # Make the request to Google to exchange the code for an access token
    token_response = requests.post(token_url, data=token_data)
    if not token_response.ok:
        print('Google token error:', token_response.text)
    token_response.raise_for_status()
    token_info = token_response.json()
    access_token = token_info.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain access token")
    
    # Get user info from Google using the access token
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    user_info_response = requests.get(user_info_url, params={'access_token': access_token})
    user_info_response.raise_for_status()
    user_info = user_info_response.json()
    
    # Check if user exists, if not create them
    db_user = get_user(db, user_info['email'])
    if not db_user:
        db_user = User(
            email=user_info['email'],
            username=user_info['email'].split('@')[0],
            is_active=True,
            is_admin=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    
    # Create access token for the user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    # Redirect to dashboard with the token
    redirect_url = f"/dashboard.html?access_token={token}"
    return RedirectResponse(redirect_url)

# Mount frontend static files last, after all API routes are registered
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
