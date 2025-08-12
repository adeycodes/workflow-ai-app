document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const alert = document.getElementById('alert');
            const loginBtn = document.getElementById('loginBtn');
            const loginText = document.getElementById('loginText');
            const loginSpinner = document.getElementById('loginSpinner');
            
            // Reset alert
            alert.style.display = 'none';
            
            // Show loading state
            loginText.style.display = 'none';
            loginSpinner.style.display = 'inline-block';
            loginBtn.disabled = true;
            
            try {
                const response = await fetch(CONFIG.API_BASE_URL + '/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: new URLSearchParams({
                        'username': email,
                        'password': password
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Store token in localStorage
                    localStorage.setItem('access_token', data.access_token);
                    
                    alert.className = 'alert alert-success';
                    alert.innerHTML = '<i class="fas fa-check-circle"></i> Login successful! Redirecting...';
                    alert.style.display = 'block';
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard.html';
                    }, 1000);
                } else {
                    alert.className = 'alert alert-danger';
                    alert.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${data.detail || 'Login failed'}`;
                    alert.style.display = 'block';
                }
            } catch (error) {
                alert.className = 'alert alert-danger';
                alert.innerHTML = '<i class="fas fa-exclamation-triangle"></i> An error occurred. Please try again.';
                alert.style.display = 'block';
            } finally {
                // Restore button state
                loginText.style.display = 'inline';
                loginSpinner.style.display = 'none';
                loginBtn.disabled = false;
            }
        });
    }
    
    // Google Login
    document.getElementById('googleLoginBtn').addEventListener('click', function() {
        // Redirect to Google OAuth endpoint
        window.location.href = CONFIG.API_BASE_URL + '/auth/google/login';
    });

    // Microsoft Login (placeholder)
    document.getElementById('microsoftLoginBtn').addEventListener('click', function() {
        const alert = document.getElementById('alert');
        alert.className = 'alert alert-info';
        alert.innerHTML = '<i class="fas fa-info-circle"></i> Microsoft login is not yet implemented.';
        alert.style.display = 'block';
    });
    
    // Show alert function
    function showAlert(message, type) {
        const alert = document.getElementById('alert');
        const iconClass = type === 'success' ? 'check-circle' : 
                         type === 'danger' ? 'exclamation-triangle' : 
                         type === 'warning' ? 'exclamation-circle' : 'info-circle';
        
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `<i class="fas fa-${iconClass}"></i> ${message}`;
        alert.style.display = 'flex';
        
        // Smooth show animation
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            alert.style.transition = 'all 0.3s ease';
            alert.style.opacity = '1';
            alert.style.transform = 'translateY(0)';
        }, 10);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    }
});
