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

# Determine which AI provider to use
ai_provider = os.getenv("AI_PROVIDER", "openai").lower()

# Initialize OpenAI client (only if using OpenAI)
if ai_provider == "openai":
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
else:
    client = None

# Import Falcon client (only if using Falcon)
if ai_provider == "falcon":
    try:
        from app.falcon_client import falcon_client
        if not falcon_client:
            logger.warning("Falcon client not initialized. Check FALCON_API_BASE_URL environment variable.")
    except ImportError:
        logger.error("Failed to import Falcon client. Make sure falcon_client.py exists.")
        falcon_client = None
else:
    falcon_client = None

logger.info(f"AI Provider configured: {ai_provider}")


class AIClient:
    """AI client for content generation with retry logic and streaming support.
    Supports both OpenAI and Falcon API providers based on AI_PROVIDER environment variable.
    """
    
    def __init__(self):
        self.provider = ai_provider
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Only used for OpenAI
        self.timeout = int(os.getenv("AI_TIMEOUT", "60"))
    
    async def generate_stream(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate content using AI with streaming support.
        Routes to appropriate provider based on AI_PROVIDER setting.
        """
        if self.provider == "openai":
            return await self._generate_openai(request, prompt_data)
        elif self.provider == "falcon":
            return await self._generate_falcon(request, prompt_data)
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}. Supported providers: 'openai', 'falcon'")
    
    async def generate_stream_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Generate content in chunks for SSE streaming.
        Routes to appropriate provider based on AI_PROVIDER setting.
        """
        if self.provider == "openai":
            async for chunk in self._generate_openai_chunks(request, prompt_data):
                yield chunk
        elif self.provider == "falcon":
            async for chunk in self._generate_falcon_chunks(request, prompt_data):
                yield chunk
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}. Supported providers: 'openai', 'falcon'")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def _generate_openai(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content using OpenAI API."""
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
            
            logger.info(f"Calling OpenAI model: {self.model}, temperature: {temperature}, max_tokens: {max_tokens}")
            
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
            
            logger.info(f"OpenAI generation completed. Content length: {len(full_content)}, Tokens: {tokens_used}")
            
            return {
                "content": full_content.strip(),
                "metadata": {
                    "tokens_used": tokens_used,
                    "model": self.model,
                },
            }
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}", exc_info=True)
            raise
    
    async def _generate_openai_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate content in chunks using OpenAI API."""
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
            
            logger.info(f"Starting OpenAI streaming generation: {self.model}")
            
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
            
            logger.info("OpenAI streaming generation completed")
            
        except Exception as e:
            logger.error(f"OpenAI streaming generation error: {e}", exc_info=True)
            raise
    
    async def _generate_falcon(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content using Falcon API."""
        if not falcon_client:
            raise Exception("Falcon client not initialized. Check FALCON_API_BASE_URL environment variable.")
        
        try:
            return await falcon_client.generate_stream(request, prompt_data)
        except Exception as e:
            logger.error(f"Falcon generation error: {e}", exc_info=True)
            raise
    
    async def _generate_falcon_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate content in chunks using Falcon API."""
        if not falcon_client:
            raise Exception("Falcon client not initialized. Check FALCON_API_BASE_URL environment variable.")
        
        try:
            async for chunk in falcon_client.generate_stream_chunks(request, prompt_data):
                yield chunk
        except Exception as e:
            logger.error(f"Falcon streaming generation error: {e}", exc_info=True)
            raise
