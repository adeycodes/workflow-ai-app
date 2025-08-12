document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
    }
    
    // Logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        });
    }
    
    // Profile form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            showAlert('Profile updated successfully!', 'success');
        });
    }
    
    // Password form submission
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const newPassword = document.getElementById('newPassword').value;
            const confirmNewPassword = document.getElementById('confirmNewPassword').value;
            
            if (newPassword !== confirmNewPassword) {
                showAlert('New passwords do not match', 'danger');
                return;
            }
            
            if (newPassword.length < 8) {
                showAlert('Password must be at least 8 characters long', 'danger');
                return;
            }
            
            // In a real implementation, this would make an API call to update the password
            showAlert('Password updated successfully!', 'success');
            
            // Reset form
            passwordForm.reset();
        });
    }
    
    // Show alert function
    function showAlert(message, type) {
        const alert = document.getElementById('alert');
        if (!alert) return;
        
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
