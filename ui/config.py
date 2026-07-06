"""
Configuration builder and provider constants for the NeSygma interactive UI.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agent.config import MCPAgentConfig, MCPServerConfig, LLMProvider

# ── Provider → default model ────────────────────────────────────────
PROVIDER_MODELS: Dict[str, str] = {
    "google": "gemini-3.1-flash-lite",
    "nvidia": "nvidia/nemotron-3-nano-30b-a3b",
    "nvidia2": "nvidia/nemotron-3-nano-30b-a3b",
    "openrouter": "openai/gpt-oss-120b",
    "mistral": "mistral-small-2603",
    "xiaomi": "mimo-v2.5-pro",
}

ALL_PROVIDERS = list(PROVIDER_MODELS.keys())
ALL_SOLVERS = ["z3", "clingo", "vampire"]
ALL_EFFORTS = ["none", "minimal", "low", "medium", "high", "xhigh"]

# ── OpenRouter model catalog (dropdown) ─────────────────────────────
# Each entry is a unique model. Reasoning on/off is controlled by the UI toggle.
# ChatOpenRouter does not support extra_body, so reasoning is a simple on/off.
OPENROUTER_MODELS: list[Dict[str, Any]] = [
    {
        "label": "GPT-OSS 120B",
        "model": "openai/gpt-oss-120b",
        "openrouter_provider": {"order": ["deepinfra/bf16"], "allow_fallbacks": True},
        "default_reasoning": True,
    },
    {
        "label": "GPT-OSS 20B",
        "model": "openai/gpt-oss-20b",
        "openrouter_provider": {"order": ["wandb/fp4"], "allow_fallbacks": True},
        "default_reasoning": True,
    },
    {
        "label": "Xiaomi MiMo V2 Flash 309B",
        "model": "xiaomi/mimo-v2-flash",
        "openrouter_provider": {"order": ["xiaomi/fp8"], "allow_fallbacks": False},
        "default_reasoning": True,
    },
    {
        "label": "DeepSeek V4 Flash 284B",
        "model": "deepseek/deepseek-v4-flash",
        "openrouter_provider": {"order": ["deepseek"], "allow_fallbacks": False},
        "default_reasoning": True,
    },
    {
        "label": "NVIDIA Nemotron 30B (Free)",
        "model": "nvidia/nemotron-3-nano-30b-a3b:free",
        "openrouter_provider": None,
        "default_reasoning": True,
    },
    {
        "label": "Mercury 2",
        "model": "inception/mercury-2",
        "openrouter_provider": None,
        "default_reasoning": True,
    },
]

OPENROUTER_MODEL_LABELS = [m["label"] for m in OPENROUTER_MODELS]


# ── Provider → API key env var ──────────────────────────────────────
_PROVIDER_KEY_MAP = {
    "google": "GOOGLE_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "nvidia2": "NVIDIA_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "xiaomi": "MIMO_API_KEY",
}


def build_config(
    provider_str: str,
    model_name: str,
    solver_str: str,
    reasoning_enabled: bool,
    reasoning_effort: str,
    temperature: float,
    top_p: float,
    seed: int,
    max_iterations: int,
    max_output_tokens: int = 32768,
    workspace_path: Optional[Path] = None,
    benchmark: Optional[str] = None,
    model_extra_body: Optional[Dict[str, Any]] = None,
    openrouter_provider: Optional[dict] = None,
) -> MCPAgentConfig:
    """Build MCPAgentConfig from UI widget values."""
    provider = LLMProvider(provider_str)

    api_key = None
    env_key = _PROVIDER_KEY_MAP.get(provider_str)
    if env_key:
        api_key = os.environ.get(env_key)

    env = os.environ.copy()
    if benchmark:
        env["NESYGMA_BENCHMARK"] = str(benchmark)
    if workspace_path:
        env_var_map = {"vampire": "VAMPIRE_WORKSPACE", "clingo": "CLINGO_WORKSPACE", "z3": "Z3_WORKSPACE"}
        env_var = env_var_map.get(solver_str)
        if env_var:
            env[env_var] = str(workspace_path)

    config_base = {
        "provider": provider,
        "openai_api_key": api_key,
        "model_name": model_name,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "seed": seed,
        "reasoning_enabled": reasoning_enabled,
        "reasoning_effort": reasoning_effort,
        "solver": solver_str,
        "mcp_servers": {
            solver_str: MCPServerConfig(
                command="python",
                args=["-m", f"{solver_str}_mcp_server"],
                transport="stdio",
                env=env,
            )
        },
        "benchmark": benchmark,
        "max_iterations": max_iterations,
    }

    if model_extra_body:
        config_base["model_extra_body"] = model_extra_body

    if openrouter_provider:
        config_base["openrouter_provider"] = openrouter_provider

    return MCPAgentConfig(**config_base)