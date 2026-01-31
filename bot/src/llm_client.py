from openai import AsyncOpenAI
import instructor
from typing import Dict, Type, TypeVar, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """OpenRouter LLM client with DeepSeek primary and Claude fallback"""

    def __init__(
        self,
        api_key: str,
        primary_model: str = "deepseek/deepseek-chat",
        fallback_model: str = "anthropic/claude-3.5-sonnet"
    ):
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_model = fallback_model

        # Initialize OpenRouter client with instructor
        self.client = instructor.from_openai(
            AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        )

    async def complete(
        self,
        response_model: Type[T],
        messages: list[Dict[str, str]],
        use_fallback: bool = False,
        **kwargs
    ) -> T:
        """
        Complete with structured output using instructor

        Args:
            response_model: Pydantic model for structured output
            messages: Chat messages
            use_fallback: Use fallback model (Claude) instead of primary
            **kwargs: Additional completion parameters

        Returns:
            Parsed response matching response_model
        """
        model = self.fallback_model if use_fallback else self.primary_model

        try:
            result = await self.client.chat.completions.create(
                model=model,
                response_model=response_model,
                messages=messages,
                **kwargs
            )

            logger.info(f"LLM completion successful with {model}")
            return result

        except Exception as e:
            if not use_fallback and self.fallback_model:
                logger.warning(
                    f"Primary model {self.primary_model} failed: {e}. "
                    f"Trying fallback {self.fallback_model}"
                )
                return await self.complete(
                    response_model=response_model,
                    messages=messages,
                    use_fallback=True,
                    **kwargs
                )
            raise
