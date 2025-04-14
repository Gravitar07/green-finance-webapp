import numpy as np
import os
import joblib
import logging
import traceback
from app.config import Config
from app.utils.exceptions import log_exception, ModelLoadingError, PreprocessingError, PredictionError
from app.utils.helper import calculate_esg
from app.models.llm import LLM

logger = logging.getLogger(__name__)

# Store loaded models
models = {}

def initialize_models():
    """Initialize and load ML models from disk"""
    try:
        scaler_path = os.path.join(Config.MODELS_PATH, "scaler_object.joblib")
        ml_model_path = os.path.join(Config.MODELS_PATH, "random_forest.joblib")
        
        # Print the actual paths for debugging
        logger.info(f"Loading models from: {scaler_path} and {ml_model_path}")
        
        if os.path.exists(scaler_path) and os.path.exists(ml_model_path):
            models["scaler"] = joblib.load(scaler_path)
            models["ml_model"] = joblib.load(ml_model_path)
            logger.info("Models initialized successfully.")
            return True
        else:
            missing_files = []
            if not os.path.exists(scaler_path):
                missing_files.append(scaler_path)
            if not os.path.exists(ml_model_path):
                missing_files.append(ml_model_path)
            
            error_msg = f"Model files not found: {', '.join(missing_files)}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
    except Exception as e:
        error_msg = f"Error loading models: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise e

class DataPreprocessor:
    def __init__(self):
        try:
            self.scaler = models.get("scaler")
            if not self.scaler:
                raise ModelLoadingError("Scaler not initialized. Call initialize_models() first.")
            logger.info("Scaler loaded successfully.")
        except Exception as e:
            log_exception(e, "Error loading scaler in DataPreprocessor.")
            raise ModelLoadingError("Could not load the scaler for data preprocessing.")
        
    def preprocess(self, input_data):
        try:
            logger.info(f"Preprocessing data: {input_data}")
            scaled_data = self.scaler.transform(np.array(input_data).reshape(1, -1))
            logger.info("Data preprocessing completed successfully.")
            return scaled_data
        except Exception as e:
            error_msg = f"Error in preprocessing data: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise PreprocessingError(f"Preprocessing failed: {str(e)}") from e
        
class MLModelPredictor:
    def __init__(self):
        try:
            self.model = models.get("ml_model")
            if not self.model:
                raise ModelLoadingError("ML model not initialized. Call initialize_models() first.")
            logger.info("ML model loaded successfully.")
        except Exception as e:
            log_exception(e, "Failed to load ML model in MLModelPredictor.")
            raise ModelLoadingError("Could not load ML model. Please check model path and format.") from e

    def predict(self, preprocessed_data):
        try:
            logger.info(f"Making prediction with data shape: {preprocessed_data.shape}")
            prediction = self.model.predict_proba(preprocessed_data)
            logger.info(f"ML model prediction result: {prediction}")
            return prediction
        except Exception as e:
            error_msg = f"Error during ML model prediction: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise PredictionError(f"Prediction failed: {str(e)}") from e

def run_prediction(
    impact_area_community, 
    impact_area_environment, 
    impact_area_customers, 
    impact_area_governance, 
    certification_cycle, 
    company_details
):
    """
    Runs the full prediction pipeline for green finance risk analysis
    
    Args:
        impact_area_community (float): Community impact score
        impact_area_environment (float): Environment impact score
        impact_area_customers (float): Customers impact score
        impact_area_governance (float): Governance impact score
        certification_cycle (int): Certification cycle value
        company_details (dict): Dictionary containing company details
        
    Returns:
        dict: Dictionary containing prediction results
    """
    llm_report = None
    llm_error = None
    
    try:
        logger.info(f"Starting prediction for company: {company_details.get('company_name', 'Unknown')}")
        
        # Initialize classes
        preprocessor = DataPreprocessor()
        ml_predictor = MLModelPredictor()
        
        # Prepare structured data input for ML model
        structured_data = [
            impact_area_community, 
            impact_area_customers, 
            impact_area_environment, 
            impact_area_governance, 
            certification_cycle
        ]
        
        logger.info(f"Input data: {structured_data}")
        
        # Preprocess the data
        preprocessed_data = preprocessor.preprocess(structured_data)
        
        # Get predictions from ML model
        # ml_prediction_result = ml_predictor.predict(preprocessed_data)
        # risk_probability = float(ml_prediction_result[0][1])  # Class 1 probability
        # logger.info(f"Risk probability: {risk_probability}")
        
        # Calculate ESG score
        esg_score = calculate_esg(
            impact_area_environment, 
            impact_area_community, 
            impact_area_governance,
            Config.ESG_WEIGHTS
        )
        logger.info(f"ESG score: {esg_score}")

        # Derive risk probability from ESG score
        risk_probability = max(0.0, min(1.0, (100 - esg_score) / 100))
        logger.info(f"Calculated risk probability from ESG score: {risk_probability}")
        
        # Format raw input for LLM
        input_raw_data = f"""
Company Name: {company_details.get('company_name', 'Unknown')}
Place: {company_details.get('country', 'Unknown')}  
Industry Category: {company_details.get('industry_category', 'Unknown')}  
Sector: {company_details.get('sector', 'Unknown')}  
Industry: {company_details.get('industry', 'Unknown')}  
Products and Services: {company_details.get('products_and_services', 'Unknown')}  
Description: {company_details.get('description', 'Unknown')}
Impact Area Community Value: {impact_area_community}
Impact Area Environment Value: {impact_area_environment}
Impact Area Customers Value: {impact_area_customers}
Impact Area Governance Value: {impact_area_governance}
Certification Cycle: {certification_cycle}
        """
        
        # Prepare result for LLM
        result_for_llm = f"""
        Green Finance Report:

        **ESG Score:** {esg_score}
        
        **ML Model Risk Probability:** {risk_probability}
        
        {input_raw_data}
        """
        
        # Try to get LLM report, but continue even if it fails
        try:
            llm = LLM()
            llm_report = llm.inference(result=result_for_llm)
            logger.info("LLM report generated successfully.")
        except Exception as e:
            llm_error = str(e)
            logger.error(f"Error generating LLM report: {llm_error}")
            logger.error(traceback.format_exc())
            # Create a basic report if LLM fails
            llm_report = f"""
            ### {company_details.get('company_name', 'Unknown')} - Green Finance Report
            
            **Note:** This is a simplified report due to an error in the LLM service.
            
            #### ESG Score: {esg_score:.2f}
            #### Risk Probability: {risk_probability:.2%}
            
            Please try again later for a complete analysis.
            """
        
        # Return complete results
        return {
            "esg_score": esg_score,
            "risk_probability": risk_probability,
            "llm_report": llm_report,
            "llm_error": llm_error
        }
    
    except Exception as e:
        error_msg = f"Error in prediction function: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise PredictionError(error_msg) from e 