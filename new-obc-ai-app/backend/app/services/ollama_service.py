import httpx
import logging
from typing import Optional, Generator, Any
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger("ollama_service")

class OllamaService:
    """
    Service to handle interactions with the local Ollama LLM runtime.
    """
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    async def check_health(self) -> bool:
        """Verifies if the Ollama service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> Any:
        """
        Generates a response from the local LLM.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 1024,
            }
        }

        if system_prompt:
            # Note: For /api/generate, system prompt is often part of the prompt
            # or handled via the /api/chat endpoint. We will use /api/chat for
            # better conversation support in the next iteration, but for core
            # connectivity, we implement /api/generate.
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    return self._stream_response(client, url, payload)
                else:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json().get("response", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.text}")
            raise HTTPException(status_code=502, detail=f"Ollama runtime returned error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error communicating with Ollama: {e}")
            raise HTTPException(status_code=503, detail="Ollama service is unavailable")

    async def _stream_response(self, client: httpx.AsyncClient, url: str, payload: dict) -> Generator[str, None, None]:
        """Handles streaming responses from Ollama."""
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

ollama_service = OllamaService()
