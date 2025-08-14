import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Environment detection
IS_PRODUCTION = os.getenv('VERCEL_ENV') == 'production'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Set redirect URI based on environment
if IS_PRODUCTION:
    BASE_URL = "https://workflow-ai-app.vercel.app"
    GOOGLE_REDIRECT_URI = f"{BASE_URL}/api/auth/google/callback"
    DATABASE_URL = os.getenv("POSTGRES_URL")  # Vercel Postgres URL
else:
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{BASE_URL}/api/auth/google/callback")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workflowai.db")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
if not SECRET_KEY and IS_PRODUCTION:
    raise ValueError("JWT_SECRET must be set in production")
SECRET_KEY = SECRET_KEY or "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

# CORS Configuration
if IS_PRODUCTION:
    ALLOWED_ORIGINS = [
        "https://workflow-ai-app.vercel.app",
        "https://*.vercel.app"
    ]
else:
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost"
    ]
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# n8n
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

# Paystack
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")