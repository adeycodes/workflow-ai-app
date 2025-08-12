document.getElementById('signupForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fullName = document.getElementById('fullName').value;
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const terms = document.getElementById('terms').checked;
    const alert = document.getElementById('alert');
    const signupBtn = document.getElementById('signupBtn');
    const signupText = document.getElementById('signupText');
    const signupSpinner = document.getElementById('signupSpinner');
    
    // Reset alert
    alert.style.display = 'none';
    
    // Validate form
    if (password !== confirmPassword) {
        alert.className = 'alert alert-danger';
        alert.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Passwords do not match';
        alert.style.display = 'block';
        return;
    }
    
    if (!terms) {
        alert.className = 'alert alert-danger';
        alert.innerHTML = '<i class="fas fa-exclamation-triangle"></i> You must agree to the Terms of Service';
        alert.style.display = 'block';
        return;
    }
    
    // Show loading state
    signupText.style.display = 'none';
    signupSpinner.style.display = 'inline-block';
    signupBtn.disabled = true;
    
    try {
        const response = await fetch(CONFIG.API_BASE_URL + '/users/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // If backend returns a token, store and redirect
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                window.location.href = '/dashboard.html';
                return;
            }
            alert.className = 'alert alert-success';
            alert.innerHTML = '<i class="fas fa-check-circle"></i> Account created successfully! Redirecting to login...';
            alert.style.display = 'block';
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 2000);
        } else {
            alert.className = 'alert alert-danger';
            alert.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${data.detail || 'Signup failed'}`;
            alert.style.display = 'block';
        }
    } catch (error) {
        alert.className = 'alert alert-danger';
        alert.innerHTML = '<i class="fas fa-exclamation-triangle"></i> An error occurred. Please try again.';
        alert.style.display = 'block';
    } finally {
        signupText.style.display = 'inline';
        signupSpinner.style.display = 'none';
        signupBtn.disabled = false;
    }
});

// Google Signup
document.getElementById('googleSignupBtn').addEventListener('click', function() {
    // Redirect to Google OAuth endpoint for signup
    window.location.href = CONFIG.API_BASE_URL + '/auth/google/login';
});

// Handle Google OAuth callback (if redirected back with token)
document.addEventListener('DOMContentLoaded', function() {
    const params = new URLSearchParams(window.location.search);
    if (params.has('access_token')) {
        localStorage.setItem('access_token', params.get('access_token'));
        window.location.href = '/dashboard.html';
    }
});

// Microsoft Signup (placeholder)
document.getElementById('microsoftSignupBtn').addEventListener('click', function() {
    const alert = document.getElementById('alert');
    alert.className = 'alert alert-info';
    alert.innerHTML = '<i class="fas fa-info-circle"></i> Microsoft signup is not yet implemented.';
    alert.style.display = 'block';
});
