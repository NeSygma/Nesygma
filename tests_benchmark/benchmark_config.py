import os
import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agent.config import MCPAgentConfig, MCPServerConfig, LLMProvider

def create_agent_config(provider_str: str, solver_str: str, model_override: str, workspace_path: Path = None, or_provider: str = None, benchmark: str = None, key_index: int = None) -> MCPAgentConfig:
    provider = LLMProvider(provider_str)
    
    if provider == LLMProvider.GOOGLE:
        if key_index:
            key_name = "GOOGLE_API_KEY" if key_index == 1 else f"GOOGLE_API_KEY_{key_index}"
            api_key = os.environ.get(key_name)
        else:
            api_key = os.environ.get("GOOGLE_API_KEY")
        default_model = "gemini-3.1-flash-lite"
    elif provider == LLMProvider.NVIDIA:
        api_key = os.environ.get("NVIDIA_API_KEY")
        default_model = "nvidia/nemotron-3-nano-30b-a3b"
    elif provider == LLMProvider.MISTRAL:
        api_key = os.environ.get("MISTRAL_API_KEY")
        default_model = "mistral-small-2603"
    elif provider == LLMProvider.XIAOMI:
        api_key = os.environ.get("MIMO_API_KEY")
        default_model = "mimo-v2.5-pro"
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        default_model = "openai/gpt-oss-120b"

    env = os.environ.copy()
    if benchmark:
        env["NESYGMA_BENCHMARK"] = str(benchmark)
        
    if workspace_path:
        env_var_map = {
            "vampire": "VAMPIRE_WORKSPACE",
            "clingo": "CLINGO_WORKSPACE",
            "z3": "Z3_WORKSPACE"
        }
        env_var = env_var_map.get(solver_str)
        if env_var:
            env[env_var] = str(workspace_path)

    config_base = {
        "provider": provider,
        "openai_api_key": api_key,
        "model_name": model_override or default_model,
        "max_output_tokens": 32768,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 42,
        "reasoning_enabled": True,
        "reasoning_effort": "medium",
        "solver": solver_str,
        "mcp_servers": {
            solver_str: MCPServerConfig(
                command="python",
                args=["-m", f"{solver_str}_mcp_server"],
                transport="stdio",
                env=env
            )
        },
        "benchmark": benchmark
    }
    
    return MCPAgentConfig(**config_base)

def setup_argparser(description="NeSygma Benchmarking Script"):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--benchmark", type=str, choices=["ASPBench", "FOLIO", "agieval_lsat"], required=True)
    parser.add_argument("--problem", type=str, help="Problem ID (ASPBench) or index (FOLIO/agieval_lsat)")
    parser.add_argument("--start", type=int, help="Start problem index (inclusive) for running a range of problems")
    parser.add_argument("--end", type=int, help="End problem index (inclusive) for running a range of problems")
    parser.add_argument("--provider", type=str, default="cerebras")
    parser.add_argument("--solver", type=str, default=None, help="Solver override. If omitted in MCP, it auto-selects from Selector.")
    parser.add_argument("--model", type=str, help="Override default model")
    parser.add_argument("--or-provider", type=str, default=None,
                        help="Pin OpenRouter to a specific upstream provider (e.g. DeepInfra, Anthropic, OpenAI)")
    parser.add_argument("--key-index", type=int, default=None, help="Google API key index (1-11) to override GOOGLE_API_KEY")
    return parser
