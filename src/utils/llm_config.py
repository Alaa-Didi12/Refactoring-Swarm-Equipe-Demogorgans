"""
LLM Configuration and interaction module.
Handles communication with Google Gemini API.
"""
from dotenv import load_dotenv


import os
import google.genai as genai
from typing import Optional
load_dotenv()

class LLMConfig:
    """Configuration and interface for LLM interactions."""
    
    def __init__(self, model_name: str = "models/gemini-2.5-flash"):
        """
        Initialize LLM configuration.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY not found in environment. "
                "Please create a .env file with your API key."
            )
        
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        generation_config = {
            "temperature": temperature,
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            return f"ERROR: LLM generation failed - {str(e)}"
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model_name