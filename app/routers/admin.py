from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from app.database.database import get_db
from app.database.models import User, Prediction
from app.utils.auth import get_current_user, create_access_token, verify_password, get_password_hash
from app.utils.helper import clean_text

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")

async def get_current_admin(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Checking admin access for user: {current_user.username}")
    if not current_user.is_admin:
        logger.warning(f"User {current_user.username} attempted to access admin page without admin privileges")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    logger.info(f"Admin access granted for user: {current_user.username}")
    return current_user

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Admin dashboard accessed by: {current_user.username}")
        # Get all users and sort by created_at
        users = db.query(User).order_by(User.created_at.desc()).all()
        
        # Get all predictions and sort by created_at
        predictions = db.query(Prediction).order_by(Prediction.created_at.desc()).all()
        
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "users": users,
                "predictions": predictions,
                "username": current_user.username
            }
        )
    except HTTPException as e:
        logger.error(f"HTTP Exception in admin dashboard: {str(e)}")
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        raise
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while accessing the admin dashboard"
        )

@router.post("/admin/users/create")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Check if user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_admin=is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully"}

@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    username: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
    is_active: bool = Form(None),
    is_admin: bool = Form(None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password is not None:
        user.hashed_password = get_password_hash(password)
    if is_active is not None:
        user.is_active = is_active
    if is_admin is not None:
        user.is_admin = is_admin
    
    db.commit()
    return {"message": "User updated successfully"}

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user's predictions first
    db.query(Prediction).filter(Prediction.user_id == user_id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.get("/admin/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "users": users,
            "username": current_user.username
        }
    )

@router.get("/admin/predictions", response_class=HTMLResponse)
async def list_predictions(
    request: Request,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    predictions = db.query(Prediction).all()
    return templates.TemplateResponse(
        "admin/predictions.html",
        {
            "request": request,
            "predictions": predictions,
            "username": current_user.username
        }
    ) 