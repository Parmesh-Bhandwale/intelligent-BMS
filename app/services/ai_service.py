import httpx
from app.core.config import settings

class AIService:
    def __init__(self):
        self.api_url = "http://localhost:11434/api/generate" # Default Ollama URL

    async def generate_book_summary(self, title: str, content: str) -> str:
        prompt = f"Summarize the following book titled '{title}': {content}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={"model": "llama3", "prompt": prompt, "stream": False},
                timeout=60.0
            )
            result = response.json()
            return result.get("response", "Summary generation failed.")

    async def get_recommendations(self, preferences: str, book_list: list) -> str:
        # Business logic for comparing user preferences against database
        pass
    
    import asyncio
import logging
from app.utils.exceptions import InternalServerException

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    async def generate_summary(text: str) -> str:
        logger.info("AI summary generation started")
        try:
            await asyncio.sleep(0.3)
            return f"AI Summary for: {text[:80]}"
        except Exception:
            logger.exception("AI summary generation failed")
            raise InternalServerException("AI service failed")
