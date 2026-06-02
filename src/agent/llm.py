import logging
from typing import List, Dict, Any, Optional
try:
    import ollama
except ImportError:
    ollama = None

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Standardized client proxy for Ollama Llama 3.1:8b used in reasoning loops
    and memory consolidation.
    """
    def __init__(self, default_model: str = "llama3.1:8b"):
        self.default_model = default_model
        if not ollama:
            logger.warning("ollama package not installed. LLM features will fail.")

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """
        Send a chat completion request to the LLM.
        """
        if not ollama:
            return "Error: Ollama client not available."
            
        target_model = model or self.default_model
        try:
            client = ollama.AsyncClient()
            response = await client.chat(model=target_model, messages=messages)
            return response['message']['content']
        except Exception as e:
            logger.error(f"LLM Chat Error: {e}")
            return f"Thinking Error: {str(e)}"
            
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Send a raw completion request (often used for short memory tasks).
        """
        if not ollama:
            return "Error: Ollama client not available."
            
        target_model = model or self.default_model
        try:
            client = ollama.AsyncClient()
            response = await client.generate(model=target_model, prompt=prompt)
            return response['response']
        except Exception as e:
            logger.error(f"LLM Generate Error: {e}")
            return f"Generation Error: {str(e)}"
