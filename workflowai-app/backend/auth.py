from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import User
from database import get_db
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # Debug: Print request details
    print("\n=== Authentication Debug ===")
    print(f"Request URL: {request.url}")
    print(f"Request Method: {request.method}")
    print("Request Headers:", dict(request.headers))
    print("Request Cookies:", request.cookies)
    
    # Try to get token from Authorization header first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        print("Found token in Authorization header")
    
    # Then try to get token from cookie
    elif "access_token" in request.cookies:
        cookie_token = request.cookies["access_token"]
        if cookie_token.startswith("Bearer "):
            token = cookie_token.split(" ")[1]
            print("Found token in access_token cookie")
    
    # If still no token, try to get from query parameters (for testing)
    elif "token" in request.query_params:
        token = request.query_params["token"]
        print("Found token in query parameters")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        print("No token found in headers, cookies, or query parameters")
        raise credentials_exception
    
    try:
        # Print token for debugging (only first 10 chars for security)
        print(f"Token (first 10 chars): {token[:10]}..." if token else "No token")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            print("No email in token payload")
            raise credentials_exception
            
        print(f"Token payload: {payload}")
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    user = get_user(db, email=email)
    if user is None:
        print(f"User not found in database: {email}")
        raise credentials_exception
    
    # Verify token matches the one in the database
    if not hasattr(user, 'token') or user.token != token:
        print("Token does not match the one in database")
        print(f"DB Token: {user.token[:10]}..." if hasattr(user, 'token') and user.token else "No token in database")
        raise credentials_exception
    
    print(f"Successfully authenticated user: {user.email}")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user