import logging
from typing import Dict, Any, List, Optional

class ChatMemory:
    """
    Class for storing and managing chat history.
    """
    
    def __init__(self, max_history: int = 50):
        """
        Initialize chat memory.
        
        Args:
            max_history: Maximum number of messages to store
        """
        self.messages = []
        self.max_history = max_history
        logging.info(f"ChatMemory initialized with max_history={max_history}")
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the chat history.
        
        Args:
            content: Message content
        """
        message = {
            "role": "user",
            "content": content
        }
        self._add_message(message)
    
    def add_assistant_message(self, content: str) -> None:
        """
        Add an assistant message to the chat history.
        
        Args:
            content: Message content
        """
        message = {
            "role": "assistant",
            "content": content
        }
        self._add_message(message)
    
    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the chat history.
        
        Args:
            content: Message content
        """
        message = {
            "role": "system",
            "content": content
        }
        self._add_message(message)
    
    def _add_message(self, message: Dict[str, str]) -> None:
        """
        Add a message to the chat history.
        
        Args:
            message: Message dictionary with role and content
        """
        self.messages.append(message)
        
        # Trim history if it exceeds the maximum length
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages in the chat history.
        
        Returns:
            List of message dictionaries
        """
        return self.messages
    
    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]:
        """
        Get the last n messages in the chat history.
        
        Args:
            n: Number of messages to get
            
        Returns:
            List of message dictionaries
        """
        return self.messages[-n:] if n < len(self.messages) else self.messages
    
    def get_formatted_history(self, max_messages: Optional[int] = None) -> str:
        """
        Get formatted chat history for prompts.
        
        Args:
            max_messages: Optional limit on number of messages to include
            
        Returns:
            Formatted chat history string
        """
        messages = self.messages
        if max_messages:
            messages = self.get_last_n_messages(max_messages)
        
        formatted_history = ""
        for message in messages:
            role = message["role"].capitalize()
            content = message["content"]
            formatted_history += f"{role}: {content}\n\n"
        
        return formatted_history
    
    def clear(self) -> None:
        """Clear all messages from chat history."""
        self.messages = []
        logging.info("Chat history cleared")
