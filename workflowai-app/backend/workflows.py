from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Workflow
from database import get_db
from auth import get_current_active_user
from pydantic import BaseModel

router = APIRouter()

class WorkflowCreate(BaseModel):
    name: str
    description: str
    n8n_workflow_id: str

class WorkflowUpdate(BaseModel):
    name: str = None
    description: str = None
    is_active: bool = None

class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str
    n8n_workflow_id: str
    is_active: bool
    owner_id: int
    
    class Config:
        orm_mode = True

@router.post("/workflows/", response_model=WorkflowResponse)
def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        n8n_workflow_id=workflow.n8n_workflow_id,
        owner_id=current_user.id
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@router.get("/workflows/", response_model=List[WorkflowResponse])
def read_workflows(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    workflows = db.query(Workflow).filter(Workflow.owner_id == current_user.id).offset(skip).limit(limit).all()
    return workflows

@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
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