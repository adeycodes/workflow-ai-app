import requests
from typing import Dict, Any, Optional, List
from config import N8N_BASE_URL, N8N_API_KEY
from fastapi import HTTPException

class N8NService:
    def __init__(self):
        self.base_url = N8N_BASE_URL
        self.headers = {
            "X-N8N-API-KEY": N8N_API_KEY,
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to n8n API"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error communicating with n8n: {str(e)}"
            )

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict:
        """Create a new workflow in n8n"""
        return self._make_request("POST", "workflows", workflow_data)

    def get_workflow(self, workflow_id: str) -> Dict:
        """Get workflow details from n8n"""
        return self._make_request("GET", f"workflows/{workflow_id}")

    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Dict:
        """Update an existing workflow in n8n"""
        return self._make_request("PUT", f"workflows/{workflow_id}", workflow_data)

    def delete_workflow(self, workflow_id: str) -> None:
        """Delete a workflow from n8n"""
        self._make_request("DELETE", f"workflows/{workflow_id}")

    def activate_workflow(self, workflow_id: str) -> Dict:
        """Activate a workflow in n8n"""
        return self._make_request("POST", f"workflows/{workflow_id}/activate")

    def deactivate_workflow(self, workflow_id: str) -> Dict:
        """Deactivate a workflow in n8n"""
        return self._make_request("POST", f"workflows/{workflow_id}/deactivate")

    def execute_workflow(self, workflow_id: str, execution_data: Optional[Dict] = None) -> Dict:
        """Execute a workflow immediately"""
        return self._make_request("POST", f"workflows/{workflow_id}/execute", execution_data or {})

    def get_execution_data(self, execution_id: str) -> Dict:
        """Get execution details of a workflow run"""
        return self._make_request("GET", f"executions/{execution_id}")

    def get_active_workflows(self) -> List[Dict]:
        """Get all active workflows"""
        return self._make_request("GET", "workflows/active")

    def get_workflow_executions(self, workflow_id: str, limit: int = 20) -> List[Dict]:
        """Get execution history of a workflow"""
        return self._make_request("GET", f"workflows/{workflow_id}/executions?limit={limit}")
