import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import google.generativeai as genai

class BaseAgent(ABC):
    """
    Base abstract class for all agents in the system.
    Provides common functionality and required method signatures.
    """
    
    def __init__(self, gemini_client, generation_config=None):
        """
        Initialize the base agent with a Gemini client.
        
        Args:
            gemini_client: The initialized Gemini client
            generation_config: Optional configuration for generation
        """
        self.gemini_client = gemini_client
        self.generation_config = generation_config or {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-thinking-exp-01-21",
            generation_config=self.generation_config
        )
        self.context = {}
        logging.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def process_query(self, query: str, chat_memory: Any = None) -> str:
        """
        Process a query from the user.
        
        Args:
            query: The user's query string
            chat_memory: Optional chat memory object
            
        Returns:
            The response string
        """
        pass
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response using the Gemini model.
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt to provide context
            
        Returns:
            The generated response string
        """
        try:
            # Create chat session if system prompt is provided
            if system_prompt:
                chat = self.model.start_chat(history=[
                    {"role": "system", "content": system_prompt}
                ])
                response = chat.send_message(prompt)
            else:
                response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"
    
    def update_context(self, key: str, value: Any) -> None:
        """
        Update the agent's context with new information.
        
        Args:
            key: The context key
            value: The context value
        """
        self.context[key] = value
        logging.debug(f"Updated context: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the agent's context.
        
        Args:
            key: The context key
            default: Default value if key not found
            
        Returns:
            The context value or default
        """
        return self.context.get(key, default)
    
    def format_prompt(self, prompt_template: str, **kwargs) -> str:
        """
        Format a prompt template with provided values.
        
        Args:
            prompt_template: The prompt template string
            **kwargs: Values to fill in the template
            
        Returns:
            The formatted prompt string
        """
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logging.error(f"Missing key in prompt template: {e}")
            return prompt_template