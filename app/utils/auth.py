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

# Password encryption context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token - for API authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)

def verify_password(plain_password, hashed_password):
    """
    Verify if the plain password matches the hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)

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
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
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
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
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
    if not token:
        return None
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    return token

async def get_current_user(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user from JWT token
    
    Args:
        request: FastAPI request object
        db: Database session
        token: JWT token from OAuth2 scheme (API only)
        
    Returns:
        User object if authentication successful
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First try to get token from cookie (for web UI)
    cookie_token = get_token_from_cookie(request)
    
    # Use token from cookie or header
    final_token = cookie_token or token
    
    if not final_token:
        raise credentials_exception

    try:
        payload = jwt.decode(final_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user 