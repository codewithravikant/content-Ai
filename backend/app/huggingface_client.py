import os
import logging
import json
from typing import Dict, Any, AsyncGenerator
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import asyncio

logger = logging.getLogger(__name__)

# Hugging Face API configuration
hf_api_key = os.getenv("HF_API_KEY")
hf_model = os.getenv("HF_MODEL", "google/flan-t5-large")
# HF now requires router.huggingface.co instead of api-inference.huggingface.co
hf_base_url = os.getenv("HF_BASE_URL", "https://router.huggingface.co")
hf_timeout = int(os.getenv("HF_TIMEOUT", "120"))  # Default 120 seconds

# Debug logging (written to NDJSON file). Do not log secrets.
_DEBUG_LOG_PATH = "/Users/ravikantpandit/codewithravi/Content-AI/.cursor/debug.log"
_DEBUG_SESSION = "debug-session"
_DEBUG_RUN = "run1"


def _agent_log(hypothesis_id: str, location: str, message: str, data: Dict[str, Any]) -> None:
    """Append a small NDJSON log for debug mode; ignore all errors."""
    try:
        with open(_DEBUG_LOG_PATH, "a") as f:
            f.write(
                json.dumps(
                    {
                        "sessionId": _DEBUG_SESSION,
                        "runId": _DEBUG_RUN,
                        "hypothesisId": hypothesis_id,
                        "location": location,
                        "message": message,
                        "data": data,
                        "timestamp": int(asyncio.get_event_loop().time() * 1000),
                    }
                )
                + "\n"
            )
    except Exception:
        pass


class HuggingFaceClient:
    """Hugging Face Inference API client for content generation with retry logic and streaming support."""
    
    def __init__(self):
        if not hf_api_key:
            logger.warning("HF_API_KEY not set. Hugging Face client will not work.")
        self.api_key = hf_api_key
        self.model = hf_model
        self.base_url = hf_base_url.rstrip("/")
        self.timeout = hf_timeout
        self.api_url = f"{self.base_url}/models/{self.model}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def generate_stream(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate content using Hugging Face Inference API.
        Combines system and user prompts into a single prompt.
        """
        if not self.api_key:
            raise Exception("Hugging Face API key not configured. Set HF_API_KEY environment variable.")
        
        try:
            # region agent log
            _agent_log(
                hypothesis_id="H1",
                location="huggingface_client.py:generate_stream:start",
                message="calling huggingface",
                data={
                    "url": self.api_url,
                    "model": self.model,
                },
            )
            # endregion
            # Combine system and user prompts for Hugging Face (single prompt format)
            combined_prompt = f"{prompt_data['system_prompt']}\n\n{prompt_data['user_prompt']}"
            
            # Get generation parameters
            gen_params = request.generation_params or {}
            temperature = gen_params.temperature if hasattr(gen_params, 'temperature') else 0.7
            max_tokens = gen_params.max_tokens if hasattr(gen_params, 'max_tokens') else 2000
            top_p = gen_params.top_p if hasattr(gen_params, 'top_p') else 0.9
            
            logger.info(f"Calling Hugging Face API: {self.api_url}, temperature: {temperature}, max_tokens: {max_tokens}")
            
            # Prepare request payload for Hugging Face Inference API
            # For text generation models, parameters are optional and format varies by model
            # Start with just inputs, parameters can be added at top level if model supports them
            payload = {
                "inputs": combined_prompt,
            }
            
            # Note: Hugging Face Inference API parameters vary by model
            # Many models support parameters at top level, but format is model-specific
            # For simplicity, we'll send just the inputs (models have reasonable defaults)
            # Advanced users can modify the model or extend this to add parameters
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            # Make request to Hugging Face Inference API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                )
                # region agent log
                _agent_log(
                    hypothesis_id="H1",
                    location="huggingface_client.py:generate_stream:response",
                    message="huggingface response status",
                    data={"status": response.status_code},
                )
                # endregion
                
                # Handle model loading delays (503) with retry
                if response.status_code == 503:
                    error_data = response.json() if response.content else {}
                    estimated_time = error_data.get("estimated_time", 0)
                    logger.warning(f"Model is loading, estimated time: {estimated_time}s")
                    # Retry will be handled by tenacity, but we can raise a specific error
                    raise httpx.HTTPStatusError(
                        "Model is loading, please try again in a few moments",
                        request=response.request,
                        response=response,
                    )
                
                response.raise_for_status()
                result = response.json()
            
            # Extract content from response
            # Hugging Face Inference API returns: [{"generated_text": "..."}]
            content = ""
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    content = result[0].get("generated_text", "")
                else:
                    content = str(result[0])
            elif isinstance(result, dict):
                # Some models might return a different format
                content = result.get("generated_text") or result.get("text") or result.get("content") or ""
            else:
                content = str(result)
            
            logger.info(f"Hugging Face API generation completed. Content length: {len(content)}")
            # region agent log
            _agent_log(
                hypothesis_id="H1",
                location="huggingface_client.py:generate_stream:success",
                message="huggingface success",
                data={"content_length": len(content)},
            )
            # endregion
            
            # Extract token usage if available (HF API doesn't always provide this)
            tokens_used = None
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                tokens_used = result[0].get("tokens_used") or result[0].get("num_tokens")
            
            return {
                "content": content.strip() if isinstance(content, str) else str(content).strip(),
                "metadata": {
                    "tokens_used": tokens_used,
                    "model": self.model,
                },
            }
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_text = e.response.text
            
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", error_text)
            except:
                error_msg = error_text
            
            logger.error(f"Hugging Face API HTTP error: {status_code} - {error_msg}")
            # region agent log
            _agent_log(
                hypothesis_id="H1",
                location="huggingface_client.py:generate_stream:http_error",
                message="huggingface http error",
                data={"status": status_code, "error": error_msg},
            )
            # endregion
            
            # Provide specific error messages for common status codes
            if status_code == 503:
                error_message = f"Hugging Face model is loading (503). Please try again in a few moments. Model: {self.model}"
            elif status_code == 429:
                error_message = f"Hugging Face API rate limit exceeded (429). Please try again later."
            elif status_code == 401:
                error_message = f"Hugging Face API authentication failed (401). Check HF_API_KEY environment variable."
            elif status_code == 404:
                error_message = f"Hugging Face model not found (404). Check HF_MODEL environment variable: {self.model}"
            elif status_code == 500:
                error_message = f"Hugging Face API server error (500). The service may be experiencing issues."
            else:
                error_message = f"Hugging Face API error ({status_code}): {error_msg}"
            
            raise Exception(error_message)
        except httpx.RequestError as e:
            logger.error(f"Hugging Face API request error: {e}")
            # region agent log
            _agent_log(
                hypothesis_id="H1",
                location="huggingface_client.py:generate_stream:request_error",
                message="huggingface request error",
                data={"error": str(e)},
            )
            # endregion
            raise Exception(f"Failed to connect to Hugging Face API: {str(e)}. Check your network connection and HF_API_KEY.")
        except Exception as e:
            logger.error(f"Hugging Face API generation error: {e}", exc_info=True)
            # region agent log
            _agent_log(
                hypothesis_id="H1",
                location="huggingface_client.py:generate_stream:exception",
                message="huggingface exception",
                data={"error": str(e)},
            )
            # endregion
            raise
    
    async def generate_stream_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Generate content in chunks for SSE streaming.
        Note: Hugging Face Inference API doesn't support true streaming,
        so this implementation generates the full response and yields it in chunks.
        """
        if not self.api_key:
            raise Exception("Hugging Face API key not configured. Set HF_API_KEY environment variable.")
        
        try:
            # Generate full content first
            result = await self.generate_stream(request, prompt_data)
            content = result["content"]
            
            # Yield content in chunks (simulate streaming)
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
            
            logger.info("Hugging Face streaming generation completed")
            
        except Exception as e:
            logger.error(f"Hugging Face streaming generation error: {e}", exc_info=True)
            raise


# Initialize Hugging Face client instance
huggingface_client = HuggingFaceClient() if hf_api_key else None
