// Load templates when page loads
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
    }
    
    loadTemplates();
});

// Load templates from backend
async function loadTemplates() {
    const token = localStorage.getItem('access_token');
    const container = document.getElementById('templatesContainer');
    const alert = document.getElementById('alert');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/templates/`);
        
        if (response.ok) {
            const templates = await response.json();
            renderTemplates(templates);
        } else {
            throw new Error('Failed to load templates');
        }
    } catch (error) {
        console.error('Error loading templates:', error);
        container.innerHTML = `
            <div class="text-center" style="grid-column: 1 / -1; padding: var(--spacing-xl);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--danger);"></i>
                <p class="mt-md">Failed to load templates. Please try again.</p>
                <button class="btn btn-outline" onclick="loadTemplates()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render templates in the container
function renderTemplates(templates) {
    const container = document.getElementById('templatesContainer');
    
    if (templates.length === 0) {
        container.innerHTML = `
            <div class="text-center" style="grid-column: 1 / -1; padding: var(--spacing-xl);">
                <i class="fas fa-th-large" style="font-size: 2rem; color: var(--gray-400);"></i>
                <p class="mt-md">No templates available yet.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = templates.map(template => `
        <div class="feature-card">
            <div class="d-flex justify-content-between align-items-start mb-md">
                <div>
                    <h3 class="mb-sm">${template.name}</h3>
                    <p class="mb-0" style="color: var(--gray-600); font-size: var(--text-sm);">
                        ${template.description || 'No description provided'}
                    </p>
                </div>
                <div class="template-category badge badge-primary">
                    ${template.category}
                </div>
            </div>
            
            <div class="d-flex justify-content-between align-items-center mt-lg">
                <span style="color: var(--gray-500); font-size: var(--text-xs);">
                    <i class="fas fa-hashtag"></i> ID: ${template.id}
                </span>
                
                <div class="d-flex gap-sm">
                    <button class="btn btn-sm btn-outline" onclick="previewTemplate(${template.id})">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="useTemplate(${template.id})">
                        <i class="fas fa-plus"></i> Use Template
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Preview template
function previewTemplate(templateId) {
    showAlert('Template preview would open in a modal. In a real implementation, this would show template details.', 'info');
}

// Use template - create a new workflow based on this template
async function useTemplate(templateId) {
    const token = localStorage.getItem('access_token');
    const alert = document.getElementById('alert');
    
    try {
        // First, get the template details
        const templateResponse = await fetch(`${CONFIG.API_BASE_URL}/api/templates/${templateId}`);
        
        if (templateResponse.ok) {
            const template = await templateResponse.json();
            
            // Create a new workflow based on this template
            const workflowResponse = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: `Copy of ${template.name}`,
                    description: template.description,
                    n8n_workflow_id: template.n8n_workflow_id
                })
            });
            
            if (workflowResponse.ok) {
                const workflow = await workflowResponse.json();
                showAlert(`Template "${template.name}" added to your workflows!`, 'success');
                
                // Optionally redirect to the new workflow
                setTimeout(() => {
                    window.location.href = `/builder.html?id=${workflow.id}`;
                }, 2000);
            } else if (workflowResponse.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('access_token');
                window.location.href = '/login.html';
            } else {
                throw new Error('Failed to create workflow from template');
            }
        } else {
            throw new Error('Failed to load template');
        }
    } catch (error) {
        console.error('Error using template:', error);
        showAlert('Failed to use template. Please try again.', 'danger');
    }
}

// Show alert
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    const iconClass = type === 'success' ? 'check-circle' : 
                     type === 'danger' ? 'exclamation-triangle' : 
                     type === 'info' ? 'info-circle' : 'exclamation-triangle';
    
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="fas fa-${iconClass}"></i> ${message}`;
    alert.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Logout functionality
document.getElementById('logoutBtn').addEventListener('click', function(e) {
    e.preventDefault();
    localStorage.removeItem('access_token');
    window.location.href = '/login.html';
});
