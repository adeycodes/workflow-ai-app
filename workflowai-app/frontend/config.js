// frontend/config.js
const isProduction = window.location.hostname !== 'localhost' && !window.location.hostname.startsWith('127.0.0.1');
const hostname = window.location.hostname;

// Log environment for debugging
console.log('Frontend Environment:', {
    hostname,
    isProduction,
    env: process.env.NODE_ENV,
    vercelEnv: process.env.VERCEL_ENV
});

const CONFIG = {
    // Use relative URLs in production to avoid CORS issues
    API_BASE_URL: isProduction 
        ? 'https://workflow-ai-app.vercel.app/api' 
        : 'http://localhost:8000',
        
    // Google Client ID - make sure to set this in Vercel environment variables
    GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '285368318527-re6cp4iq5r4gk8tsu4qu2llm5eus3bbq.apps.googleusercontent.com',
    
    // n8n configuration
    N8N_BASE_URL: isProduction 
        ? 'https://workflow-ai-app.vercel.app/api/n8n'  // If using n8n as an API route
        : 'http://localhost:5678',
        
    // Add other environment-specific settings here
    IS_PRODUCTION: isProduction,
    
    // Add version info
    VERSION: '1.0.0',
    BUILD_DATE: new Date().toISOString()
};

// Log the config (without sensitive data)
console.log('App Config:', {
    ...CONFIG,
    GOOGLE_CLIENT_ID: CONFIG.GOOGLE_CLIENT_ID ? '***REDACTED***' : 'Not set'
});

export default CONFIG;