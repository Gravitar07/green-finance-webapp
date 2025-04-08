def clean_text(text):
    """
    Helper function to clean and sanitize text by removing unwanted characters and escape sequences.
    
    Args:
        text (str): The input text to clean.
    
    Returns:
        str: The cleaned text.
    """
    if not isinstance(text, str):
        text = str(text)  # Ensure the input is a string
    # Remove unwanted escape sequences and whitespace
    text = text.replace("\n", " ").replace("\r", " ").replace("x000D", "").replace("_", "").strip()
    # Replace multiple spaces with a single space
    text = " ".join(text.split())
    return text

def calculate_esg(impact_area_environment, impact_area_community, impact_area_governance, weights):
    """
    Calculate ESG score based on impact areas and weights.
    
    Args:
        impact_area_environment (float): Environment impact score
        impact_area_community (float): Community/Social impact score
        impact_area_governance (float): Governance impact score
        weights (dict): Dictionary containing weights for each category
        
    Returns:
        float: Calculated ESG score
    """
    esg_score = ((weights['environment'] * impact_area_environment) + 
                 (weights['social'] * impact_area_community) + 
                 (weights['governance'] * impact_area_governance))
    return esg_score 