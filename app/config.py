import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_NAME = "llama3-70b-8192"
    
    # File Paths - Use absolute paths to avoid issues
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MODELS_PATH = os.path.join(BASE_DIR, "final_models")
    DATA_PATH = os.path.join(BASE_DIR, "data", "unique_companies_dataset.csv")
    
    # Database Settings
    DATABASE_URL = "sqlite:///./green_finance.db"
    
    # ESG Weights
    ESG_WEIGHTS = {
        "environment": 0.5,
        "social": 0.3,
        "governance": 0.2
    }
    
    # Security settings
    SECRET_KEY = "green_finance_secure_key_for_jwt_tokens"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Print configuration for debugging
    @classmethod
    def print_config(cls):
        print(f"BASE_DIR: {cls.BASE_DIR}")
        print(f"MODELS_PATH: {cls.MODELS_PATH}")
        print(f"DATA_PATH: {cls.DATA_PATH}")
        print(f"GROQ_API_KEY: {'Set' if cls.GROQ_API_KEY else 'Not set'}")
        print(f"GROQ_MODEL_NAME: {cls.GROQ_MODEL_NAME}")
        
        # Check if model files exist
        print(f"\nChecking if model files exist:")
        scaler_path = os.path.join(cls.MODELS_PATH, "scaler_object.joblib")
        ml_model_path = os.path.join(cls.MODELS_PATH, "random_forest.joblib")
        print(f"Scaler path: {scaler_path} - Exists: {os.path.exists(scaler_path)}")
        print(f"ML model path: {ml_model_path} - Exists: {os.path.exists(ml_model_path)}")
        
        # Check if data file exists
        print(f"\nChecking if data file exists:")
        print(f"Data path: {cls.DATA_PATH} - Exists: {os.path.exists(cls.DATA_PATH)}") 