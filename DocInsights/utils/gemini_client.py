import logging
import google.generativeai as genai
from typing import Dict, Any

def setup_gemini_client(api_key: str) -> Dict[str, Any]:
    """
    Set up the Google Gemini API client.
    
    Args:
        api_key: Google Gemini API key
        
    Returns:
        Client configuration dictionary
    """
    try:
        # Configure the Gemini API with the provided key
        genai.configure(api_key=api_key)
        
        # Get available models
        models = genai.list_models()
        gemini_models = [model for model in models if "gemini" in model.name.lower()]
        
        logging.info(f"Gemini client initialized with {len(gemini_models)} available models")
        
        # Check that Gemini Pro is available
        has_gemini_pro = any("gemini-2.0-flash-thinking-exp-01-21" in model.name.lower() for model in gemini_models)
        if not has_gemini_pro:
            logging.warning("Gemini Pro model not found in available models")
        
        # Create a client configuration dictionary
        client_config = {
            "api_key": "****" + api_key[-4:],  # For logging, only show last 4 chars
            "models": [model.name for model in gemini_models],
            "default_model": "gemini-2.0-flash-thinking-exp-01-21",
            "default_generation_config": {
                "temperature": 0.4
            }
        }
        
        return client_config
        
    except Exception as e:
        logging.error(f"Error initializing Gemini client: {e}")
        raise
