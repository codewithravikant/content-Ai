import os
import logging
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

# Falcon API configuration
falcon_base_url = os.getenv("FALCON_API_BASE_URL")
falcon_api_key = os.getenv("FALCON_API_KEY")  # Optional, for authentication if needed
falcon_timeout = int(os.getenv("FALCON_TIMEOUT", "120"))  # Default 120 seconds


class FalconClient:
    """Falcon AI API client for content generation with retry logic and streaming support."""
    
    def __init__(self):
        if not falcon_base_url:
            logger.warning("FALCON_API_BASE_URL not set. Falcon client will not work.")
        self.base_url = falcon_base_url.rstrip('/') if falcon_base_url else None
        self.timeout = falcon_timeout
        self.api_key = falcon_api_key
    
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
        Generate content using Falcon API.
        Combines system and user prompts into a single prompt.
        """
        if not self.base_url:
            raise Exception("Falcon API base URL not configured. Set FALCON_API_BASE_URL environment variable.")
        
        try:
            # Combine system and user prompts for Falcon (simple prompt format)
            # Falcon typically uses a single prompt string
            combined_prompt = f"{prompt_data['system_prompt']}\n\n{prompt_data['user_prompt']}"
            
            # Get generation parameters
            gen_params = request.generation_params or {}
            temperature = gen_params.temperature if hasattr(gen_params, 'temperature') else 0.7
            max_tokens = gen_params.max_tokens if hasattr(gen_params, 'max_tokens') else 2000
            top_p = gen_params.top_p if hasattr(gen_params, 'top_p') else 0.9
            
            logger.info(f"Calling Falcon API: {self.base_url}, temperature: {temperature}, max_tokens: {max_tokens}")
            
            # Prepare request payload (simple prompt format)
            payload = {
                "prompt": combined_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
            }
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Make request to Falcon API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
            
            # Extract content from response
            # Handle different possible response formats
            if isinstance(result, str):
                content = result
            elif isinstance(result, dict):
                # Try common response field names
                content = result.get("text") or result.get("content") or result.get("response") or result.get("output") or ""
                if not content and "choices" in result:
                    # OpenAI-compatible format
                    if result["choices"] and len(result["choices"]) > 0:
                        content = result["choices"][0].get("text") or result["choices"][0].get("message", {}).get("content", "")
            else:
                content = str(result)
            
            logger.info(f"Falcon API generation completed. Content length: {len(content)}")
            
            # Extract token usage if available
            tokens_used = None
            if isinstance(result, dict):
                if "usage" in result:
                    tokens_used = result["usage"].get("total_tokens") if isinstance(result["usage"], dict) else None
                elif "tokens_used" in result:
                    tokens_used = result["tokens_used"]
            
            return {
                "content": content.strip() if isinstance(content, str) else str(content).strip(),
                "metadata": {
                    "tokens_used": tokens_used,
                    "model": "falcon",
                },
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Falcon API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Falcon API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Falcon API request error: {e}")
            raise Exception(f"Failed to connect to Falcon API: {str(e)}")
        except Exception as e:
            logger.error(f"Falcon API generation error: {e}", exc_info=True)
            raise
    
    async def generate_stream_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Generate content in chunks for SSE streaming.
        Note: Falcon API may not support streaming - this implementation
        generates the full response and yields it in chunks.
        """
        if not self.base_url:
            raise Exception("Falcon API base URL not configured. Set FALCON_API_BASE_URL environment variable.")
        
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
            
            logger.info("Falcon streaming generation completed")
            
        except Exception as e:
            logger.error(f"Falcon streaming generation error: {e}", exc_info=True)
            raise


# Initialize Falcon client instance
falcon_client = FalconClient() if falcon_base_url else None
