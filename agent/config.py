from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    NVIDIA = "nvidia"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    MISTRAL = "mistral"
    XIAOMI = "xiaomi"


PROVIDER_CONFIG = {
    LLMProvider.NVIDIA: {
        "api_base": "https://integrate.api.nvidia.com/v1",
        "api_key_env_vars": ["NVIDIA_API_KEY"],
    },
    LLMProvider.OPENROUTER: {
        "api_base": "https://openrouter.ai/api/v1",
        "api_key_env_vars": ["OPENROUTER_API_KEY"],
    },
    LLMProvider.GOOGLE: {
        "api_base": None,
        "api_key_env_vars": [
            "GOOGLE_API_KEY",
            "GOOGLE_API_KEY_2",
            "GOOGLE_API_KEY_3",
            "GOOGLE_API_KEY_4",
            "GOOGLE_API_KEY_5",
            "GOOGLE_API_KEY_6",
            "GOOGLE_API_KEY_7",
            "GOOGLE_API_KEY_8",
            "GOOGLE_API_KEY_9",
            "GOOGLE_API_KEY_10",
            "GOOGLE_API_KEY_11",
        ],
    },
    LLMProvider.MISTRAL: {
        "api_base": None,
        "api_key_env_vars": ["MISTRAL_API_KEY"],
    },
    LLMProvider.XIAOMI: {
        "api_base": "https://api.xiaomimimo.com/v1",
        "api_key_env_vars": ["MIMO_API_KEY"],
    },
}


class MCPServerConfig(BaseModel):
    command: str = Field(description="Command to run the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    transport: str = Field(default="stdio", description="Transport type")
    env: Optional[dict] = Field(default=None, description="Environment variables")


class MCPAgentConfig(BaseModel):
    provider: LLMProvider = Field(
        default=LLMProvider.GOOGLE,
        description="LLM provider: 'nvidia', 'openrouter', 'google', 'mistral', or 'xiaomi'"
    )

    # LLM settings
    openai_api_key: Optional[str] = Field(default=None, description="Explicit API key (overrides env lookup)")
    model_name: str = Field(default="gemini-3.1-flash-lite")
    max_output_tokens: int = Field(default=16384)
    temperature: float = Field(default=0.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter")
    repetition_penalty: Optional[float] = Field(default=None, description="Repetition penalty")
    seed: Optional[int] = Field(default=42, description="Seed for deterministic sampling (best-effort)")
    benchmark: Optional[str] = Field(default=None, description="Benchmark dataset name (e.g. FOLIO, ASPBench)")
    reasoning_enabled: bool = Field(default=True, description="Enable reasoning/thinking")
    reasoning_effort: str = Field(default="high", description="Reasoning effort: low, medium, high, xhigh")
    openrouter_provider: Optional[dict] = Field(
        default=None,
        description="OpenRouter provider routing config (order, allow_fallbacks, require_parameters, etc.)"
    )
    model_extra_body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Model-specific extra body params merged into the API request"
    )

    # Solver specialization
    solver: str = Field(
        default="z3",
        description="Solver specialization: 'clingo', 'z3', or 'vampire'"
    )

    # Agent settings
    max_iterations: int = Field(default=7, ge=1, le=10)
    translator_max_iterations: int = Field(
        default=4,
        ge=1,
        le=4,
        description="Maximum refinement iterations for translator phase before hard failure."
    )
    prune_history: bool = Field(default=True, description="Keep only the latest iteration's tool/AI messages to save tokens")
    tool_timeout_seconds: int = Field(
        default=70,
        ge=1,
        description="Per-tool MCP call timeout in seconds (client-side safety timeout)."
    )

    # MCP servers - use absolute path for reliability
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)