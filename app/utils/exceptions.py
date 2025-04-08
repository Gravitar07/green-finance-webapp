import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Custom Exceptions
class ModelLoadingError(Exception):
    """Exception raised when model loading fails."""
    pass

class PreprocessingError(Exception):
    """Exception raised when data preprocessing fails."""
    pass

class PredictionError(Exception):
    """Exception raised when prediction fails."""
    pass

class APIError(Exception):
    """Exception raised when API call fails."""
    pass

def log_exception(exception, message):
    """
    Log exception details with an informative message.
    
    Args:
        exception: The exception object
        message: Contextual message about where/why exception occurred
    """
    logger.error(f"{message} {str(exception)}")
    logger.debug(traceback.format_exc())
    return {"error": message, "detail": str(exception)} 