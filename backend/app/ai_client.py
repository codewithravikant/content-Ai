import os
import logging
from typing import Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import asyncio

logger = logging.getLogger(__name__)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY not set. AI generation will fail.")
elif api_key.startswith("AIza"):
    logger.error(
        "Invalid API key format detected. The key appears to be a Google API key (starts with 'AIza'). "
        "OpenAI API keys should start with 'sk-' or 'sk-proj-'. "
        "Please get your OpenAI API key from https://platform.openai.com/account/api-keys"
    )
    raise ValueError(
        "Invalid API key: OpenAI API keys must start with 'sk-' or 'sk-proj-'. "
        "You provided a key that starts with 'AIza' which appears to be a Google API key. "
        "Get your OpenAI API key from: https://platform.openai.com/account/api-keys"
    )
elif not (api_key.startswith("sk-") or api_key.startswith("sk-proj-")):
    logger.warning(
        f"API key format may be incorrect. OpenAI keys typically start with 'sk-' or 'sk-proj-'. "
        f"Your key starts with: {api_key[:4]}..."
    )

client = AsyncOpenAI(api_key=api_key) if api_key else None


class AIClient:
    """AI client for content generation with retry logic and streaming support."""
    
    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.timeout = int(os.getenv("AI_TIMEOUT", "60"))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def generate_stream(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate content using AI with streaming support.
        Includes retry logic with exponential backoff.
        """
        if not client:
            raise Exception("OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": prompt_data["system_prompt"]},
                {"role": "user", "content": prompt_data["user_prompt"]},
            ]
            
            # Get generation parameters
            gen_params = request.generation_params or {}
            temperature = gen_params.temperature if hasattr(gen_params, 'temperature') else 0.7
            max_tokens = gen_params.max_tokens if hasattr(gen_params, 'max_tokens') else 2000
            top_p = gen_params.top_p if hasattr(gen_params, 'top_p') else 0.9
            
            logger.info(f"Calling AI model: {self.model}, temperature: {temperature}, max_tokens: {max_tokens}")
            
            # Call OpenAI API with streaming
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
                timeout=self.timeout,
            )
            
            # Collect streamed content
            full_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_content += chunk.choices[0].delta.content
            
            # Get token usage from last chunk (if available)
            tokens_used = None
            if hasattr(chunk, 'usage') and chunk.usage:
                tokens_used = chunk.usage.total_tokens
            
            logger.info(f"AI generation completed. Content length: {len(full_content)}, Tokens: {tokens_used}")
            
            return {
                "content": full_content.strip(),
                "metadata": {
                    "tokens_used": tokens_used,
                    "model": self.model,
                },
            }
            
        except Exception as e:
            logger.error(f"AI generation error: {e}", exc_info=True)
            raise
    
    async def generate_stream_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Generate content in chunks for SSE streaming.
        Yields content chunks as they are generated.
        """
        if not client:
            raise Exception("OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": prompt_data["system_prompt"]},
                {"role": "user", "content": prompt_data["user_prompt"]},
            ]
            
            # Get generation parameters
            gen_params = request.generation_params or {}
            temperature = gen_params.temperature if hasattr(gen_params, 'temperature') else 0.7
            max_tokens = gen_params.max_tokens if hasattr(gen_params, 'max_tokens') else 2000
            top_p = gen_params.top_p if hasattr(gen_params, 'top_p') else 0.9
            
            logger.info(f"Starting streaming generation: {self.model}")
            
            # Call OpenAI API with streaming
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
                timeout=self.timeout,
            )
            
            # Yield chunks as they arrive
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    await asyncio.sleep(0)  # Yield control to event loop
            
            logger.info("Streaming generation completed")
            
        except Exception as e:
            logger.error(f"Streaming generation error: {e}", exc_info=True)
            raise
