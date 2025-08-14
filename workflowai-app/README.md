# workflow-ai-app

# WorkflowAI - Business Automation Tool

WorkflowAI is a full-stack workflow automation web application designed for Nigerian SMEs and entrepreneurs. It allows users to automate repetitive business tasks using a drag-and-drop builder powered by n8n.

## Features

### Frontend (React/Vanilla JS)

- Landing page with business-focused copy
- Login/Signup pages
- Dashboard with active workflows and execution history
- Workflow Builder (iframe-based n8n integration)
- Template Library with pre-built workflows
- Settings and Billing (Paystack integration)
- Responsive design for all devices

### Backend (Python - FastAPI)

- JWT Authentication
- CRUD operations for workflows
- Execution logs tracking
- Template management
- Admin panel for managing templates
- Secure API endpoints

### Integrations

- n8n hosted instance (iframe integration)
- SQLite database
- Paystack for subscriptions
- Webhook endpoint for third-party events

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, FastAPI
- **Database**: SQLite
- **Authentication**: JWT
- **Workflow Engine**: n8n (iframe integration)
- **Payment**: Paystack
- **Deployment**: Replit

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/workflowai-app.git
   cd workflowai-app


   running backend
   -- uvicorn main:app
   ```
