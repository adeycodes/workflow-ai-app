from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import ExecutionLog, User
from database import get_db
from auth import get_current_active_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class LogResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    execution_time: datetime
    details: str
    
    class Config:
        orm_mode = True

@router.get("/logs/", response_model=List[LogResponse])
def read_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.user_id == current_user.id)
        .order_by(ExecutionLog.execution_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs

@router.get("/logs/{log_id}", response_model=LogResponse)
def read_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    log = db.query(ExecutionLog).filter(
        ExecutionLog.id == log_id,
        ExecutionLog.user_id == current_user.id
    ).first()
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return log
