from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    workflows = relationship("Workflow", back_populates="owner")
    logs = relationship("ExecutionLog", back_populates="user")

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    n8n_workflow_id = Column(String)
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="workflows")
    logs = relationship("ExecutionLog", back_populates="workflow")

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)
    execution_time = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)
    
    workflow = relationship("Workflow", back_populates="logs")
    user = relationship("User", back_populates="logs")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    n8n_workflow_id = Column(String)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)