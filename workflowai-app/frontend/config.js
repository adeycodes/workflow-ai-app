// frontend/config.js
const isProduction = window.location.hostname !== 'localhost' && !window.location.hostname.startsWith('127.0.0.1');

const CONFIG = {
    // Use relative URLs in production to avoid CORS issues
    API_BASE_URL: isProduction ? '' : 'http://localhost:8000',
    // Google Client ID should be set via environment variables in production
    GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID',
    // n8n configuration - using local n8n instance in development
    N8N_BASE_URL: isProduction 
        ? 'https://your-n8n-instance.vercel.app'  // Replace with your n8n instance URL in production
        : 'http://localhost:5678',
    // Add other environment-specific settings here
    IS_PRODUCTION: isProduction
};

// Make sure to set the correct Google Client ID in Vercel environment variables
export default CONFIG;