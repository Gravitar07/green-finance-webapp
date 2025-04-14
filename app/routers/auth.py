from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.utils.auth import authenticate_user, create_access_token, get_password_hash
from datetime import timedelta
from app.config import Config
from pydantic import BaseModel
from typing import Optional
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

# Templates
templates = Jinja2Templates(directory="app/templates")

# Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Routes for API access
@router.post("/api/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """API endpoint for token acquisition"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/signup")
def signup_api(user_data: UserCreate, db: Session = Depends(get_db)):
    """API endpoint for user registration"""
    # Check if username already exists
    db_username = db.query(User).filter(User.username == user_data.username).first()
    if db_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_email = db.query(User).filter(User.email == user_data.email).first()
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully"}

# Routes for UI
@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page for web UI"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission"""
    try:
        logger.info(f"Login attempt for user: {username}")
        user = authenticate_user(db, username, password)
        if not user:
            logger.warning(f"Failed login attempt for user: {username}")
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Invalid username or password"}
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Set redirect URL based on user role
        redirect_url = "/admin" if user.is_admin else "/home"
        logger.info(f"User {username} logged in successfully, redirecting to: {redirect_url}")
        
        # Redirect with token
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token", 
            value=f"Bearer {access_token}", 
            httponly=True,
            max_age=1800,  # 30 minutes
            samesite="lax",
            secure=False  # Set to False for local development
        )
        return response
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "An error occurred during login"}
        )

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    """Sign up page for web UI"""
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup", response_class=HTMLResponse)
def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle signup form submission"""
    # Check if username already exists
    db_username = db.query(User).filter(User.username == username).first()
    if db_username:
        return templates.TemplateResponse(
            "signup.html", 
            {"request": request, "error": "Username already registered"}
        )
    
    # Check if email already exists
    db_email = db.query(User).filter(User.email == email).first()
    if db_email:
        return templates.TemplateResponse(
            "signup.html", 
            {"request": request, "error": "Email already registered"}
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    
    # Redirect to login page
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
def logout():
    """Handle user logout"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response 