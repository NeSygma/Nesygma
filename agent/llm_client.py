import os
import logging
from typing import Optional
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_openrouter import ChatOpenRouter

from agent.config import LLMProvider, PROVIDER_CONFIG, MCPAgentConfig

logger = logging.getLogger(__name__)


class LLMManager:
    """Manages LLM initialization for the agent."""

    def __init__(self, config: MCPAgentConfig):
        self.config = config

        # Resolve provider-specific settings
        provider_cfg = PROVIDER_CONFIG[self.config.provider]
        self._api_base: Optional[str] = provider_cfg.get("api_base")

        # Collect the best available API key
        self._api_key: Optional[str] = None

        # 1. Config argument takes priority
        if self.config.openai_api_key:
            self._api_key = self.config.openai_api_key

        # 2. Collect from provider-specific environment variables
        if not self._api_key:
            for env_var in provider_cfg["api_key_env_vars"]:
                key = os.environ.get(env_var)
                if key:
                    self._api_key = key
                    break

        if not self._api_key:
            logger.warning(
                f"No API key found for provider '{self.config.provider.value}'. "
                f"Set one of: {provider_cfg['api_key_env_vars']}"
            )
        else:
            logger.info(f"Provider '{self.config.provider.value}' — using primary API key.")

    def get_llm(self, api_key: Optional[str] = None):
        """Get an LLM instance for the configured provider."""
        key = api_key or self._api_key
        if not key:
            raise ValueError(f"No API key available for provider '{self.config.provider.value}'.")

        # ── Google Gemini ────────────────────────────────────────────
        if self.config.provider == LLMProvider.GOOGLE:
            return self._build_google(key)

        # ── Mistral ──────────────────────────────────────────────────
        if self.config.provider == LLMProvider.MISTRAL:
            return self._build_mistral(key)

        # ── OpenRouter ───────────────────────────────────────────────
        if self.config.provider == LLMProvider.OPENROUTER:
            return self._build_openrouter(key)

        # ── Xiaomi (OpenAI-compatible) ───────────────────────────────
        if self.config.provider == LLMProvider.XIAOMI:
            return self._build_deepseek_compat(key)

        # ── NVIDIA (OpenAI-compatible via ChatDeepSeek) ──────────────
        if self.config.provider == LLMProvider.NVIDIA:
            return self._build_deepseek_compat(key)

        raise ValueError(f"Unknown provider: {self.config.provider}")

    # ── Google Gemini ────────────────────────────────────────────────
    def _build_google(self, key: str):
        thinking_params = {}
        google_kwargs = {
            "model": self.config.model_name,
            "google_api_key": key,
            "max_output_tokens": self.config.max_output_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "streaming": True,
            "model_kwargs": {
                "automatic_function_calling": {"disable": True},
            },
        }

        model_name = (self.config.model_name or "").lower()
        effort = (self.config.reasoning_effort or "high").lower()

        if self.config.reasoning_enabled:
            thinking_params["include_thoughts"] = True
            if model_name.startswith("gemini-3"):
                effort_map = {"none": "minimal", "minimal": "minimal", "low": "low", "medium": "medium", "high": "high", "xhigh": "high"}
                thinking_params["thinking_level"] = effort_map.get(effort, "high")
            elif model_name.startswith("gemini-2.5"):
                budget_map = {"none": 0, "minimal": 128, "low": 256, "medium": 1024, "high": 2048, "xhigh": 4096}
                thinking_params["thinking_budget"] = budget_map.get(effort, 2048)
        else:
            if model_name.startswith("gemini-3"):
                thinking_params["thinking_level"] = "minimal"
            elif model_name.startswith("gemini-2.5"):
                thinking_params["thinking_budget"] = 0

        google_kwargs.update(thinking_params)

        try:
            return ChatGoogleGenerativeAI(**google_kwargs)
        except TypeError as e:
            logger.warning(
                "Google thinking parameters not supported as direct kwargs (%s). "
                "Retrying via model_kwargs.", str(e),
            )
            fallback_kwargs = dict(google_kwargs)
            fallback_model_kwargs = dict(fallback_kwargs.get("model_kwargs", {}))
            fallback_model_kwargs.update(thinking_params)
            fallback_kwargs["model_kwargs"] = fallback_model_kwargs
            fallback_kwargs.pop("include_thoughts", None)
            fallback_kwargs.pop("thinking_level", None)
            fallback_kwargs.pop("thinking_budget", None)
            return ChatGoogleGenerativeAI(**fallback_kwargs)

    # ── Mistral ──────────────────────────────────────────────────────
    def _build_mistral(self, key: str):
        mistral_kwargs = dict(
            model=self.config.model_name,
            api_key=key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_output_tokens,
            streaming=True,
        )
        if self.config.seed is not None:
            mistral_kwargs["random_seed"] = self.config.seed
        if self.config.reasoning_enabled:
            mistral_kwargs["model_kwargs"] = {
                "reasoning_effort": self.config.reasoning_effort.lower() if self.config.reasoning_effort else "high",
            }
        return ChatMistralAI(**mistral_kwargs)

    # ── OpenRouter ───────────────────────────────────────────────────
    def _build_openrouter(self, key: str):
        or_kwargs = dict(
            model=self.config.model_name,
            openrouter_api_key=key,
            max_tokens=self.config.max_output_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            seed=self.config.seed,
            streaming=True,
        )
        if self.config.openrouter_provider:
            or_kwargs["openrouter_provider"] = self.config.openrouter_provider

        # ChatOpenRouter.reasoning accepts {"effort": ..., "summary": ...}
        # effort values: 'xhigh', 'high', 'medium', 'low', 'minimal', 'none'
        if self.config.reasoning_enabled:
            effort = (self.config.reasoning_effort or "high").lower()
            or_kwargs["reasoning"] = {"effort": effort, "summary": "auto"}
        else:
            or_kwargs["reasoning"] = {"effort": "none"}

        return ChatOpenRouter(**or_kwargs)

    # ── DeepSeek-compatible (NVIDIA, Xiaomi) ─────────────────────────
    def _build_deepseek_compat(self, key: str):
        kwargs = dict(
            api_base=self._api_base,
            api_key=key,
            model=self.config.model_name,
            max_tokens=self.config.max_output_tokens,
            temperature=self.config.temperature,
            streaming=True,
            top_p=self.config.top_p,
            seed=self.config.seed,
            model_kwargs={"stream_options": {"include_usage": True}},
        )

        # Merge model-specific extra body from config
        if self.config.model_extra_body:
            kwargs["extra_body"] = dict(self.config.model_extra_body)
        elif not self.config.reasoning_enabled:
            # Explicitly disable reasoning/thinking when toggle is off
            kwargs["extra_body"] = {
                "reasoning": {"enabled": False},
                "thinking": {"type": "disabled"},
            }

        return ChatDeepSeek(**kwargs)
