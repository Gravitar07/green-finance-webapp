from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    predictions = relationship("Prediction", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String)
    impact_area_community = Column(Float)
    impact_area_environment = Column(Float)
    impact_area_customers = Column(Float)
    impact_area_governance = Column(Float)
    certification_cycle = Column(Integer)
    esg_score = Column(Float)
    risk_probability = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # LLM Response - stored as text
    llm_response = Column(Text)
    
    # Relationship
    user = relationship("User", back_populates="predictions") 