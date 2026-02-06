"""
API Utility Functions
Handles API key rotation and fallback logic
"""

import logging
from typing import Callable, Any
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def execute_with_fallback(config, llm_callable: Callable, *args, **kwargs) -> Any:
    """
    Execute an LLM call with automatic fallback to backup API keys on failure

    Args:
        config: Config object with API key management
        llm_callable: The LLM function/method to call
        *args, **kwargs: Arguments to pass to the callable

    Returns:
        Result from the LLM call

    Raises:
        Exception: If all API keys fail
    """
    last_exception = None
    attempts = 0
    max_attempts = 1 + len(config.fallback_api_keys)

    while attempts < max_attempts:
        try:
            logger.info(f"Attempting LLM call (attempt {attempts + 1}/{max_attempts})")
            result = llm_callable(*args, **kwargs)
            return result

        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()

            # Check if it's an API key exhaustion error
            if any(keyword in error_msg for keyword in ['rate limit', 'quota', 'insufficient', 'limit exceeded']):
                logger.warning(f"API key issue detected: {e}")

                # Try to switch to fallback key
                if config.switch_to_fallback_key():
                    logger.info("Switched to fallback API key, retrying...")

                    # Reinitialize the LLM with the new API key
                    if hasattr(llm_callable, '__self__'):
                        # It's a method, update the instance's LLM
                        agent = llm_callable.__self__
                        agent.llm = create_new_llm(config)
                        logger.info("LLM reinitialized with new API key")

                    attempts += 1
                    continue
                else:
                    logger.error("No more fallback API keys available")
                    raise Exception("All API keys exhausted") from e
            else:
                # Some other error, re-raise immediately
                logger.error(f"Non-recoverable error: {e}")
                raise

        attempts += 1

    # If we get here, all attempts failed
    raise last_exception


def create_new_llm(config):
    """
    Create a new LLM instance with current config

    Args:
        config: Config object

    Returns:
        ChatOpenAI or ChatAnthropic instance
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.callbacks import StreamingStdOutCallbackHandler

    callbacks = [StreamingStdOutCallbackHandler()] if config.use_streaming else []

    if config.llm_provider == "openai":
        llm_kwargs = {
            "model": config.llm_model,
            "temperature": 0.1,
            "openai_api_key": config.get_active_api_key(),  # Use current active key
            "max_retries": config.max_retries,
        }
        if hasattr(config, 'openai_base_url') and config.openai_base_url:
            llm_kwargs["base_url"] = config.openai_base_url
        return ChatOpenAI(**llm_kwargs)
    else:
        return ChatAnthropic(
            model=config.llm_model,
            temperature=0.1,
            anthropic_api_key=config.anthropic_api_key
        )


def wrap_llm_call(func):
    """
    Decorator to wrap LLM calls with automatic fallback logic

    Usage:
        @wrap_llm_call
        def my_llm_method(self, ...):
            result = self.llm.invoke(...)
            return result
    """
    def wrapper(self, *args, **kwargs):
        try:
            return execute_with_fallback(self.config, func, self, *args, **kwargs)
        except Exception as e:
            logger.error(f"LLM call failed after all retries: {e}")
            raise

    return wrapper
