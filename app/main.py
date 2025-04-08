from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os
import logging

from app.database.database import engine
from app.database.models import Base, User
from app.models.predictor import initialize_models
from app.routers import auth, prediction
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="Green Finance Risk Prediction")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "images"), exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize models on startup
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Starting application...")
        
        # Print configuration
        logger.info("Printing configuration...")
        Config.print_config()
        
        # Initialize models
        logger.info("Initializing models...")
        initialize_models()
        logger.info("Models initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.error("Application may not function correctly due to startup errors")

# Include routers
app.include_router(auth.router)
app.include_router(prediction.router)

@app.get("/")
async def root():
    """Root endpoint, redirects to login page"""
    return RedirectResponse(url="/login")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 