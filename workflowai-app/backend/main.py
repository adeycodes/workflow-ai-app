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
    get_current_user,
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
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth configuration is missing. Please check your .env file."
        )
    
    # Generate state parameter to prevent CSRF
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL with all required parameters
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile openid",
        "access_type": "offline",
        "state": state,
        "prompt": "consent"  # Force consent screen to ensure refresh token
    }
    
    # Build authorization URL
    from urllib.parse import urlencode
    authorization_url = f"{google_auth_url}?{urlencode(params)}"
    print(f"Redirecting to: {authorization_url}")  # Debug print
    return RedirectResponse(url=authorization_url, status_code=302)

@app.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Get the authorization code
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    try:
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
        
        print("Exchanging code for token...")  # Debug print
        token_response = requests.post(token_url, data=token_data)
        print(f"Token response status: {token_response.status_code}")  # Debug print
        
        if not token_response.ok:
            print('Google token error:', token_response.text)
            raise HTTPException(status_code=400, detail=f"Failed to get access token: {token_response.text}")
        
        token_info = token_response.json()
        access_token = token_info.get('access_token')
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in response")
        
        # Get user info from Google
        print("Getting user info...")  # Debug print
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_info_response = requests.get(user_info_url, headers={
            "Authorization": f"Bearer {access_token}"
        })
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        # Create or update user in database
        db_user = get_user(db, user_info['email'])
        if not db_user:
            # Create new user with Google info
            db_user = User(
                email=user_info['email'],
                username=user_info.get('name', user_info['email'].split('@')[0]),
                hashed_password="",  # No password for Google users
                is_active=True
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        elif not db_user.is_active:
            # If user exists but is inactive, activate them
            db_user.is_active = True
            db.commit()
            db.refresh(db_user)
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": db_user.email}, expires_delta=access_token_expires
        )
        
        # Update user with new token
        db_user.token = token
        db.commit()
        db.refresh(db_user)
        
        # Debug: Print token for verification
        print(f"Generated JWT token for {db_user.email}: {token}")
        
        # Create a response that will set the cookie and then redirect
        response = RedirectResponse(url="/dashboard.html", status_code=302)
        
        # Set the cookie with the token
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='lax',
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 60 minutes
        )
        
        # Also set a non-httpOnly cookie for the frontend to detect auth state
        response.set_cookie(
            key="is_authenticated",
            value="true",
            secure=False,
            samesite='lax',
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
        # Add debug information
        print(f"\n=== Authentication Successful ===")
        print(f"User: {db_user.email}")
        print(f"Token: {token[:20]}...")
        print(f"Cookies set: access_token and is_authenticated")
        print(f"Redirecting to: /dashboard.html")
        
        # Add debug headers
        response.headers["X-Auth-Status"] = "Authenticated"
        response.headers["X-User-Email"] = db_user.email
        
        return response
    
    except Exception as e:
        print(f"Error in callback: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

# Import CORS settings from config
from config import ALLOWED_ORIGINS

# CORS middleware with specific origins and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
        "X-Auth-Token",
        "Access-Control-Allow-Credentials"
    ],
    expose_headers=["*"],
    max_age=600,  # 10 minutes
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
async def read_users_me(request: Request, current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/auth/logout")
async def logout():
    response = RedirectResponse(url="/login.html")
    response.delete_cookie(key="access_token")
    return response

# Mount frontend static files last, after all API routes are registered
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Serve index.html for the root path
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_path, 'index.html'))

# Explicitly serve dashboard.html
@app.get("/dashboard.html")
async def serve_dashboard():
    dashboard_path = os.path.join(frontend_path, 'dashboard.html')
    if not os.path.exists(dashboard_path):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(dashboard_path)

# Catch-all route for SPA routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(frontend_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # For SPA routing, return index.html and let the frontend router handle it
    return FileResponse(os.path.join(frontend_path, 'index.html'))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
