// frontend/config.js - Browser-compatible configuration
(function() {
    // Detect environment
    const isProduction = window.location.hostname !== 'localhost' && !window.location.hostname.startsWith('127.0.0.1');
    const hostname = window.location.hostname;
    const isVercel = hostname.includes('vercel.app');

    // Create global CONFIG object
    window.CONFIG = {
        // API Base URL
        API_BASE_URL: isVercel 
            ? 'https://' + hostname + '/api' 
            : 'http://localhost:8000',
            
        // Google Client ID - using the one from Google Cloud Console
        GOOGLE_CLIENT_ID: '285368318527-re6cp4iq5r4gk8tsu4qu2llm5eus3bbq.apps.googleusercontent.com',
        
        // n8n configuration
        N8N_BASE_URL: isVercel 
            ? 'https://' + hostname + '/api/n8n'
            : 'http://localhost:5678',
            
        // Environment flags
        IS_PRODUCTION: isProduction,
        IS_VERCEL: isVercel,
        
        // Version info
        VERSION: '1.0.0',
        BUILD_DATE: new Date().toISOString()
    };

    // Debug logging
    if (!isProduction) {
        console.log('Frontend Environment:', {
            hostname,
            isProduction,
            isVercel,
            config: {
                ...window.CONFIG,
                GOOGLE_CLIENT_ID: '***REDACTED***' // Don't log the actual client ID
            }
        });
    }
})();