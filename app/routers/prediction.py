from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pandas as pd
from typing import Optional
import json
import markdown2

from app.database.database import get_db
from app.database.models import User, Prediction
from app.utils.auth import get_current_user
from app.models.predictor import run_prediction
from app.utils.helper import clean_text
from app.config import Config

router = APIRouter(tags=["Prediction"])

# Templates
templates = Jinja2Templates(directory="app/templates")

# Cache for company data
companies_df = None

def get_company_data():
    """Get company data from CSV file and cache it"""
    global companies_df
    if companies_df is None:
        companies_df = pd.read_csv(Config.DATA_PATH)
    return companies_df

def render_markdown_to_html(markdown_text):
    """Convert markdown text to HTML"""
    if not markdown_text:
        return ""
    
    # Add extra extensions for better rendering
    html = markdown2.markdown(
        markdown_text,
        extras=[
            "tables",
            "break-on-newline",
            "cuddled-lists",
            "fenced-code-blocks"
        ]
    )
    return html

@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Home page with prediction form"""
    # Get company data
    try:
        df = get_company_data()
        companies = df["company_name"].unique().tolist()
        
        return templates.TemplateResponse(
            "home.html", 
            {
                "request": request, 
                "companies": companies,
                "username": current_user.username
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "home.html", 
            {
                "request": request,
                "error": f"Error loading company data: {str(e)}",
                "companies": [],
                "username": current_user.username
            }
        )

@router.get("/api/company/{company_name}")
async def get_company_details(
    company_name: str, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """API endpoint to get company details"""
    df = get_company_data()
    company = df[df['company_name'] == company_name]
    
    if company.empty:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Convert to dict
    company_data = company.iloc[0].to_dict()
    
    # Clean text fields
    for field in ['description', 'products_and_services']:
        if field in company_data:
            company_data[field] = clean_text(company_data[field])
    
    return company_data

@router.post("/predict", response_class=HTMLResponse)
async def predict(
    request: Request,
    company_name: str = Form(...),
    impact_area_community: float = Form(...),
    impact_area_environment: float = Form(...),
    impact_area_customers: float = Form(...),
    impact_area_governance: float = Form(...),
    certification_cycle: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle prediction form submission"""
    try:
        # Get company details
        df = get_company_data()
        company = df[df['company_name'] == company_name]
        
        if company.empty:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_details = company.iloc[0].to_dict()
        
        # Clean text fields
        for field in ['description', 'products_and_services']:
            if field in company_details:
                company_details[field] = clean_text(company_details[field])
        
        # Run prediction
        result = run_prediction(
            impact_area_community=impact_area_community,
            impact_area_environment=impact_area_environment,
            impact_area_customers=impact_area_customers,
            impact_area_governance=impact_area_governance,
            certification_cycle=certification_cycle,
            company_details=company_details
        )
        
        # Save prediction to database
        new_prediction = Prediction(
            user_id=current_user.id,
            company_name=company_name,
            impact_area_community=impact_area_community,
            impact_area_environment=impact_area_environment,
            impact_area_customers=impact_area_customers,
            impact_area_governance=impact_area_governance,
            certification_cycle=certification_cycle,
            esg_score=result["esg_score"],
            risk_probability=result["risk_probability"],
            llm_response=result["llm_report"]
        )
        
        db.add(new_prediction)
        db.commit()
        db.refresh(new_prediction)
        
        # Return page with result
        return templates.TemplateResponse(
            "result.html", 
            {
                "request": request,
                "company_name": company_name,
                "esg_score": result["esg_score"],
                "risk_probability": result["risk_probability"],
                "llm_report": render_markdown_to_html(result["llm_report"]),
                "llm_error": result.get("llm_error"),
                "username": current_user.username
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "home.html", 
            {
                "request": request,
                "error": f"Prediction error: {str(e)}",
                "companies": get_company_data()["company_name"].unique().tolist(),
                "username": current_user.username
            }
        )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """User dashboard showing prediction history"""
    # Get user's predictions
    predictions = db.query(Prediction).filter(Prediction.user_id == current_user.id).order_by(Prediction.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "predictions": predictions,
            "username": current_user.username
        }
    )

@router.delete("/api/prediction/{prediction_id}")
async def delete_prediction(
    prediction_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API endpoint to delete a prediction"""
    # Get prediction
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Check if prediction belongs to current user
    if prediction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this prediction")
    
    # Delete prediction
    db.delete(prediction)
    db.commit()
    
    return {"message": "Prediction deleted successfully"}

@router.get("/api/prediction/{prediction_id}")
async def get_prediction_details(
    prediction_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API endpoint to get prediction details"""
    # Get prediction
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Check if prediction belongs to current user
    if prediction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this prediction")
    
    # Convert to dict
    prediction_data = {
        "id": prediction.id,
        "company_name": prediction.company_name,
        "impact_area_community": prediction.impact_area_community,
        "impact_area_environment": prediction.impact_area_environment,
        "impact_area_customers": prediction.impact_area_customers,
        "impact_area_governance": prediction.impact_area_governance,
        "certification_cycle": prediction.certification_cycle,
        "esg_score": prediction.esg_score,
        "risk_probability": prediction.risk_probability,
        "llm_response": render_markdown_to_html(prediction.llm_response),
        "created_at": prediction.created_at.isoformat()
    }
    
    return prediction_data 