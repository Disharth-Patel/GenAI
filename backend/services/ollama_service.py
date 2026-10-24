import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests

logger = logging.getLogger("ollama_service")

class OllamaService:
    """
    Manages local open-weight LLM inference via Ollama runtime.
    Features:
    - Zero paid cloud API dependencies
    - Configurable model selection (e.g., llama3.2:3b, llama3.2:latest, qwen2.5:3b)
    - Health & availability probing with clear status codes
    - Exact token counting & tokens-per-second measurement via Ollama metrics
    - Non-crashing graceful degradation
    """

    def __init__(self):
        raw_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.base_url = raw_url.replace("localhost", "127.0.0.1")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2:latest").strip()
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
        self.session = requests.Session()

    def check_health(self) -> Dict[str, Any]:
        """
        Check whether Ollama runtime is reachable and if the target model is installed.
        Returns a rich status dict with actionable setup instructions if unavailable.
        """
        try:
            res = self.session.get(f"{self.base_url}/api/tags", timeout=4.0)
            if res.status_code != 200:
                return {
                    "available": False,
                    "status": "error",
                    "code": "BAD_RESPONSE",
                    "message": f"Ollama returned HTTP {res.status_code}",
                    "active_model": self.model_name,
                    "installed_models": [],
                    "instruction": f"Restart Ollama or verify port 11434."
                }

            data = res.json()
            models = data.get("models", [])
            model_names = [m.get("name") for m in models if m.get("name")]

            # Check if active model exists (exact match or tag prefix)
            target = self.model_name.lower()
            model_installed = any(
                m.lower() == target or m.lower().startswith(f"{target}:") or target.startswith(f"{m.lower().split(':')[0]}:")
                for m in model_names
            )

            if model_installed:
                return {
                    "available": True,
                    "status": "ready",
                    "code": "READY",
                    "message": f"Ollama runtime ready with model '{self.model_name}'",
                    "active_model": self.model_name,
                    "installed_models": model_names,
                    "instruction": "Local LLM is active and ready for inference."
                }
            else:
                return {
                    "available": False,
                    "status": "model_missing",
                    "code": "MODEL_NOT_FOUND",
                    "message": f"Ollama is running, but model '{self.model_name}' is not downloaded yet.",
                    "active_model": self.model_name,
                    "installed_models": model_names,
                    "instruction": f"Run 'ollama pull {self.model_name}' in your terminal to download the model."
                }
        except requests.exceptions.ConnectionError:
            return {
                "available": False,
                "status": "offline",
                "code": "OLLAMA_STOPPED",
                "message": f"Cannot connect to Ollama on {self.base_url}. Service is not running.",
                "active_model": self.model_name,
                "installed_models": [],
                "instruction": f"Start the Ollama application or run 'ollama serve' in your terminal."
            }
        except Exception as e:
            return {
                "available": False,
                "status": "error",
                "code": "UNKNOWN_ERROR",
                "message": f"Error probing Ollama: {str(e)}",
                "active_model": self.model_name,
                "installed_models": [],
                "instruction": f"Verify Ollama installation and logs."
            }

    def generate_chat(
        self,
        system_instruction: str,
        context_text: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: str = "en",
        temperature: float = 0.3,
        max_tokens: int = 350
    ) -> Optional[Dict[str, Any]]:
        """
        Execute chat inference using Ollama API with grounded RAG context.
        Returns a dict containing response text, metrics (latency, tokens, tps),
        or None if Ollama inference fails.
        """
        messages = []

        # System prompt with retrieved context
        system_content = (
            f"{system_instruction}\n\n"
            f"[Grounded Knowledge Base Context]\n"
            f"{context_text}\n\n"
            f"Instructions:\n"
            f"- Answer the user's question accurately using the context above.\n"
            f"- Respond in the detected/requested language.\n"
            f"- If official links are present in the context, mention them."
        )
        messages.append({"role": "system", "content": system_content})

        # Append recent conversation history
        if conversation_history:
            for h in conversation_history[-6:]:
                role = "user" if h.get("role") == "user" else "assistant"
                text = h.get("text", "").strip()
                if text:
                    messages.append({"role": role, "content": text})

        # Append current user prompt
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "num_ctx": 2048,
            }
        }

        t_start = time.perf_counter()
        try:
            res = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            total_latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

            if res.status_code != 200:
                logger.warning(f"Ollama returned HTTP {res.status_code}: {res.text}")
                return None

            data = res.json()
            message_obj = data.get("message", {})
            content = message_obj.get("content", "").strip()

            if not content:
                return None

            prompt_tokens = data.get("prompt_eval_count") or 0
            completion_tokens = data.get("eval_count") or 0
            total_tokens = prompt_tokens + completion_tokens

            eval_duration_ns = data.get("eval_duration") or 0
            eval_duration_sec = eval_duration_ns / 1e9 if eval_duration_ns > 0 else (total_latency_ms / 1000.0)
            tokens_per_sec = round(completion_tokens / eval_duration_sec, 2) if (completion_tokens > 0 and eval_duration_sec > 0) else 0.0

            return {
                "content": content,
                "model": self.model_name,
                "latency_ms": total_latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_second": tokens_per_sec,
                "cost_est_usd": 0.0, # Completely free local inference!
                "provider": "ollama"
            }
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            return None


# Singleton instance
ollama_service = OllamaService()
