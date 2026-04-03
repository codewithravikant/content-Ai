import os
import logging
import asyncio
from typing import Any, AsyncGenerator, Dict

from openai import AsyncOpenAI, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _normalize_openrouter_model_id(raw: str) -> str:
    """Fix common .env mistakes. OpenRouter IDs look like `qwen/...` or `openai/gpt-3.5-turbo`, not `openai/qwen/...`."""
    m = (raw or "").strip()
    if m.startswith("openai/qwen/"):
        return m[len("openai/") :]
    return m


def _usage_total_tokens(usage: Any) -> int | None:
    """OpenRouter sometimes returns `usage` as a dict (not a Pydantic object with attributes)."""
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage.get("total_tokens")
    return getattr(usage, "total_tokens", None)


def _build_openrouter_client() -> AsyncOpenAI | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. AI generation will fail.")
        return None

    app_url = os.getenv("APP_URL", "http://localhost:3000")
    app_title = os.getenv("APP_TITLE", "Ghostwriter")
    return AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": app_url,
            "X-Title": app_title,
        },
    )


client = _build_openrouter_client()

# region agent log
try:
    from app.debug_ndjson import dbg as _agent_dbg

    _agent_dbg(
        "H4",
        "ai_client.module_init",
        "openrouter_client_state",
        {"has_client": client is not None, "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")},
    )
except Exception:
    pass
# endregion


def _should_retry_generation(exc: BaseException) -> bool:
    """Retry on 5xx, timeouts, rate limits; do not retry most 4xx (e.g. 402 billing)."""
    if isinstance(exc, APIStatusError):
        code = getattr(exc, "status_code", None)
        if code is None:
            return True
        if code >= 500:
            return True
        if code in (408, 429):
            return True
        return False
    return True


class AIClient:
    """OpenRouter client with retry logic and streaming support."""

    def __init__(self):
        self.provider = "openrouter"
        self.model = _normalize_openrouter_model_id(
            os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        )
        self.timeout = int(os.getenv("AI_TIMEOUT", "60"))
        logger.info("Initialized AIClient with provider: %s, model: %s", self.provider, self.model)

    def _require_client(self) -> AsyncOpenAI:
        if not client:
            raise Exception("OpenRouter client not initialized. Check OPENROUTER_API_KEY environment variable.")
        return client

    @staticmethod
    def _extract_params(request: Any) -> tuple[float, int, float]:
        gen_params = request.generation_params or {}
        temperature = gen_params.temperature if hasattr(gen_params, "temperature") else 0.7
        max_tokens = gen_params.max_tokens if hasattr(gen_params, "max_tokens") else 2000
        top_p = gen_params.top_p if hasattr(gen_params, "top_p") else 0.9
        return temperature, max_tokens, top_p

    async def _generate_openrouter(self, request: Any, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        api = self._require_client()
        temperature, max_tokens, top_p = self._extract_params(request)
        messages = [
            {"role": "system", "content": prompt_data["system_prompt"]},
            {"role": "user", "content": prompt_data["user_prompt"]},
        ]

        logger.info(
            "Calling OpenRouter model: %s, temperature: %s, max_tokens: %s",
            self.model,
            temperature,
            max_tokens,
        )

        stream = await api.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
            timeout=self.timeout,
        )

        full_content = ""
        final_chunk = None
        tokens_used: int | None = None
        async for chunk in stream:
            final_chunk = chunk
            u = getattr(chunk, "usage", None)
            if u is not None:
                t = _usage_total_tokens(u)
                if t is not None:
                    tokens_used = t
            if not chunk.choices:
                continue
            delta_obj = chunk.choices[0].delta
            if delta_obj is None:
                continue
            delta = getattr(delta_obj, "content", None)
            if delta:
                full_content += delta

        logger.info("Generation completed. Content length: %s, Tokens: %s", len(full_content), tokens_used)
        return {
            "content": full_content.strip(),
            "metadata": {
                "tokens_used": tokens_used,
                "model": self.model,
                "provider": self.provider,
            },
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_should_retry_generation),
        reraise=True,
    )
    async def generate_stream(self, request: Any, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self._generate_openrouter(request, prompt_data)
        except Exception as e:
            logger.error("AI generation error: %s", e, exc_info=True)
            raise

    async def _generate_openrouter_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        api = self._require_client()
        temperature, max_tokens, top_p = self._extract_params(request)
        messages = [
            {"role": "system", "content": prompt_data["system_prompt"]},
            {"role": "user", "content": prompt_data["user_prompt"]},
        ]

        logger.info("Starting OpenRouter streaming generation: %s", self.model)
        stream = await api.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
            timeout=self.timeout,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta_obj = chunk.choices[0].delta
            if delta_obj is None:
                continue
            delta = getattr(delta_obj, "content", None)
            if delta:
                yield delta
                await asyncio.sleep(0)

        logger.info("Streaming generation completed")

    async def generate_stream_chunks(
        self,
        request: Any,
        prompt_data: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        try:
            async for chunk in self._generate_openrouter_chunks(request, prompt_data):
                yield chunk
        except Exception as e:
            logger.error("Streaming generation error: %s", e, exc_info=True)
            raise
