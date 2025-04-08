from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
    
    # LLM Response - stored as text
    llm_response = Column(Text)
    
    # Relationship
    user = relationship("User", back_populates="predictions") 