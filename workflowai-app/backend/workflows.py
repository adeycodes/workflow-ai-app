from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from models import Workflow, ExecutionLog
from database import get_db
from auth import get_current_active_user
from pydantic import BaseModel, Field
from n8n_service import N8NService
from datetime import datetime

router = APIRouter()
n8n = N8NService()

class WorkflowBase(BaseModel):
    name: str
    description: str
    workflow_data: Optional[Dict] = Field(default={}, description="n8n workflow definition")

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    workflow_data: Optional[Dict] = None

class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str
    n8n_workflow_id: str
    is_active: bool
    owner_id: int
    
    class Config:
        orm_mode = True

class ExecutionLogCreate(BaseModel):
    status: str
    details: Optional[str] = None

class ExecutionLogResponse(BaseModel):
    id: int
    workflow_id: int
    user_id: int
    status: str
    execution_time: datetime
    details: Optional[str] = None

    class Config:
        orm_mode = True

@router.post("/workflows/", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        # Create workflow in n8n
        n8n_workflow = n8n.create_workflow({
            "name": workflow.name,
            "nodes": workflow.workflow_data.get("nodes", []),
            "connections": workflow.workflow_data.get("connections", {})
        })
        
        # Create workflow in our database
        db_workflow = Workflow(
            name=workflow.name,
            description=workflow.description,
            n8n_workflow_id=n8n_workflow["id"],
            owner_id=current_user.id
        )
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    except Exception as e:
        # If database operation fails, try to clean up n8n workflow
        if "n8n_workflow" in locals():
            try:
                n8n.delete_workflow(n8n_workflow["id"])
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )

@router.get("/workflows/", response_model=List[WorkflowResponse])
def read_workflows(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    workflows = db.query(Workflow).filter(Workflow.owner_id == current_user.id).offset(skip).limit(limit).all()
    return workflows

@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def read_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Get the workflow
    db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        # Update n8n workflow if workflow_data is provided
        if workflow_update.workflow_data:
            n8n.update_workflow(db_workflow.n8n_workflow_id, {
                "name": workflow_update.name or db_workflow.name,
                "nodes": workflow_update.workflow_data.get("nodes", []),
                "connections": workflow_update.workflow_data.get("connections", {})
            })

        # Update database record
        if workflow_update.name:
            db_workflow.name = workflow_update.name
        if workflow_update.description:
            db_workflow.description = workflow_update.description
        if workflow_update.is_active is not None:
            db_workflow.is_active = workflow_update.is_active
            if workflow_update.is_active:
                n8n.activate_workflow(db_workflow.n8n_workflow_id)
            else:
                n8n.deactivate_workflow(db_workflow.n8n_workflow_id)

        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        # Delete from n8n first
        n8n.delete_workflow(workflow.n8n_workflow_id)
        # Then delete from our database
        db.delete(workflow)
        db.commit()
        return {"message": "Workflow deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    execution_data: Dict = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        # Execute workflow in n8n
        execution = n8n.execute_workflow(workflow.n8n_workflow_id, execution_data)
        
        # Log the execution
        log = ExecutionLog(
            workflow_id=workflow.id,
            user_id=current_user.id,
            status="started",
            details=str(execution)
        )
        db.add(log)
        db.commit()
        
        return {
            "message": "Workflow execution started",
            "execution_id": execution.get("id"),
            "log_id": log.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@router.get("/workflows/{workflow_id}/executions", response_model=List[ExecutionLogResponse])
async def get_workflow_executions(
    workflow_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        # Get executions from both n8n and our database
        n8n_executions = n8n.get_workflow_executions(workflow.n8n_workflow_id, limit)
        
        # Get execution logs from our database
        db_logs = db.query(ExecutionLog).filter(
            ExecutionLog.workflow_id == workflow_id,
            ExecutionLog.user_id == current_user.id
        ).order_by(ExecutionLog.execution_time.desc()).limit(limit).all()
        
        # Update execution logs with n8n status if available
        for log in db_logs:
            for n8n_exec in n8n_executions:
                if str(n8n_exec.get("id")) in log.details:
                    log.status = n8n_exec.get("status", log.status)
                    log.details = str(n8n_exec)
                    db.add(log)
        
        db.commit()
        return db_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow executions: {str(e)}")

@router.get("/workflows/{workflow_id}/executions/{execution_id}", response_model=ExecutionLogResponse)
async def get_execution_details(
    workflow_id: int,
    execution_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if workflow exists and belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get execution log
    execution = db.query(ExecutionLog).filter(
        ExecutionLog.id == execution_id,
        ExecutionLog.workflow_id == workflow_id,
        ExecutionLog.user_id == current_user.id
    ).first()
    
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution log not found")
    
    try:
        # Try to get updated status from n8n
        n8n_execution = n8n.get_execution_data(execution.details.get("id"))
        if n8n_execution:
            execution.status = n8n_execution.get("status", execution.status)
            execution.details = str(n8n_execution)
            db.add(execution)
            db.commit()
    except:
        pass  # If n8n data can't be fetched, return existing log data
    
    return execution

@router.post("/workflows/{workflow_id}/executions/{execution_id}", response_model=ExecutionLogResponse)
async def update_execution_status(
    workflow_id: int,
    execution_id: int,
    log_update: ExecutionLogCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if workflow exists and belongs to user
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get execution log
    execution = db.query(ExecutionLog).filter(
        ExecutionLog.id == execution_id,
        ExecutionLog.workflow_id == workflow_id,
        ExecutionLog.user_id == current_user.id
    ).first()
    
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution log not found")
    
    # Update the execution log
    execution.status = log_update.status
    if log_update.details:
        execution.details = log_update.details
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    return execution
def read_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: int, workflow: WorkflowUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.name is not None:
        db_workflow.name = workflow.name
    if workflow.description is not None:
        db_workflow.description = workflow.description
    if workflow.is_active is not None:
        db_workflow.is_active = workflow.is_active
    
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == current_user.id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(workflow)
    db.commit()
    return {"message": "Workflow deleted successfully"}