from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Template
from database import get_db
from auth import get_current_active_user, get_current_admin_user
from pydantic import BaseModel

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    description: str
    n8n_workflow_id: str
    category: str

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    n8n_workflow_id: str
    category: str
    
    class Config:
        orm_mode = True

@router.post("/templates/", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    db_template = Template(
        name=template.name,
        description=template.description,
        n8n_workflow_id=template.n8n_workflow_id,
        category=template.category
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates/", response_model=List[TemplateResponse])
def read_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    templates = db.query(Template).offset(skip).limit(limit).all()
    return templates

@router.get("/templates/{template_id}", response_model=TemplateResponse)
def read_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/templates/{template_id}", response_model=TemplateResponse)
def update_template(template_id: int, template: TemplateCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_template.name = template.name
    db_template.description = template.description
    db_template.n8n_workflow_id = template.n8n_workflow_id
    db_template.category = template.category
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}