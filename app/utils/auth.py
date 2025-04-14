from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.config import Config
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password encryption context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token - for API authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)

def verify_password(plain_password, hashed_password):
    """
    Verify if the plain password matches the hashed password
    """
    result = pwd_context.verify(plain_password, hashed_password)
    logger.info(f"Password verification result: {result}")
    return result

def get_password_hash(password):
    """
    Generate a hash from the given password
    """
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate user by username and password
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        User model if authentication successful, None otherwise
    """
    logger.info(f"Attempting to authenticate user: {username}")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password for user: {username}")
        return None
    logger.info(f"User authenticated successfully: {username}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token for the user
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    logger.info(f"Creating access token for data: {data}")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    logger.info("Access token created successfully")
    return encoded_jwt

def get_token_from_cookie(request: Request):
    """
    Extract token from cookie
    
    Args:
        request: FastAPI request object
        
    Returns:
        Token string if found, None otherwise
    """
    token = request.cookies.get("access_token")
    logger.info(f"Token from cookie: {'Found' if token else 'Not found'}")
    if not token:
        return None
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
        logger.info("Removed 'Bearer ' prefix from token")
    return token

async def get_current_user(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user from JWT token
    """
    logger.info("Attempting to get current user")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First try to get token from cookie (for web UI)
    cookie_token = get_token_from_cookie(request)
    logger.info(f"Cookie token: {'Found' if cookie_token else 'Not found'}")
    
    # Use token from cookie or header
    final_token = cookie_token or token
    logger.info(f"Final token: {'Found' if final_token else 'Not found'}")
    
    if not final_token:
        logger.error("No token found in cookie or header")
        raise credentials_exception

    try:
        logger.info("Attempting to decode JWT token")
        payload = jwt.decode(final_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("No username found in token payload")
            raise credentials_exception
        logger.info(f"Token decoded successfully for user: {username}")
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logger.error(f"User not found in database: {username}")
        raise credentials_exception
    
    if not user.is_active:
        logger.error(f"User account is not active: {username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    logger.info(f"User found and authenticated: {username}")
    return user 