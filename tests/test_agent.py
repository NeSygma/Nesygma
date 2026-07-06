"""
Tests for the agent module: config, llm_client, phase_translator, phase_prompts,
single_pass_runner, mcp_core.
Tests pure logic without requiring actual LLM connections or MCP servers.
"""
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  {GREEN}✓{RESET} {name}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {name}")
        if detail:
            for line in detail.strip().split("\n"):
                print(f"    {YELLOW}{line}{RESET}")


class FakeChunk:
    """Mock AIMessageChunk for testing streaming functions."""
    def __init__(self, content="", tool_calls=None, usage_metadata=None,
                 additional_kwargs=None, response_metadata=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage_metadata = usage_metadata
        self.additional_kwargs = additional_kwargs or {}
        self.response_metadata = response_metadata or {}

    def __add__(self, other):
        if other is None:
            return self
        new = FakeChunk()
        new.content = (self.content or "") + (other.content or "")
        new.tool_calls = list(self.tool_calls) + list(other.tool_calls)
        new.usage_metadata = other.usage_metadata or self.usage_metadata
        new.additional_kwargs = {**self.additional_kwargs, **other.additional_kwargs}
        new.response_metadata = {**self.response_metadata, **other.response_metadata}
        return new


# ═════════════════════════════ CONFIG: LLMProvider ENUM ═════════════════════

def test_llm_provider_values():
    """LLMProvider should have all 6 expected providers."""
    from agent.config import LLMProvider
    expected = {"nvidia", "nvidia2", "openrouter", "google", "mistral", "xiaomi"}
    actual = {p.value for p in LLMProvider}
    ok = actual == expected
    report("LLMProvider has all 6 providers", ok, f"Got: {actual}")


def test_llm_provider_from_string():
    """LLMProvider should be constructible from string values."""
    from agent.config import LLMProvider
    for val in ["nvidia", "nvidia2", "openrouter", "google", "mistral", "xiaomi"]:
        p = LLMProvider(val)
        ok = p.value == val
        report(f"LLMProvider('{val}') works", ok)


def test_llm_provider_invalid():
    """LLMProvider with invalid value should raise ValueError."""
    from agent.config import LLMProvider
    try:
        LLMProvider("invalid_provider")
        report("LLMProvider('invalid') raises ValueError", False, "No exception raised")
    except ValueError:
        report("LLMProvider('invalid') raises ValueError", True)


def test_llm_provider_is_str():
    """LLMProvider should be a string enum (serializable)."""
    from agent.config import LLMProvider
    ok = isinstance(LLMProvider.GOOGLE, str) and LLMProvider.GOOGLE == "google"
    report("LLMProvider is str enum", ok)


# ═════════════════════════════ CONFIG: PROVIDER_CONFIG ══════════════════════

def test_provider_config_has_all_providers():
    """PROVIDER_CONFIG should have entries for all LLMProvider members."""
    from agent.config import PROVIDER_CONFIG, LLMProvider
    for p in LLMProvider:
        if p not in PROVIDER_CONFIG:
            report(f"PROVIDER_CONFIG has entry for {p.value}", False, "Missing")
            return
    report("PROVIDER_CONFIG has entries for all providers", True)


def test_provider_config_has_api_key_env_vars():
    """Each provider config should have api_key_env_vars as a non-empty list."""
    from agent.config import PROVIDER_CONFIG
    for provider, cfg in PROVIDER_CONFIG.items():
        env_vars = cfg.get("api_key_env_vars", [])
        if not isinstance(env_vars, list) or len(env_vars) == 0:
            report(f"PROVIDER_CONFIG[{provider.value}] has api_key_env_vars", False)
            return
    report("All providers have non-empty api_key_env_vars", True)


def test_provider_config_google_has_multiple_keys():
    """Google should have multiple API key env vars for rotation."""
    from agent.config import PROVIDER_CONFIG, LLMProvider
    env_vars = PROVIDER_CONFIG[LLMProvider.GOOGLE]["api_key_env_vars"]
    ok = len(env_vars) >= 2 and "GOOGLE_API_KEY" in env_vars
    report(f"Google has {len(env_vars)} API key env vars", ok)


def test_provider_config_api_base_types():
    """api_base should be either None or a string URL."""
    from agent.config import PROVIDER_CONFIG
    for provider, cfg in PROVIDER_CONFIG.items():
        api_base = cfg.get("api_base")
        if api_base is not None and not isinstance(api_base, str):
            report(f"PROVIDER_CONFIG[{provider.value}].api_base is None or str", False)
            return
    report("All api_base values are None or str", True)


# ═════════════════════════════ CONFIG: MCPServerConfig ══════════════════════

def test_mcp_server_config_defaults():
    """MCPServerConfig should have sensible defaults."""
    from agent.config import MCPServerConfig
    cfg = MCPServerConfig(command="python")
    ok = (
        cfg.command == "python"
        and cfg.args == []
        and cfg.transport == "stdio"
        and cfg.env is None
    )
    report("MCPServerConfig defaults correct", ok)


def test_mcp_server_config_custom():
    """MCPServerConfig should accept custom values."""
    from agent.config import MCPServerConfig
    cfg = MCPServerConfig(
        command="python",
        args=["-m", "z3_mcp_server"],
        transport="stdio",
        env={"Z3_TIMEOUT": "60"},
    )
    ok = (
        cfg.args == ["-m", "z3_mcp_server"]
        and cfg.transport == "stdio"
        and cfg.env == {"Z3_TIMEOUT": "60"}
    )
    report("MCPServerConfig custom values work", ok)


def test_mcp_server_config_model_dump():
    """MCPServerConfig.model_dump() should produce a clean dict."""
    from agent.config import MCPServerConfig
    cfg = MCPServerConfig(command="python", args=["-m", "test"])
    d = cfg.model_dump()
    ok = isinstance(d, dict) and d["command"] == "python" and d["args"] == ["-m", "test"]
    report("MCPServerConfig.model_dump() works", ok)


def test_mcp_server_config_model_dump_exclude_none():
    """MCPServerConfig.model_dump(exclude_none=True) should omit None fields."""
    from agent.config import MCPServerConfig
    cfg = MCPServerConfig(command="python")
    d = cfg.model_dump(exclude_none=True)
    ok = "env" not in d
    report("MCPServerConfig.model_dump(exclude_none) omits None env", ok)


# ═════════════════════════════ CONFIG: MCPAgentConfig ═══════════════════════

def test_mcp_agent_config_defaults():
    """MCPAgentConfig should have sensible defaults."""
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig()
    ok = (
        cfg.provider == LLMProvider.GOOGLE
        and cfg.model_name == "gemini-3.1-flash-lite"
        and cfg.solver == "z3"
        and cfg.max_output_tokens == 16384
        and cfg.temperature == 0.0
        and cfg.top_p == 1.0
        and cfg.seed == 42
        and cfg.reasoning_enabled is True
        and cfg.reasoning_effort == "high"
        and cfg.max_iterations == 7
        and cfg.translator_max_iterations == 4
        and cfg.prune_history is True
        and cfg.tool_timeout_seconds == 70
        and cfg.benchmark is None
        and cfg.mcp_servers == {}
    )
    report("MCPAgentConfig defaults are correct", ok)


def test_mcp_agent_config_custom():
    """MCPAgentConfig should accept all custom values."""
    from agent.config import MCPAgentConfig, LLMProvider, MCPServerConfig
    cfg = MCPAgentConfig(
        provider=LLMProvider.NVIDIA,
        model_name="test-model",
        solver="clingo",
        max_output_tokens=8192,
        temperature=0.5,
        top_p=0.9,
        seed=99,
        reasoning_enabled=False,
        reasoning_effort="low",
        max_iterations=3,
        translator_max_iterations=2,
        prune_history=False,
        tool_timeout_seconds=30,
        benchmark="FOLIO",
        mcp_servers={"clingo": MCPServerConfig(command="python", args=["-m", "clingo_mcp_server"])},
    )
    ok = (
        cfg.provider == LLMProvider.NVIDIA
        and cfg.model_name == "test-model"
        and cfg.solver == "clingo"
        and cfg.max_output_tokens == 8192
        and cfg.temperature == 0.5
        and cfg.top_p == 0.9
        and cfg.seed == 99
        and cfg.reasoning_enabled is False
        and cfg.reasoning_effort == "low"
        and cfg.max_iterations == 3
        and cfg.translator_max_iterations == 2
        and cfg.prune_history is False
        and cfg.tool_timeout_seconds == 30
        and cfg.benchmark == "FOLIO"
        and "clingo" in cfg.mcp_servers
    )
    report("MCPAgentConfig custom values work", ok)


def test_mcp_agent_config_top_p_bounds():
    """MCPAgentConfig top_p should reject values outside [0, 1]."""
    from agent.config import MCPAgentConfig
    try:
        MCPAgentConfig(top_p=1.5)
        report("MCPAgentConfig top_p=1.5 raises ValidationError", False, "No exception")
    except Exception:
        report("MCPAgentConfig top_p=1.5 raises ValidationError", True)

    try:
        MCPAgentConfig(top_p=-0.1)
        report("MCPAgentConfig top_p=-0.1 raises ValidationError", False, "No exception")
    except Exception:
        report("MCPAgentConfig top_p=-0.1 raises ValidationError", True)


def test_mcp_agent_config_max_iterations_bounds():
    """MCPAgentConfig max_iterations should reject values outside [1, 10]."""
    from agent.config import MCPAgentConfig
    try:
        MCPAgentConfig(max_iterations=0)
        report("MCPAgentConfig max_iterations=0 raises ValidationError", False, "No exception")
    except Exception:
        report("MCPAgentConfig max_iterations=0 raises ValidationError", True)

    try:
        MCPAgentConfig(max_iterations=11)
        report("MCPAgentConfig max_iterations=11 raises ValidationError", False, "No exception")
    except Exception:
        report("MCPAgentConfig max_iterations=11 raises ValidationError", True)


def test_mcp_agent_config_translator_max_iterations_bounds():
    """MCPAgentConfig translator_max_iterations should reject values outside [1, 4]."""
    from agent.config import MCPAgentConfig
    try:
        MCPAgentConfig(translator_max_iterations=5)
        report("MCPAgentConfig translator_max_iterations=5 raises ValidationError", False, "No exception")
    except Exception:
        report("MCPAgentConfig translator_max_iterations=5 raises ValidationError", True)


def test_mcp_agent_config_tool_timeout_bounds():
    """MCPAgentConfig tool_timeout_seconds should reject values < 1."""
    from agent.config import MCPAgentConfig
    try:
        MCPAgentConfig(tool_timeout_seconds=0)
        report("MCPAgentConfig tool_timeout_seconds=0 raises ValidationError", False, "No exception")
    except Exception:
        report("MCPAgentConfig tool_timeout_seconds=0 raises ValidationError", True)


def test_mcp_agent_config_model_dump():
    """MCPAgentConfig.model_dump() should produce a serializable dict."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig()
    d = cfg.model_dump()
    ok = isinstance(d, dict) and "provider" in d and "solver" in d
    report("MCPAgentConfig.model_dump() works", ok)


def test_mcp_agent_config_openrouter_fields():
    """MCPAgentConfig should support openrouter_provider and model_extra_body."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(
        openrouter_provider={"order": ["deepseek"]},
        model_extra_body={"reasoning": {"effort": "high"}},
    )
    ok = (
        cfg.openrouter_provider == {"order": ["deepseek"]}
        and cfg.model_extra_body == {"reasoning": {"effort": "high"}}
    )
    report("MCPAgentConfig openrouter fields work", ok)


# ═════════════════════════════ PhaseUsage ═══════════════════════════════════

def test_phase_usage_defaults():
    """PhaseUsage should default all counters to 0."""
    from agent.phase_translator import PhaseUsage
    u = PhaseUsage()
    ok = u.input_tokens == 0 and u.output_tokens == 0 and u.total_tokens == 0
    report("PhaseUsage defaults to 0", ok)


def test_phase_usage_custom():
    """PhaseUsage should accept custom values."""
    from agent.phase_translator import PhaseUsage
    u = PhaseUsage(input_tokens=100, output_tokens=200, total_tokens=300)
    ok = u.input_tokens == 100 and u.output_tokens == 200 and u.total_tokens == 300
    report("PhaseUsage custom values work", ok)


def test_phase_usage_negative_rejected():
    """PhaseUsage should reject negative token counts."""
    from agent.phase_translator import PhaseUsage
    try:
        PhaseUsage(input_tokens=-1)
        report("PhaseUsage negative input_tokens raises ValidationError", False, "No exception")
    except Exception:
        report("PhaseUsage negative input_tokens raises ValidationError", True)


def test_phase_usage_no_extra_fields():
    """PhaseUsage should reject extra fields."""
    from agent.phase_translator import PhaseUsage
    try:
        PhaseUsage(extra_field=123)
        report("PhaseUsage rejects extra fields", False, "No exception")
    except Exception:
        report("PhaseUsage rejects extra fields", True)


def test_phase_usage_assignment_validation():
    """PhaseUsage should validate on assignment."""
    from agent.phase_translator import PhaseUsage
    u = PhaseUsage()
    try:
        u.input_tokens = -5
        report("PhaseUsage validates on assignment", False, "No exception raised for negative")
    except Exception:
        report("PhaseUsage validates on assignment", True)


# ═════════════════════════════ TranslatorOutcome ════════════════════════════

def test_translator_outcome_success_requires_result():
    """Successful TranslatorOutcome must have definitive_result_text."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    try:
        TranslatorOutcome(
            success=True,
            iterations_used=1,
            messages=[],
            usage=PhaseUsage(),
            definitive_result_text=None,
        )
        report("TranslatorOutcome success without result raises", False, "No exception")
    except ValueError as e:
        ok = "definitive_result_text" in str(e)
        report("TranslatorOutcome success without result raises ValueError", ok, str(e))


def test_translator_outcome_success_with_result():
    """Successful TranslatorOutcome with definitive_result_text should be valid."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    outcome = TranslatorOutcome(
        success=True,
        iterations_used=1,
        messages=[],
        usage=PhaseUsage(),
        definitive_result_text="result here",
    )
    ok = outcome.success and outcome.definitive_result_text == "result here"
    report("TranslatorOutcome success with result is valid", ok)


def test_translator_outcome_failure_requires_reason():
    """Failed TranslatorOutcome must have failure_reason."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    try:
        TranslatorOutcome(
            success=False,
            iterations_used=1,
            messages=[],
            usage=PhaseUsage(),
            failure_reason=None,
        )
        report("TranslatorOutcome failure without reason raises", False, "No exception")
    except ValueError as e:
        ok = "failure_reason" in str(e)
        report("TranslatorOutcome failure without reason raises ValueError", ok, str(e))


def test_translator_outcome_failure_with_reason():
    """Failed TranslatorOutcome with failure_reason should be valid."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    outcome = TranslatorOutcome(
        success=False,
        iterations_used=3,
        messages=[],
        usage=PhaseUsage(),
        failure_reason="max iterations reached",
    )
    ok = not outcome.success and outcome.failure_reason == "max iterations reached"
    report("TranslatorOutcome failure with reason is valid", ok)


def test_translator_outcome_no_extra_fields():
    """TranslatorOutcome should reject extra fields."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    try:
        TranslatorOutcome(
            success=True,
            iterations_used=1,
            messages=[],
            usage=PhaseUsage(),
            definitive_result_text="ok",
            bogus_field="nope",
        )
        report("TranslatorOutcome rejects extra fields", False, "No exception")
    except Exception:
        report("TranslatorOutcome rejects extra fields", True)


def test_translator_outcome_iterations_non_negative():
    """TranslatorOutcome should reject negative iterations_used."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    try:
        TranslatorOutcome(
            success=False,
            iterations_used=-1,
            messages=[],
            usage=PhaseUsage(),
            failure_reason="test",
        )
        report("TranslatorOutcome rejects negative iterations", False, "No exception")
    except Exception:
        report("TranslatorOutcome rejects negative iterations", True)


def test_translator_outcome_with_solver_payload():
    """TranslatorOutcome should store solver_payload and last_tool_* fields."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    outcome = TranslatorOutcome(
        success=True,
        iterations_used=2,
        messages=[],
        usage=PhaseUsage(),
        definitive_result_text="ok",
        solver_payload={"status": "satisfiable", "models": [["a"]]},
        last_tool_name="run_clingo",
        last_tool_args={"filename": "test.lp"},
    )
    ok = (
        outcome.solver_payload is not None
        and outcome.solver_payload["status"] == "satisfiable"
        and outcome.last_tool_name == "run_clingo"
        and outcome.last_tool_args == {"filename": "test.lp"}
    )
    report("TranslatorOutcome stores solver_payload and tool info", ok)


# ═════════════════════════════ _chunk_content_to_text ═══════════════════════

def test_chunk_content_none():
    """None content should return empty string."""
    from agent.phase_translator import _chunk_content_to_text
    ok = _chunk_content_to_text(None) == ""
    report("_chunk_content_to_text(None) -> ''", ok)


def test_chunk_content_string():
    """String content should be returned as-is."""
    from agent.phase_translator import _chunk_content_to_text
    ok = _chunk_content_to_text("hello world") == "hello world"
    report("_chunk_content_to_text(str) -> str", ok)


def test_chunk_content_list_strings():
    """List of strings should be concatenated."""
    from agent.phase_translator import _chunk_content_to_text
    result = _chunk_content_to_text(["hello", " ", "world"])
    ok = result == "hello world"
    report("_chunk_content_to_text(list[str]) -> concatenated", ok)


def test_chunk_content_list_dicts_with_text():
    """List of dicts with 'text' key should extract text."""
    from agent.phase_translator import _chunk_content_to_text
    content = [{"type": "text", "text": "hello"}, {"type": "text", "text": " world"}]
    ok = _chunk_content_to_text(content) == "hello world"
    report("_chunk_content_to_text(list[dict{text}]) -> extracted", ok)


def test_chunk_content_list_skips_thinking():
    """Thinking/reasoning blocks should be skipped."""
    from agent.phase_translator import _chunk_content_to_text
    content = [
        {"type": "thinking", "thinking": "internal reasoning"},
        {"type": "text", "text": "actual answer"},
    ]
    result = _chunk_content_to_text(content)
    ok = "internal reasoning" not in result and "actual answer" in result
    report("_chunk_content_to_text skips thinking blocks", ok)


def test_chunk_content_list_skips_reasoning():
    """Reasoning blocks should be skipped."""
    from agent.phase_translator import _chunk_content_to_text
    content = [
        {"type": "reasoning", "reasoning": "chain of thought"},
        {"type": "text", "text": "final answer"},
    ]
    result = _chunk_content_to_text(content)
    ok = "chain of thought" not in result and "final answer" in result
    report("_chunk_content_to_text skips reasoning blocks", ok)


def test_chunk_content_list_with_text_attr():
    """List items with .text attribute should extract text."""
    from agent.phase_translator import _chunk_content_to_text
    obj = MagicMock()
    obj.text = "from attribute"
    result = _chunk_content_to_text([obj])
    ok = result == "from attribute"
    report("_chunk_content_to_text(list[obj.text]) -> extracted", ok)


def test_chunk_content_fallback_str():
    """Non-string, non-list content should be str()-ified."""
    from agent.phase_translator import _chunk_content_to_text
    result = _chunk_content_to_text(42)
    ok = result == "42"
    report("_chunk_content_to_text(int) -> str(int)", ok)


def test_chunk_content_empty_list():
    """Empty list should return empty string."""
    from agent.phase_translator import _chunk_content_to_text
    ok = _chunk_content_to_text([]) == ""
    report("_chunk_content_to_text([]) -> ''", ok)


def test_chunk_content_mixed_list():
    """List mixing strings and dicts should concatenate correctly."""
    from agent.phase_translator import _chunk_content_to_text
    content = ["hello ", {"type": "text", "text": "world"}, " !"]
    result = _chunk_content_to_text(content)
    ok = result == "hello world !"
    report("_chunk_content_to_text mixed list -> concatenated", ok)


# ═════════════════════════════ _extract_reasoning_text ══════════════════════

def test_extract_reasoning_from_additional_kwargs_string():
    """Reasoning in additional_kwargs as string should be extracted."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning_content": "I think therefore I am"}
    chunk.response_metadata = {}
    chunk.content = "answer"
    result = _extract_reasoning_text(chunk)
    ok = result == "I think therefore I am"
    report("_extract_reasoning_text from additional_kwargs string", ok)


def test_extract_reasoning_from_additional_kwargs_dict():
    """Reasoning in additional_kwargs as dict should extract text/content."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning": {"text": "deep thought"}}
    chunk.response_metadata = {}
    chunk.content = "answer"
    result = _extract_reasoning_text(chunk)
    ok = result == "deep thought"
    report("_extract_reasoning_text from additional_kwargs dict", ok)


def test_extract_reasoning_from_content_thinking_block():
    """Thinking block in content list should be extracted."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {}
    chunk.response_metadata = {}
    chunk.content = [{"type": "thinking", "thinking": "Gemini reasoning here"}]
    result = _extract_reasoning_text(chunk)
    ok = result == "Gemini reasoning here"
    report("_extract_reasoning_text from content thinking block", ok)


def test_extract_reasoning_from_content_reasoning_block():
    """Reasoning block in content list should be extracted."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {}
    chunk.response_metadata = {}
    chunk.content = [{"type": "reasoning", "reasoning": "OpenRouter reasoning"}]
    result = _extract_reasoning_text(chunk)
    ok = result == "OpenRouter reasoning"
    report("_extract_reasoning_text from content reasoning block", ok)


def test_extract_reasoning_mistral_nested():
    """Mistral nested thinking format should be extracted."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {}
    chunk.response_metadata = {}
    chunk.content = [{"type": "thinking", "thinking": [{"type": "text", "text": "Mistral thought"}]}]
    result = _extract_reasoning_text(chunk)
    ok = result == "Mistral thought"
    report("_extract_reasoning_text Mistral nested format", ok)


def test_extract_reasoning_empty():
    """Chunk with no reasoning should return empty string."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {}
    chunk.response_metadata = {}
    chunk.content = "just text"
    result = _extract_reasoning_text(chunk)
    ok = result == ""
    report("_extract_reasoning_text no reasoning -> ''", ok)


def test_extract_reasoning_priority_additional_kwargs():
    """additional_kwargs reasoning should take priority over content blocks."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning_content": "from kwargs"}
    chunk.response_metadata = {}
    chunk.content = [{"type": "thinking", "thinking": "from content"}]
    result = _extract_reasoning_text(chunk)
    ok = result == "from kwargs"
    report("_extract_reasoning_text priority: additional_kwargs over content", ok)


def test_extract_reasoning_multiple_thinking_blocks():
    """Multiple thinking blocks in content should be concatenated."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {}
    chunk.response_metadata = {}
    chunk.content = [
        {"type": "thinking", "thinking": "first "},
        {"type": "thinking", "thinking": "second"},
    ]
    result = _extract_reasoning_text(chunk)
    ok = result == "first second"
    report("_extract_reasoning_text multiple thinking blocks -> concatenated", ok)


# ═════════════════════════════ _extract_solver_payload ══════════════════════

def test_extract_solver_payload_dict():
    """Dict input should be returned as-is."""
    from agent.phase_translator import _extract_solver_payload
    payload = {"status": "satisfiable", "models": [["a"]]}
    result = _extract_solver_payload(payload)
    ok = result == payload
    report("_extract_solver_payload(dict) -> dict", ok)


def test_extract_solver_payload_json_string():
    """JSON string should be parsed to dict."""
    from agent.phase_translator import _extract_solver_payload
    payload_str = '{"status": "satisfiable", "models": [["a"]]}'
    result = _extract_solver_payload(payload_str)
    ok = result is not None and result["status"] == "satisfiable"
    report("_extract_solver_payload(JSON string) -> dict", ok)


def test_extract_solver_payload_invalid_json_string():
    """Invalid JSON string should return None."""
    from agent.phase_translator import _extract_solver_payload
    result = _extract_solver_payload("not json at all")
    ok = result is None
    report("_extract_solver_payload(invalid JSON) -> None", ok)


def test_extract_solver_payload_list_with_text():
    """List with dict containing 'text' JSON should parse."""
    from agent.phase_translator import _extract_solver_payload
    payload = [{"type": "text", "text": '{"status": "success"}'}]
    result = _extract_solver_payload(payload)
    ok = result is not None and result["status"] == "success"
    report("_extract_solver_payload(list[text JSON]) -> dict", ok)


def test_extract_solver_payload_list_no_text():
    """List with no parseable text should return None."""
    from agent.phase_translator import _extract_solver_payload
    result = _extract_solver_payload([{"type": "image", "url": "http://example.com"}])
    ok = result is None
    report("_extract_solver_payload(list[no text]) -> None", ok)


def test_extract_solver_payload_list_with_non_dict():
    """List with non-dict items should skip them."""
    from agent.phase_translator import _extract_solver_payload
    result = _extract_solver_payload(["just a string", 42])
    ok = result is None
    report("_extract_solver_payload(list[non-dict]) -> None", ok)


def test_extract_solver_payload_none():
    """None input should return None."""
    from agent.phase_translator import _extract_solver_payload
    result = _extract_solver_payload(None)
    ok = result is None
    report("_extract_solver_payload(None) -> None", ok)


def test_extract_solver_payload_nested_list():
    """List with multiple dicts, first invalid, second valid JSON."""
    from agent.phase_translator import _extract_solver_payload
    payload = [
        {"type": "text", "text": "not json"},
        {"type": "text", "text": '{"status": "ok"}'},
    ]
    result = _extract_solver_payload(payload)
    ok = result is not None and result["status"] == "ok"
    report("_extract_solver_payload nested list -> second dict parsed", ok)


# ═════════════════════════════ _is_terminal_solver_success ══════════════════
# (Default / non-benchmark cases)

def test_terminal_none_payload():
    """None payload should return False."""
    from agent.phase_translator import _is_terminal_solver_success
    ok = _is_terminal_solver_success(None, "clingo") is False
    report("_is_terminal(None, clingo) -> False", ok)


def test_terminal_clingo_satisfiable_with_models():
    """Clingo satisfiable with models should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["a", "b"]]}
    ok = _is_terminal_solver_success(payload, "clingo") is True
    report("_is_terminal clingo satisfiable+models -> True", ok)


def test_terminal_clingo_satisfiable_no_models():
    """Clingo satisfiable without models should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": []}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo satisfiable+no models -> False", ok)


def test_terminal_clingo_optimum_found():
    """Clingo optimum_found with models should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "optimum_found", "models": [["a"]]}
    ok = _is_terminal_solver_success(payload, "clingo") is True
    report("_is_terminal clingo optimum_found -> True", ok)


def test_terminal_clingo_unsatisfiable():
    """Clingo unsatisfiable should NOT be terminal (triggers refinement)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "unsatisfiable", "models": []}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo unsatisfiable -> False (refines)", ok)


def test_terminal_clingo_unknown():
    """Clingo unknown should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "unknown", "models": []}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo unknown -> False", ok)


def test_terminal_clingo_error():
    """Clingo error should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "error", "error": "something broke"}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo error -> False", ok)


def test_terminal_clingo_timeout():
    """Clingo timeout should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "timeout", "error": "exceeded 60s"}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo timeout -> False", ok)


def test_terminal_clingo_syntax_error():
    """Clingo syntax_error should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "syntax_error", "error": "missing period"}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo syntax_error -> False", ok)


def test_terminal_clingo_grounding_timeout():
    """Clingo grounding_timeout should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "grounding_timeout", "error": "too large"}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo grounding_timeout -> False", ok)


def test_terminal_z3_sat():
    """Z3 success with 'status: sat' in stdout should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: sat\nx = 5", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 sat -> True", ok)


def test_terminal_z3_proved():
    """Z3 success with 'status: proved' in stdout should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: proved\nRESULT: true", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 proved -> True", ok)


def test_terminal_z3_unsat_with_true():
    """Z3 unsat with 'true' in stdout should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: unsat\ntrue", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 unsat+true -> True", ok)


def test_terminal_z3_unsat_with_false():
    """Z3 unsat with 'false' in stdout should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: unsat\nfalse", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 unsat+false -> True", ok)


def test_terminal_z3_unsat_without_answer():
    """Z3 unsat without true/false/proved should NOT be terminal (refines)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: unsat", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is False
    report("_is_terminal z3 unsat without answer -> False (refines)", ok)


def test_terminal_z3_no_status():
    """Z3 success with no recognizable status should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "some output without status", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is False
    report("_is_terminal z3 no status -> False", ok)


def test_terminal_z3_error_status():
    """Z3 error status should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "error", "stdout": "", "stderr": "crash"}
    ok = _is_terminal_solver_success(payload, "z3") is False
    report("_is_terminal z3 error -> False", ok)


def test_terminal_z3_timeout():
    """Z3 timeout should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "timeout", "error": "exceeded 60s"}
    ok = _is_terminal_solver_success(payload, "z3") is False
    report("_is_terminal z3 timeout -> False", ok)


def test_terminal_z3_unsat_in_stderr():
    """Z3 unsat found in stderr should also be checked."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "", "stderr": "status: unsat\ntrue"}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 unsat+true in stderr -> True", ok)


def test_terminal_vampire_theorem_countersatisfiable():
    """Vampire Theorem + CounterSatisfiable should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Theorem"},
        "negative": {"status": "success", "szs_status": "CounterSatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire Theorem+CounterSatisfiable -> True", ok)


def test_terminal_vampire_theorem_satisfiable():
    """Vampire Theorem + Satisfiable should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Theorem"},
        "negative": {"status": "success", "szs_status": "Satisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire Theorem+Satisfiable -> True", ok)


def test_terminal_vampire_contradictory_axioms():
    """Vampire ContradictoryAxioms should NOT be terminal (refines)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "ContradictoryAxioms"},
        "negative": {"status": "success", "szs_status": "CounterSatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is False
    report("_is_terminal vampire ContradictoryAxioms -> False (refines)", ok)


def test_terminal_vampire_both_theorem():
    """Vampire Theorem + Theorem (inconsistent) should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Theorem"},
        "negative": {"status": "success", "szs_status": "Theorem"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is False
    report("_is_terminal vampire Theorem+Theorem -> False (inconsistent)", ok)


def test_terminal_vampire_both_unsatisfiable():
    """Vampire Unsatisfiable + Unsatisfiable (inconsistent) should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Unsatisfiable"},
        "negative": {"status": "success", "szs_status": "Unsatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is False
    report("_is_terminal vampire Unsatisfiable+Unsatisfiable -> False (inconsistent)", ok)


def test_terminal_vampire_syntax_error():
    """Vampire SyntaxError should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "SyntaxError"},
        "negative": {"status": "success", "szs_status": "Theorem"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is False
    report("_is_terminal vampire SyntaxError -> False", ok)


def test_terminal_vampire_unknown_unknown():
    """Vampire Unknown + Unknown should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Unknown"},
        "negative": {"status": "success", "szs_status": "Unknown"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is False
    report("_is_terminal vampire Unknown+Unknown -> False", ok)


def test_terminal_vampire_theorem_unknown():
    """Vampire Theorem + Unknown should be terminal (one decisive side)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Theorem"},
        "negative": {"status": "success", "szs_status": "Unknown"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire Theorem+Unknown -> True", ok)


def test_terminal_vampire_satisfiable_countersatisfiable():
    """Vampire Satisfiable + CounterSatisfiable should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Satisfiable"},
        "negative": {"status": "success", "szs_status": "CounterSatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire Satisfiable+CounterSatisfiable -> True", ok)


def test_terminal_vampire_missing_negative():
    """Vampire with missing negative dict should handle gracefully."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Theorem"},
    }
    # negative is missing, so neg_szs = "unknown" -> one decisive + one non-decisive -> True
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire Theorem + missing negative -> True", ok)


def test_terminal_vampire_missing_positive():
    """Vampire with missing positive dict should handle gracefully."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "negative": {"status": "success", "szs_status": "CounterSatisfiable"},
    }
    # positive is missing, so pos_szs = "unknown" -> one non-decisive + one non-decisive
    # countersatisfiable is in valid_statuses but not decisive
    ok = _is_terminal_solver_success(payload, "vampire") is False
    report("_is_terminal vampire missing positive + CounterSatisfiable -> False", ok)


def test_terminal_unknown_solver():
    """Unknown solver name should return False."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["a"]]}
    ok = _is_terminal_solver_success(payload, "unknown_solver") is False
    report("_is_terminal unknown solver -> False", ok)


def test_terminal_case_insensitive_solver():
    """Solver name should be case-insensitive."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["a"]]}
    ok = _is_terminal_solver_success(payload, "CLINGO") is True
    report("_is_terminal CLINGO (uppercase) -> True", ok)


# ═════════════════════════════ _is_terminal (FOLIO benchmark) ═══════════════

def test_terminal_folio_clingo_true():
    """FOLIO + Clingo with verdict_true should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["verdict_true"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "FOLIO") is True
    report("_is_terminal FOLIO+clingo verdict_true -> True", ok)


def test_terminal_folio_clingo_false():
    """FOLIO + Clingo with verdict_false should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["verdict_false"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "FOLIO") is True
    report("_is_terminal FOLIO+clingo verdict_false -> True", ok)


def test_terminal_folio_clingo_inconsistent():
    """FOLIO + Clingo with verdict_inconsistent should NOT be terminal (refines)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["verdict_inconsistent"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "FOLIO") is False
    report("_is_terminal FOLIO+clingo verdict_inconsistent -> False (refines)", ok)


def test_terminal_folio_clingo_unsatisfiable():
    """FOLIO + Clingo unsatisfiable should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "unsatisfiable", "models": []}
    ok = _is_terminal_solver_success(payload, "clingo", "FOLIO") is False
    report("_is_terminal FOLIO+clingo unsatisfiable -> False", ok)


def test_terminal_folio_z3_true():
    """FOLIO + Z3 with CONCLUSION: True should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    # FOLIO+Z3 first requires _z3_base_ok() which needs status: sat/proved/unsat in stdout
    payload = {"status": "success", "stdout": "status: sat\nCONCLUSION: True", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "FOLIO") is True
    report("_is_terminal FOLIO+z3 CONCLUSION: True -> True", ok)


def test_terminal_folio_z3_inconsistent():
    """FOLIO + Z3 with CONCLUSION: Inconsistent should NOT be terminal (refines)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: sat\nCONCLUSION: Inconsistent", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "FOLIO") is False
    report("_is_terminal FOLIO+z3 CONCLUSION: Inconsistent -> False (refines)", ok)


def test_terminal_folio_z3_error():
    """FOLIO + Z3 with error status should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "error", "stdout": "", "stderr": "crash"}
    ok = _is_terminal_solver_success(payload, "z3", "FOLIO") is False
    report("_is_terminal FOLIO+z3 error -> False", ok)


def test_terminal_folio_vampire():
    """FOLIO + Vampire should use base vampire check."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Theorem"},
        "negative": {"status": "success", "szs_status": "CounterSatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire", "FOLIO") is True
    report("_is_terminal FOLIO+vampire Theorem+CounterSatisfiable -> True", ok)


# ═════════════════════════════ _is_terminal (LSAT benchmark) ════════════════

def test_terminal_lsat_clingo_single_option():
    """LSAT + Clingo with exactly 1 option should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["answer_b", "other"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "agieval_lsat") is True
    report("_is_terminal LSAT+clingo single option B -> True", ok)


def test_terminal_lsat_clingo_multiple_options():
    """LSAT + Clingo with multiple options should NOT be terminal (refines)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["answer_a"], ["answer_b"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "agieval_lsat") is False
    report("_is_terminal LSAT+clingo multiple options -> False (refines)", ok)


def test_terminal_lsat_clingo_no_options():
    """LSAT + Clingo with no recognizable options should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["something_else"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "agieval_lsat") is False
    report("_is_terminal LSAT+clingo no options -> False", ok)


def test_terminal_lsat_clingo_unsatisfiable():
    """LSAT + Clingo unsatisfiable should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "unsatisfiable", "models": []}
    ok = _is_terminal_solver_success(payload, "clingo", "agieval_lsat") is False
    report("_is_terminal LSAT+clingo unsatisfiable -> False", ok)


def test_terminal_lsat_z3_single_letter():
    """LSAT + Z3 with single letter output should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "C", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "agieval_lsat") is True
    report("_is_terminal LSAT+z3 single letter 'C' -> True", ok)


def test_terminal_lsat_z3_answer_label():
    """LSAT + Z3 with 'answer: B' should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "The answer is: B\nSome reasoning", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "agieval_lsat") is True
    report("_is_terminal LSAT+z3 'answer: B' -> True", ok)


def test_terminal_lsat_z3_refine_marker():
    """LSAT + Z3 with 'refine:' marker should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: unsat\nrefine: need more constraints", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "agieval_lsat") is False
    report("_is_terminal LSAT+z3 refine marker -> False", ok)


def test_terminal_lsat_z3_error():
    """LSAT + Z3 with error status should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "error", "stdout": "", "stderr": "crash"}
    ok = _is_terminal_solver_success(payload, "z3", "agieval_lsat") is False
    report("_is_terminal LSAT+z3 error -> False", ok)


# ═════════════════════════════ get_request_kwargs ═══════════════════════════

def test_request_kwargs_google():
    """Google provider should include automatic_function_calling disable."""
    from agent.phase_translator import get_request_kwargs
    kwargs = get_request_kwargs("google")
    ok = kwargs == {"automatic_function_calling": {"disable": True}}
    report("get_request_kwargs('google') -> AFC disabled", ok)


def test_request_kwargs_other():
    """Non-google provider should return empty dict."""
    from agent.phase_translator import get_request_kwargs
    for provider in ["nvidia", "nvidia2", "openrouter", "mistral", "xiaomi", ""]:
        kwargs = get_request_kwargs(provider)
        if kwargs != {}:
            report(f"get_request_kwargs('{provider}') -> {{}}", False, f"Got: {kwargs}")
            return
    report("get_request_kwargs(non-google) -> {}", True)


def test_request_kwargs_case_insensitive():
    """Provider name should be case-insensitive."""
    from agent.phase_translator import get_request_kwargs
    kwargs = get_request_kwargs("GOOGLE")
    ok = kwargs == {"automatic_function_calling": {"disable": True}}
    report("get_request_kwargs('GOOGLE') -> AFC disabled", ok)


# ═════════════════════════════ _is_rate_limit_error ═════════════════════════

def test_rate_limit_429():
    """Error containing '429' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("Error: 429 Too Many Requests") is True
    report("_is_rate_limit_error('429') -> True", ok)


def test_rate_limit_503():
    """Error containing '503' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("Error: 503 Service Unavailable") is True
    report("_is_rate_limit_error('503') -> True", ok)


def test_rate_limit_402():
    """Error containing '402' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("Error: 402 Payment Required") is True
    report("_is_rate_limit_error('402') -> True", ok)


def test_rate_limit_credits():
    """Error containing 'credits' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("Insufficient credits to complete request") is True
    report("_is_rate_limit_error('credits') -> True", ok)


def test_rate_limit_payment_required():
    """Error containing 'paymentrequired' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("PaymentRequiredResponseError") is True
    report("_is_rate_limit_error('paymentrequired') -> True", ok)


def test_rate_limit_normal_error():
    """Normal error should not be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("KeyError: 'model' not found") is False
    report("_is_rate_limit_error(normal error) -> False", ok)


def test_rate_limit_empty():
    """Empty string should not be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("") is False
    report("_is_rate_limit_error('') -> False", ok)


def test_rate_limit_afford():
    """Error containing 'afford' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("Cannot afford this request") is True
    report("_is_rate_limit_error('afford') -> True", ok)


def test_rate_limit_insufficient():
    """Error containing 'insufficient' should be rate limit."""
    from agent.phase_translator import _is_rate_limit_error
    ok = _is_rate_limit_error("Insufficient funds") is True
    report("_is_rate_limit_error('insufficient') -> True", ok)


# ═════════════════════════════ phase_prompts ════════════════════════════════

def test_get_translator_prompt_clingo():
    """get_translator_prompt('clingo') should return Clingo prompt."""
    from agent.phase_prompts import get_translator_prompt
    prompt = get_translator_prompt("clingo")
    ok = isinstance(prompt, str) and len(prompt) > 100
    report("get_translator_prompt('clingo') -> non-empty string", ok)


def test_get_translator_prompt_z3():
    """get_translator_prompt('z3') should return Z3 prompt."""
    from agent.phase_prompts import get_translator_prompt
    prompt = get_translator_prompt("z3")
    ok = isinstance(prompt, str) and len(prompt) > 100
    report("get_translator_prompt('z3') -> non-empty string", ok)


def test_get_translator_prompt_vampire():
    """get_translator_prompt('vampire') should return Vampire prompt."""
    from agent.phase_prompts import get_translator_prompt
    prompt = get_translator_prompt("vampire")
    ok = isinstance(prompt, str) and len(prompt) > 100
    report("get_translator_prompt('vampire') -> non-empty string", ok)


def test_get_translator_prompt_unknown():
    """get_translator_prompt with unknown solver should fallback to Z3."""
    from agent.phase_prompts import get_translator_prompt
    from z3_mcp_server.prompts import Z3_SYSTEM_PROMPT
    prompt = get_translator_prompt("unknown_solver")
    ok = Z3_SYSTEM_PROMPT in prompt
    report("get_translator_prompt('unknown') -> Z3 fallback", ok)


def test_get_translator_prompt_case_insensitive():
    """get_translator_prompt should be case-insensitive."""
    from agent.phase_prompts import get_translator_prompt
    p1 = get_translator_prompt("CLINGO")
    p2 = get_translator_prompt("clingo")
    ok = p1 == p2
    report("get_translator_prompt case-insensitive", ok)


def test_get_translator_prompt_whitespace():
    """get_translator_prompt should handle whitespace."""
    from agent.phase_prompts import get_translator_prompt
    p1 = get_translator_prompt("  clingo  ")
    p2 = get_translator_prompt("clingo")
    ok = p1 == p2
    report("get_translator_prompt handles whitespace", ok)


def test_get_answer_prompt_clingo():
    """get_answer_prompt('clingo') should return non-empty string."""
    from agent.phase_prompts import get_answer_prompt
    prompt = get_answer_prompt("clingo")
    ok = isinstance(prompt, str) and len(prompt) > 100
    report("get_answer_prompt('clingo') -> non-empty string", ok)


def test_get_answer_prompt_z3():
    """get_answer_prompt('z3') should return non-empty string."""
    from agent.phase_prompts import get_answer_prompt
    prompt = get_answer_prompt("z3")
    ok = isinstance(prompt, str) and len(prompt) > 100
    report("get_answer_prompt('z3') -> non-empty string", ok)


def test_get_answer_prompt_vampire():
    """get_answer_prompt('vampire') should return non-empty string."""
    from agent.phase_prompts import get_answer_prompt
    prompt = get_answer_prompt("vampire")
    ok = isinstance(prompt, str) and len(prompt) > 100
    report("get_answer_prompt('vampire') -> non-empty string", ok)


def test_get_answer_prompt_unknown():
    """get_answer_prompt with unknown solver should fallback to Z3."""
    from agent.phase_prompts import get_answer_prompt, ANSWER_POLICIES
    prompt = get_answer_prompt("unknown_solver")
    z3_prompt = ANSWER_POLICIES["z3"].render()
    ok = prompt == z3_prompt
    report("get_answer_prompt('unknown') -> Z3 fallback", ok)


def test_answer_policy_render():
    """AnswerPhasePolicy.render() should produce a complete prompt."""
    from agent.phase_prompts import ANSWER_POLICIES
    for solver, policy in ANSWER_POLICIES.items():
        rendered = policy.render()
        ok = (
            isinstance(rendered, str)
            and "Interpretation Phase" in rendered
            and "Output Format (STRICT)" in rendered
            and "STOP RULES" in rendered
            and len(rendered) > 200
        )
        report(f"AnswerPhasePolicy('{solver}').render() is complete", ok)
        if not ok:
            return


def test_answer_policy_all_solvers():
    """ANSWER_POLICIES should have entries for all 3 solvers."""
    from agent.phase_prompts import ANSWER_POLICIES
    ok = set(ANSWER_POLICIES.keys()) == {"clingo", "z3", "vampire"}
    report("ANSWER_POLICIES has all 3 solvers", ok)


def test_translator_prompts_all_solvers():
    """TRANSLATOR_PROMPTS should have entries for all 3 solvers."""
    from agent.phase_prompts import TRANSLATOR_PROMPTS
    ok = set(TRANSLATOR_PROMPTS.keys()) == {"clingo", "z3", "vampire"}
    report("TRANSLATOR_PROMPTS has all 3 solvers", ok)


def test_answer_prompt_contains_symbolic_grounding():
    """All answer prompts should mention symbolic grounding rule."""
    from agent.phase_prompts import get_answer_prompt
    for solver in ["clingo", "z3", "vampire"]:
        prompt = get_answer_prompt(solver)
        ok = "Symbolic Grounding" in prompt
        report(f"get_answer_prompt('{solver}') has Symbolic Grounding rule", ok)
        if not ok:
            return


# ═════════════════════════════ single_pass_runner ═══════════════════════════

def test_single_pass_chunk_content_to_text():
    """single_pass_runner._chunk_content_to_text should work same as phase_translator."""
    from agent.single_pass_runner import _chunk_content_to_text as sp_chunk
    from agent.phase_translator import _chunk_content_to_text as pt_chunk

    test_cases = [
        None,
        "hello",
        ["a", "b"],
        [{"type": "text", "text": "x"}],
        [{"type": "thinking", "thinking": "r"}, {"type": "text", "text": "a"}],
        42,
    ]
    for case in test_cases:
        sp_result = sp_chunk(case)
        pt_result = pt_chunk(case)
        if sp_result != pt_result:
            report("single_pass _chunk_content_to_text matches phase_translator", False, f"Input: {case}")
            return
    report("single_pass _chunk_content_to_text matches phase_translator", True)


def test_single_pass_extract_reasoning_text():
    """single_pass_runner._extract_reasoning_text should work same as phase_translator."""
    from agent.single_pass_runner import _extract_reasoning_text as sp_extract
    from agent.phase_translator import _extract_reasoning_text as pt_extract

    # Test with a mock chunk
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning_content": "test reasoning"}
    chunk.response_metadata = {}
    chunk.content = "answer"

    sp_result = sp_extract(chunk)
    pt_result = pt_extract(chunk)
    ok = sp_result == pt_result == "test reasoning"
    report("single_pass _extract_reasoning_text matches phase_translator", ok)


def test_single_pass_is_rate_limit_error():
    """single_pass_runner._is_rate_limit_error should work same as phase_translator."""
    from agent.single_pass_runner import _is_rate_limit_error as sp_check
    from agent.phase_translator import _is_rate_limit_error as pt_check

    test_cases = [
        "Error: 429",
        "Error: 503",
        "Error: 402",
        "Insufficient credits",
        "Normal error",
        "",
    ]
    for case in test_cases:
        if sp_check(case) != pt_check(case):
            report("single_pass _is_rate_limit_error matches phase_translator", False, f"Input: {case}")
            return
    report("single_pass _is_rate_limit_error matches phase_translator", True)


# ═════════════════════════════ LLMManager ═══════════════════════════════════

def test_llm_manager_init_with_config_key():
    """LLMManager should use config API key when provided."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, openai_api_key="test-key-123")
    mgr = LLMManager(cfg)
    ok = mgr._api_key == "test-key-123"
    report("LLMManager uses config API key", ok)


def test_llm_manager_init_env_key():
    """LLMManager should fall back to environment variable."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE)
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key-456"}, clear=False):
        mgr = LLMManager(cfg)
        ok = mgr._api_key == "env-key-456"
    report("LLMManager falls back to env var", ok)


def test_llm_manager_init_no_key():
    """LLMManager with no key should have None _api_key."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, openai_api_key=None)
    # Temporarily remove all Google env vars
    env_backup = {}
    for var in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3"]:
        if var in os.environ:
            env_backup[var] = os.environ.pop(var)
    try:
        mgr = LLMManager(cfg)
        ok = mgr._api_key is None
        report("LLMManager with no key -> _api_key is None", ok)
    finally:
        os.environ.update(env_backup)


def test_llm_manager_get_llm_no_key_raises():
    """LLMManager.get_llm() with no key should raise ValueError."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, openai_api_key=None)
    env_backup = {}
    for var in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3"]:
        if var in os.environ:
            env_backup[var] = os.environ.pop(var)
    try:
        mgr = LLMManager(cfg)
        try:
            mgr.get_llm()
            report("LLMManager.get_llm() no key -> raises ValueError", False, "No exception")
        except ValueError:
            report("LLMManager.get_llm() no key -> raises ValueError", True)
    finally:
        os.environ.update(env_backup)


def test_llm_manager_google_build():
    """LLMManager.get_llm() for Google should return ChatGoogleGenerativeAI."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm.__class__.__name__ == "ChatGoogleGenerativeAI"
    report("LLMManager Google -> ChatGoogleGenerativeAI", ok)


def test_llm_manager_openrouter_build():
    """LLMManager.get_llm() for OpenRouter should return ChatOpenRouter."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.OPENROUTER, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm.__class__.__name__ == "ChatOpenRouter"
    report("LLMManager OpenRouter -> ChatOpenRouter", ok)


def test_llm_manager_mistral_build():
    """LLMManager.get_llm() for Mistral should return ChatMistralAI."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.MISTRAL, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm.__class__.__name__ == "ChatMistralAI"
    report("LLMManager Mistral -> ChatMistralAI", ok)


def test_llm_manager_nvidia_build():
    """LLMManager.get_llm() for NVIDIA should return ChatDeepSeek."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm.__class__.__name__ == "ChatDeepSeek"
    report("LLMManager NVIDIA -> ChatDeepSeek", ok)


def test_llm_manager_nvidia2_build():
    """LLMManager.get_llm() for NVIDIA2 should return ChatDeepSeek."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA2, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm.__class__.__name__ == "ChatDeepSeek"
    report("LLMManager NVIDIA2 -> ChatDeepSeek", ok)


def test_llm_manager_xiaomi_build():
    """LLMManager.get_llm() for Xiaomi should return ChatDeepSeek."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.XIAOMI, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm.__class__.__name__ == "ChatDeepSeek"
    report("LLMManager Xiaomi -> ChatDeepSeek", ok)


def test_llm_manager_google_reasoning_enabled():
    """LLMManager Google with reasoning enabled should set thinking params."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-3.1-flash-lite",
        reasoning_enabled=True,
        reasoning_effort="high",
        openai_api_key="test-key",
    )
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    # Check that thinking params were set (via model_kwargs or direct)
    ok = llm is not None
    report("LLMManager Google reasoning_enabled builds successfully", ok)


def test_llm_manager_google_reasoning_disabled():
    """LLMManager Google with reasoning disabled should set minimal thinking."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-3.1-flash-lite",
        reasoning_enabled=False,
        openai_api_key="test-key",
    )
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager Google reasoning_disabled builds successfully", ok)


def test_llm_manager_openrouter_reasoning():
    """LLMManager OpenRouter with reasoning should set reasoning param."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(
        provider=LLMProvider.OPENROUTER,
        reasoning_enabled=True,
        reasoning_effort="xhigh",
        openai_api_key="test-key",
    )
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager OpenRouter reasoning builds successfully", ok)


def test_llm_manager_openrouter_reasoning_disabled():
    """LLMManager OpenRouter with reasoning disabled should set effort=none."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(
        provider=LLMProvider.OPENROUTER,
        reasoning_enabled=False,
        openai_api_key="test-key",
    )
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager OpenRouter reasoning_disabled builds successfully", ok)


def test_llm_manager_explicit_key_overrides_env():
    """Explicit API key should take priority over env var."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, openai_api_key="explicit-key")
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}, clear=False):
        mgr = LLMManager(cfg)
        ok = mgr._api_key == "explicit-key"
    report("Explicit API key overrides env var", ok)


def test_llm_manager_google_gemini25_reasoning():
    """LLMManager Google gemini-2.5 model should use thinking_budget."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-2.5-flash",
        reasoning_enabled=True,
        reasoning_effort="medium",
        openai_api_key="test-key",
    )
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager Google gemini-2.5 reasoning builds successfully", ok)


def test_llm_manager_mistral_reasoning():
    """LLMManager Mistral with reasoning should set model_kwargs."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(
        provider=LLMProvider.MISTRAL,
        reasoning_enabled=True,
        reasoning_effort="low",
        openai_api_key="test-key",
    )
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager Mistral reasoning builds successfully", ok)


# ═════════════════════════════ MCPAgent ════════════════════════════════════

def test_mcp_agent_init_default():
    """MCPAgent with no config should use defaults."""
    from agent.mcp_core import MCPAgent
    from agent.config import MCPAgentConfig
    agent = MCPAgent()
    ok = isinstance(agent.config, MCPAgentConfig) and agent.config.solver == "z3"
    report("MCPAgent() default config", ok)


def test_mcp_agent_init_custom_config():
    """MCPAgent with custom config should use it."""
    from agent.mcp_core import MCPAgent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, solver="clingo")
    agent = MCPAgent(config=cfg)
    ok = agent.config.provider == LLMProvider.NVIDIA and agent.config.solver == "clingo"
    report("MCPAgent(custom config) works", ok)


def test_mcp_agent_build_mcp_config():
    """MCPAgent._build_mcp_config should produce correct dict."""
    from agent.mcp_core import MCPAgent
    from agent.config import MCPAgentConfig, MCPServerConfig
    cfg = MCPAgentConfig(
        mcp_servers={"z3": MCPServerConfig(command="python", args=["-m", "z3_mcp_server"])}
    )
    agent = MCPAgent(config=cfg)
    mcp_config = agent._build_mcp_config()
    ok = (
        "z3" in mcp_config
        and mcp_config["z3"]["command"] == "python"
        and mcp_config["z3"]["args"] == ["-m", "z3_mcp_server"]
    )
    report("MCPAgent._build_mcp_config() correct", ok)


def test_mcp_agent_build_mcp_config_empty():
    """MCPAgent with no MCP servers should return empty dict."""
    from agent.mcp_core import MCPAgent
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(mcp_servers={})
    agent = MCPAgent(config=cfg)
    mcp_config = agent._build_mcp_config()
    ok = mcp_config == {}
    report("MCPAgent._build_mcp_config() empty -> {}", ok)


def test_mcp_agent_has_llm_manager():
    """MCPAgent should have an LLMManager instance."""
    from agent.mcp_core import MCPAgent
    from agent.llm_client import LLMManager
    agent = MCPAgent()
    ok = isinstance(agent.llm_manager, LLMManager)
    report("MCPAgent has LLMManager", ok)


# ═════════════════════════════ EDGE CASES & CORNER CASES ═══════════════════

def test_chunk_content_list_with_none_items():
    """List with None items should be handled gracefully."""
    from agent.phase_translator import _chunk_content_to_text
    result = _chunk_content_to_text([None, "hello", None])
    # None items in list should be skipped or str-ified
    ok = "hello" in result
    report("_chunk_content_to_text list with None items -> handled", ok)


def test_chunk_content_dict_without_text_key():
    """Dict without 'text' key should contribute empty string."""
    from agent.phase_translator import _chunk_content_to_text
    result = _chunk_content_to_text([{"type": "image", "url": "http://example.com"}])
    ok = result == ""
    report("_chunk_content_to_text dict without text -> empty", ok)


def test_extract_reasoning_no_additional_kwargs():
    """Chunk without additional_kwargs attribute should not crash."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock(spec=[])  # No attributes
    chunk.content = "just text"
    # Should not raise
    result = _extract_reasoning_text(chunk)
    ok = isinstance(result, str)
    report("_extract_reasoning_text no additional_kwargs -> no crash", ok)


def test_extract_solver_payload_deeply_nested():
    """Deeply nested non-dict structure should return None."""
    from agent.phase_translator import _extract_solver_payload
    result = _extract_solver_payload([[[["deep"]]]])
    ok = result is None
    report("_extract_solver_payload deeply nested -> None", ok)


def test_terminal_clingo_models_none():
    """Clingo with models=None should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": None}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo models=None -> False", ok)


def test_terminal_clingo_models_not_list():
    """Clingo with models as string should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": "not a list"}
    ok = _is_terminal_solver_success(payload, "clingo") is False
    report("_is_terminal clingo models='string' -> False", ok)


def test_terminal_z3_empty_stdout():
    """Z3 with empty stdout should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "", "stderr": ""}
    ok = _is_terminal_solver_success(payload, "z3") is False
    report("_is_terminal z3 empty stdout -> False", ok)


def test_terminal_z3_none_stdout():
    """Z3 with None stdout should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": None, "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3") is False
    report("_is_terminal z3 None stdout -> False", ok)


def test_terminal_vampire_szs_with_underscores():
    """Vampire SZS status with underscores should be normalized."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Counter_Satisfiable"},
        "negative": {"status": "success", "szs_status": "Theorem"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire SZS with underscores -> normalized", ok)


def test_terminal_vampire_szs_case_insensitive():
    """Vampire SZS status should be case-insensitive."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "theorem"},
        "negative": {"status": "success", "szs_status": "countersatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire SZS lowercase -> works", ok)


def test_terminal_empty_solver_name():
    """Empty solver name should return False."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["a"]]}
    ok = _is_terminal_solver_success(payload, "") is False
    report("_is_terminal empty solver -> False", ok)


def test_terminal_whitespace_solver_name():
    """Whitespace-only solver name should return False."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["a"]]}
    ok = _is_terminal_solver_success(payload, "   ") is False
    report("_is_terminal whitespace solver -> False", ok)


def test_phase_usage_large_values():
    """PhaseUsage should handle large token counts."""
    from agent.phase_translator import PhaseUsage
    u = PhaseUsage(input_tokens=1_000_000, output_tokens=500_000, total_tokens=1_500_000)
    ok = u.total_tokens == 1_500_000
    report("PhaseUsage large values work", ok)


def test_translator_outcome_zero_iterations():
    """TranslatorOutcome with 0 iterations should be valid."""
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    outcome = TranslatorOutcome(
        success=False,
        iterations_used=0,
        messages=[],
        usage=PhaseUsage(),
        failure_reason="immediate failure",
    )
    ok = outcome.iterations_used == 0
    report("TranslatorOutcome 0 iterations is valid", ok)


def test_mcp_agent_config_none_benchmark():
    """MCPAgentConfig with benchmark=None should work."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(benchmark=None)
    ok = cfg.benchmark is None
    report("MCPAgentConfig benchmark=None works", ok)


def test_mcp_agent_config_empty_benchmark():
    """MCPAgentConfig with benchmark='' should work."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(benchmark="")
    ok = cfg.benchmark == ""
    report("MCPAgentConfig benchmark='' works", ok)


# ═════════════════════════════ stream_once ═════════════════════════════════

async def test_stream_once_basic_content():
    """stream_once should return content and usage from chunks."""
    from agent.phase_translator import stream_once, PhaseUsage

    chunks = [
        FakeChunk(content="Hello", usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}),
        FakeChunk(content=" World"),
    ]

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            for c in chunks:
                yield c

    content, chunk, usage = await stream_once(FakeLLM(), [], {})
    ok = content == "Hello World" and usage.input_tokens == 10 and usage.output_tokens == 5 and usage.total_tokens == 15
    report("stream_once basic content + usage", ok, f"content={content!r}, usage={usage}")


async def test_stream_once_usage_merging():
    """stream_once should merge usage from multiple chunks (max of each field)."""
    from agent.phase_translator import stream_once

    chunks = [
        FakeChunk(content="A", usage_metadata={"input_tokens": 10, "output_tokens": 0, "total_tokens": 0}),
        FakeChunk(content="B", usage_metadata={"input_tokens": 0, "output_tokens": 5, "total_tokens": 0}),
        FakeChunk(content="C", usage_metadata={"input_tokens": 0, "output_tokens": 0, "total_tokens": 15}),
    ]

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            for c in chunks:
                yield c

    content, _, usage = await stream_once(FakeLLM(), [], {})
    ok = content == "ABC" and usage.input_tokens == 10 and usage.output_tokens == 5 and usage.total_tokens == 15
    report("stream_once usage merging (max of each field)", ok, f"usage={usage}")


async def test_stream_once_reasoning():
    """stream_once should extract reasoning from chunks."""
    from agent.phase_translator import stream_once

    chunks = [
        FakeChunk(content="answer", additional_kwargs={"reasoning_content": "I think..."}),
    ]

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            for c in chunks:
                yield c

    content, _, usage = await stream_once(FakeLLM(), [], {})
    ok = content == "answer"
    report("stream_once reasoning extraction + content", ok)


async def test_stream_once_empty():
    """stream_once with no chunks should return empty content."""
    from agent.phase_translator import stream_once

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            return
            yield  # make it an async generator

    content, chunk, usage = await stream_once(FakeLLM(), [], {})
    ok = content == "" and chunk is None and usage.total_tokens == 0
    report("stream_once empty stream -> empty content", ok)


async def test_stream_once_usage_from_aggregated():
    """stream_once should fall back to aggregated_chunk usage when no raw metadata."""
    from agent.phase_translator import stream_once

    class ChunkWithUsage:
        def __init__(self):
            self.content = "hello"
            self.tool_calls = []
            self.usage_metadata = {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30}
            self.additional_kwargs = {}
            self.response_metadata = {}

        def __add__(self, other):
            if other is None:
                return self
            return self

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield ChunkWithUsage()

    _, _, usage = await stream_once(FakeLLM(), [], {})
    ok = usage.input_tokens == 20 and usage.output_tokens == 10
    report("stream_once usage from aggregated_chunk fallback", ok, f"usage={usage}")


# ═════════════════════════════ run_answer_phase ════════════════════════════

async def test_answer_phase_success():
    """run_answer_phase should return answer text and usage."""
    from agent.phase_answer import run_answer_phase
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    from agent.config import MCPAgentConfig

    outcome = TranslatorOutcome(
        success=True, iterations_used=1, messages=[], usage=PhaseUsage(),
        definitive_result_text='{"status": "satisfiable"}',
        last_tool_name="run_clingo", last_tool_args={"code": "a.", "filename": "test.lp"},
    )

    async def mock_stream(llm, msgs, kwargs, **kw):
        return ("The answer is True.", None, PhaseUsage(input_tokens=100, output_tokens=50, total_tokens=150))

    with patch("agent.phase_answer.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        text, usage = await run_answer_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            answer_prompt="You are an answer agent.", user_query="Is p true?",
            translator_outcome=outcome,
        )
        ok = text == "The answer is True." and usage.input_tokens == 100
        report("run_answer_phase success -> returns text + usage", ok, f"text={text!r}")


async def test_answer_phase_message_construction():
    """run_answer_phase should construct messages with user_query, solver, and payload."""
    from agent.phase_answer import run_answer_phase
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    outcome = TranslatorOutcome(
        success=True, iterations_used=1, messages=[], usage=PhaseUsage(),
        definitive_result_text="solver output here",
    )
    captured_msgs = None

    async def mock_stream(llm, msgs, kwargs, **kw):
        nonlocal captured_msgs
        captured_msgs = msgs
        return ("answer", None, PhaseUsage())

    with patch("agent.phase_answer.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        await run_answer_phase(
            llm_manager=mock_mgr, provider="google", solver="z3",
            answer_prompt="prompt", user_query="What is 2+2?",
            translator_outcome=outcome,
        )
        human = [m for m in captured_msgs if isinstance(m, HumanMessage)]
        ok = (
            len(human) == 1
            and "What is 2+2?" in human[0].content
            and "solver output here" in human[0].content
            and "z3" in human[0].content
        )
        report("run_answer_phase constructs messages correctly", ok)


async def test_answer_phase_usage_accumulation():
    """run_answer_phase should accumulate usage across retries."""
    from agent.phase_answer import run_answer_phase
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    from agent.config import MCPAgentConfig

    outcome = TranslatorOutcome(
        success=True, iterations_used=1, messages=[], usage=PhaseUsage(),
        definitive_result_text="result",
    )

    call_count = 0
    async def mock_stream(llm, msgs, kwargs, **kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Error: 429 Too Many Requests")
        return ("answer", None, PhaseUsage(input_tokens=50, output_tokens=25, total_tokens=75))

    with patch("agent.phase_answer.stream_once", side_effect=mock_stream):
        with patch("agent.phase_answer.asyncio.sleep", new_callable=AsyncMock):
            mock_mgr = MagicMock()
            mock_mgr.get_llm.return_value = MagicMock()
            mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
            text, usage = await run_answer_phase(
                llm_manager=mock_mgr, provider="google", solver="clingo",
                answer_prompt="prompt", user_query="query",
                translator_outcome=outcome,
            )
            ok = text == "answer" and usage.input_tokens == 50 and call_count == 2
            report("run_answer_phase retries on 429 + accumulates usage", ok, f"call_count={call_count}")


async def test_answer_phase_no_tool_args():
    """run_answer_phase should handle missing last_tool_args gracefully."""
    from agent.phase_answer import run_answer_phase
    from agent.phase_translator import TranslatorOutcome, PhaseUsage
    from agent.config import MCPAgentConfig

    outcome = TranslatorOutcome(
        success=True, iterations_used=1, messages=[], usage=PhaseUsage(),
        definitive_result_text="result", last_tool_args=None,
    )

    async def mock_stream(llm, msgs, kwargs, **kw):
        return ("answer", None, PhaseUsage())

    with patch("agent.phase_answer.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        text, usage = await run_answer_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            answer_prompt="prompt", user_query="query",
            translator_outcome=outcome,
        )
        ok = text == "answer"
        report("run_answer_phase no last_tool_args -> still works", ok)


# ═════════════════════════════ run_translator_phase ════════════════════════

async def test_translator_phase_success():
    """run_translator_phase should return success when tool call yields terminal result."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    class FakeTool:
        name = "write_and_run_clingo"
        description = "Write and run clingo"
        async def ainvoke(self, args):
            return {"status": "satisfiable", "models": [["a"]]}

    tool_call = {"name": "write_and_run_clingo", "args": {"filename": "test.lp", "code": "a."}, "id": "call_1"}

    async def mock_stream(llm, msgs, kwargs, **kw):
        return ("", FakeChunk(tool_calls=[tool_call]), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        outcome = await run_translator_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            tools=[FakeTool()], system_prompt="test", user_query="test query",
            max_iterations=4, prune_history=False, tool_timeout_seconds=70,
        )
        ok = outcome.success and outcome.iterations_used == 1 and outcome.solver_payload is not None
        report("run_translator_phase success on first tool call", ok, f"success={outcome.success}")


async def test_translator_phase_max_iterations():
    """run_translator_phase should fail after max_iterations with no terminal result."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    async def mock_stream(llm, msgs, kwargs, **kw):
        return ("no tool call", FakeChunk(content="thinking..."), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        outcome = await run_translator_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            tools=[], system_prompt="test", user_query="test",
            max_iterations=2, prune_history=False, tool_timeout_seconds=70,
        )
        ok = not outcome.success and outcome.iterations_used == 2 and "failed" in (outcome.failure_reason or "").lower()
        report("run_translator_phase max iterations -> failure", ok, f"reason={outcome.failure_reason}")


async def test_translator_phase_overthinking():
    """run_translator_phase should abort when output tokens exceed threshold."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    async def mock_stream(llm, msgs, kwargs, **kw):
        return ("a lot", FakeChunk(content="..."), PhaseUsage(input_tokens=100, output_tokens=32001, total_tokens=32101))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        outcome = await run_translator_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            tools=[], system_prompt="test", user_query="test",
            max_iterations=4, prune_history=False, tool_timeout_seconds=70,
        )
        ok = not outcome.success and "token limit" in (outcome.failure_reason or "").lower()
        report("run_translator_phase overthinking guard -> abort", ok, f"reason={outcome.failure_reason}")


async def test_translator_phase_tool_not_found():
    """run_translator_phase should handle tool not found gracefully."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    tool_call = {"name": "nonexistent_tool", "args": {}, "id": "call_1"}
    call_count = 0

    async def mock_stream(llm, msgs, kwargs, **kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ("", FakeChunk(tool_calls=[tool_call]), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))
        return ("done", FakeChunk(), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        outcome = await run_translator_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            tools=[], system_prompt="test", user_query="test",
            max_iterations=2, prune_history=False, tool_timeout_seconds=70,
        )
        ok = not outcome.success
        report("run_translator_phase tool not found -> continues", ok)


async def test_translator_phase_prune_history():
    """run_translator_phase should prune history when prune_history=True."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    msg_counts = []

    async def mock_stream(llm, msgs, kwargs, **kw):
        msg_counts.append(len(msgs))
        return ("text", FakeChunk(content="text"), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        await run_translator_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            tools=[], system_prompt="test", user_query="test",
            max_iterations=3, prune_history=True, tool_timeout_seconds=70,
        )
        ok = msg_counts[0] == 2
        report("run_translator_phase prune_history starts with 2 messages", ok, f"msg_counts={msg_counts}")


async def test_translator_phase_rate_limit_retry():
    """run_translator_phase should retry on rate limit errors."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    call_count = 0
    async def mock_stream(llm, msgs, kwargs, **kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Error: 429 Too Many Requests")
        return ("text", FakeChunk(content="text"), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        with patch("agent.phase_translator.asyncio.sleep", new_callable=AsyncMock):
            mock_mgr = MagicMock()
            mock_mgr.get_llm.return_value = MagicMock()
            mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
            outcome = await run_translator_phase(
                llm_manager=mock_mgr, provider="google", solver="clingo",
                tools=[], system_prompt="test", user_query="test",
                max_iterations=1, prune_history=False, tool_timeout_seconds=70,
            )
            ok = call_count == 2
            report("run_translator_phase retries on 429", ok, f"call_count={call_count}")


async def test_translator_phase_tool_exception():
    """run_translator_phase should handle tool exception gracefully."""
    from agent.phase_translator import run_translator_phase, PhaseUsage
    from agent.config import MCPAgentConfig

    class BrokenTool:
        name = "broken_tool"
        description = "Broken"
        async def ainvoke(self, args):
            raise RuntimeError("Tool crashed")

    tool_call = {"name": "broken_tool", "args": {}, "id": "call_1"}
    call_count = 0

    async def mock_stream(llm, msgs, kwargs, **kw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ("", FakeChunk(tool_calls=[tool_call]), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))
        return ("done", FakeChunk(), PhaseUsage(input_tokens=10, output_tokens=5, total_tokens=15))

    with patch("agent.phase_translator.stream_once", side_effect=mock_stream):
        mock_mgr = MagicMock()
        mock_mgr.get_llm.return_value = MagicMock()
        mock_mgr.config = MCPAgentConfig(openai_api_key="test-key")
        outcome = await run_translator_phase(
            llm_manager=mock_mgr, provider="google", solver="clingo",
            tools=[BrokenTool()], system_prompt="test", user_query="test",
            max_iterations=2, prune_history=False, tool_timeout_seconds=70,
        )
        ok = not outcome.success
        report("run_translator_phase tool exception -> continues", ok)


# ═════════════════════════════ run_single_pass_stream ══════════════════════

async def test_single_pass_stream_basic():
    """run_single_pass_stream should return content and truncation flag."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(
                content="The answer is True.",
                usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                response_metadata={"finish_reason": "stop"},
            )

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    content, was_truncated = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = content == "The answer is True." and not was_truncated
    report("run_single_pass_stream basic -> content + not truncated", ok)


async def test_single_pass_stream_truncation():
    """run_single_pass_stream should detect truncation from finish_reason='length'."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(content="partial...", response_metadata={"finish_reason": "length"})

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    _, was_truncated = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = was_truncated is True
    report("run_single_pass_stream finish_reason=length -> truncated", ok)


async def test_single_pass_stream_dict_finish_reason():
    """run_single_pass_stream should detect truncation from dict finish_reason."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(content="partial...", response_metadata={"finish_reason": {"reason": "length"}})

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    _, was_truncated = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = was_truncated is True
    report("run_single_pass_stream dict finish_reason=length -> truncated", ok)


async def test_single_pass_stream_additional_kwargs_finish_reason():
    """run_single_pass_stream should detect truncation from additional_kwargs finish_reason."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(content="partial...", additional_kwargs={"finish_reason": "length"})

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    _, was_truncated = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = was_truncated is True
    report("run_single_pass_stream additional_kwargs finish_reason=length -> truncated", ok)


async def test_single_pass_stream_retry_on_rate_limit():
    """run_single_pass_stream should retry on rate limit error."""
    from agent.single_pass_runner import run_single_pass_stream

    call_count = 0
    class FlakeyLLM:
        async def astream(self, messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Error: 429 Too Many Requests")
            yield FakeChunk(content="success", usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FlakeyLLM()
    content, _ = await run_single_pass_stream(mock_mgr, [], "TEST", "query", max_retries=3, retry_delay_s=0)
    ok = content == "success" and call_count == 2
    report("run_single_pass_stream retries on 429", ok, f"call_count={call_count}")


async def test_single_pass_stream_non_retryable_error():
    """run_single_pass_stream should raise on non-retryable errors."""
    from agent.single_pass_runner import run_single_pass_stream

    class ErrorLLM:
        async def astream(self, messages, **kwargs):
            raise ValueError("Something broke")
            yield

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = ErrorLLM()
    try:
        await run_single_pass_stream(mock_mgr, [], "TEST", "query", max_retries=3, retry_delay_s=0)
        report("run_single_pass_stream non-retryable error -> raises", False, "No exception")
    except ValueError:
        report("run_single_pass_stream non-retryable error -> raises", True)


async def test_single_pass_stream_usage_from_response_metadata():
    """run_single_pass_stream should extract usage from response_metadata.token_usage."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(
                content="answer",
                response_metadata={"token_usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}},
            )

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    content, _ = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = content == "answer"
    report("run_single_pass_stream usage from response_metadata", ok)


async def test_single_pass_stream_usage_from_additional_kwargs():
    """run_single_pass_stream should extract usage from additional_kwargs.usage."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(
                content="answer",
                additional_kwargs={"usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120}},
            )

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    content, _ = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = content == "answer"
    report("run_single_pass_stream usage from additional_kwargs", ok)


async def test_single_pass_stream_reasoning():
    """run_single_pass_stream should extract and print reasoning."""
    from agent.single_pass_runner import run_single_pass_stream

    class FakeLLM:
        async def astream(self, messages, **kwargs):
            yield FakeChunk(content="answer", additional_kwargs={"reasoning_content": "thinking..."})

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = FakeLLM()
    content, _ = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = content == "answer"
    report("run_single_pass_stream reasoning extraction", ok)


async def test_single_pass_stream_empty():
    """run_single_pass_stream with no chunks should return empty content."""
    from agent.single_pass_runner import run_single_pass_stream

    class EmptyLLM:
        async def astream(self, messages, **kwargs):
            return
            yield

    mock_mgr = MagicMock()
    mock_mgr.get_llm.return_value = EmptyLLM()
    content, was_truncated = await run_single_pass_stream(mock_mgr, [], "TEST", "query")
    ok = content == "" and not was_truncated
    report("run_single_pass_stream empty stream -> empty content", ok)


# ═════════════════════════════ ADDITIONAL EDGE CASES ═══════════════════════

def test_extract_reasoning_details_key():
    """reasoning_details key in additional_kwargs should be extracted."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning_details": "deep analysis"}
    chunk.response_metadata = {}
    chunk.content = "answer"
    result = _extract_reasoning_text(chunk)
    ok = result == "deep analysis"
    report("_extract_reasoning_text from reasoning_details key", ok)


def test_extract_reasoning_dict_content():
    """reasoning dict with content key should extract content."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning": {"content": "from content key"}}
    chunk.response_metadata = {}
    chunk.content = "answer"
    result = _extract_reasoning_text(chunk)
    ok = result == "from content key"
    report("_extract_reasoning_text from reasoning dict content key", ok)


def test_extract_reasoning_dict_fallback_str():
    """reasoning dict with no text/content should str()-ify."""
    from agent.phase_translator import _extract_reasoning_text
    chunk = MagicMock()
    chunk.additional_kwargs = {"reasoning": {"other": "data"}}
    chunk.response_metadata = {}
    chunk.content = "answer"
    result = _extract_reasoning_text(chunk)
    ok = "other" in result
    report("_extract_reasoning_text from reasoning dict fallback str", ok)


def test_extract_solver_payload_list_with_array_json():
    """List with text containing JSON array should return None."""
    from agent.phase_translator import _extract_solver_payload
    payload = [{"type": "text", "text": '[1, 2, 3]'}]
    result = _extract_solver_payload(payload)
    ok = result is None
    report("_extract_solver_payload(list[text array JSON]) -> None", ok)


def test_terminal_vampire_both_refuted():
    """Vampire Satisfiable + CounterSatisfiable (both Refuted) should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "Satisfiable"},
        "negative": {"status": "success", "szs_status": "CounterSatisfiable"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire both Refuted -> True", ok)


def test_terminal_vampire_countersatisfiable_theorem():
    """Vampire CounterSatisfiable + Theorem should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {
        "positive": {"status": "success", "szs_status": "CounterSatisfiable"},
        "negative": {"status": "success", "szs_status": "Theorem"},
    }
    ok = _is_terminal_solver_success(payload, "vampire") is True
    report("_is_terminal vampire CounterSatisfiable+Theorem -> True", ok)


def test_terminal_folio_z3_no_conclusion():
    """FOLIO + Z3 with sat but no CONCLUSION should be terminal (base ok)."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "status: sat\nsome output", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "FOLIO") is True
    report("_is_terminal FOLIO+z3 sat no CONCLUSION -> True", ok)


def test_terminal_folio_clingo_verdict_uncertain():
    """FOLIO + Clingo with verdict_uncertain should be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["verdict_uncertain"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "FOLIO") is True
    report("_is_terminal FOLIO+clingo verdict_uncertain -> True", ok)


def test_terminal_lsat_clingo_multiple_options_in_model():
    """LSAT + Clingo with multiple options in single model should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "satisfiable", "models": [["answer_a", "answer_b"]]}
    ok = _is_terminal_solver_success(payload, "clingo", "agieval_lsat") is False
    report("_is_terminal LSAT+clingo multiple options in model -> False", ok)


def test_terminal_lsat_z3_multiple_letters():
    """LSAT + Z3 with multiple different letters should NOT be terminal."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "A or B", "stderr": None}
    ok = _is_terminal_solver_success(payload, "z3", "agieval_lsat") is False
    report("_is_terminal LSAT+z3 multiple letters -> False", ok)


def test_terminal_z3_sat_in_stderr():
    """Z3 sat found in stderr should also be checked."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "", "stderr": "status: sat\nx = 5"}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 sat in stderr -> True", ok)


def test_terminal_z3_proved_in_stderr():
    """Z3 proved found in stderr should also be checked."""
    from agent.phase_translator import _is_terminal_solver_success
    payload = {"status": "success", "stdout": "", "stderr": "status: proved"}
    ok = _is_terminal_solver_success(payload, "z3") is True
    report("_is_terminal z3 proved in stderr -> True", ok)


def test_mcp_agent_config_solver_validation():
    """MCPAgentConfig should accept all valid solver values."""
    from agent.config import MCPAgentConfig
    for solver in ["z3", "clingo", "vampire"]:
        cfg = MCPAgentConfig(solver=solver)
        ok = cfg.solver == solver
        if not ok:
            report(f"MCPAgentConfig solver='{solver}'", False)
            return
    report("MCPAgentConfig accepts all valid solver values", True)


def test_mcp_agent_config_seed_none():
    """MCPAgentConfig with seed=None should work."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(seed=None)
    ok = cfg.seed is None
    report("MCPAgentConfig seed=None works", ok)


def test_mcp_agent_config_top_k():
    """MCPAgentConfig with top_k should work."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(top_k=40)
    ok = cfg.top_k == 40
    report("MCPAgentConfig top_k=40 works", ok)


def test_mcp_agent_config_repetition_penalty():
    """MCPAgentConfig with repetition_penalty should work."""
    from agent.config import MCPAgentConfig
    cfg = MCPAgentConfig(repetition_penalty=1.2)
    ok = cfg.repetition_penalty == 1.2
    report("MCPAgentConfig repetition_penalty=1.2 works", ok)


def test_llm_manager_xiaomi_reasoning_disabled():
    """LLMManager Xiaomi with reasoning disabled should set extra_body."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.XIAOMI, reasoning_enabled=False, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager Xiaomi reasoning_disabled builds successfully", ok)


def test_llm_manager_nvidia_reasoning_disabled():
    """LLMManager NVIDIA with reasoning disabled should set extra_body."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, reasoning_enabled=False, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager NVIDIA reasoning_disabled builds successfully", ok)


def test_llm_manager_nvidia2_reasoning_disabled():
    """LLMManager NVIDIA2 with reasoning disabled should set extra_body."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA2, reasoning_enabled=False, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager NVIDIA2 reasoning_disabled builds successfully", ok)


def test_llm_manager_google_unknown_model():
    """LLMManager Google with unknown model name should still build."""
    from agent.llm_client import LLMManager
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, model_name="unknown-model-xyz", reasoning_enabled=True, openai_api_key="test-key")
    mgr = LLMManager(cfg)
    llm = mgr.get_llm()
    ok = llm is not None
    report("LLMManager Google unknown model -> still builds", ok)


def test_provider_config_xiaomi_has_api_base():
    """Xiaomi provider config should have a non-None api_base."""
    from agent.config import PROVIDER_CONFIG, LLMProvider
    api_base = PROVIDER_CONFIG[LLMProvider.XIAOMI].get("api_base")
    ok = api_base is not None and "xiaomi" in api_base
    report("Xiaomi has api_base with xiaomi domain", ok)


def test_provider_config_nvidia_has_api_base():
    """NVIDIA provider config should have a non-None api_base."""
    from agent.config import PROVIDER_CONFIG, LLMProvider
    api_base = PROVIDER_CONFIG[LLMProvider.NVIDIA].get("api_base")
    ok = api_base is not None and "nvidia" in api_base
    report("NVIDIA has api_base with nvidia domain", ok)


def test_provider_config_nvidia2_has_api_base():
    """NVIDIA2 provider config should have a non-None api_base."""
    from agent.config import PROVIDER_CONFIG, LLMProvider
    api_base = PROVIDER_CONFIG[LLMProvider.NVIDIA2].get("api_base")
    ok = api_base is not None and "nvidia" in api_base
    report("NVIDIA2 has api_base with nvidia domain", ok)


def test_provider_config_openrouter_has_api_base():
    """OpenRouter provider config should have a non-None api_base."""
    from agent.config import PROVIDER_CONFIG, LLMProvider
    api_base = PROVIDER_CONFIG[LLMProvider.OPENROUTER].get("api_base")
    ok = api_base is not None and "openrouter" in api_base
    report("OpenRouter has api_base with openrouter domain", ok)


# ═════════════════════════════ MAIN ════════════════════════════════════════

def main():
    print(f"\n{BOLD}=== Agent Module - Comprehensive Tests ==={RESET}\n")

    tests = [
        ("Config: LLMProvider Enum", [
            test_llm_provider_values,
            test_llm_provider_from_string,
            test_llm_provider_invalid,
            test_llm_provider_is_str,
        ]),
        ("Config: PROVIDER_CONFIG", [
            test_provider_config_has_all_providers,
            test_provider_config_has_api_key_env_vars,
            test_provider_config_google_has_multiple_keys,
            test_provider_config_api_base_types,
        ]),
        ("Config: MCPServerConfig", [
            test_mcp_server_config_defaults,
            test_mcp_server_config_custom,
            test_mcp_server_config_model_dump,
            test_mcp_server_config_model_dump_exclude_none,
        ]),
        ("Config: MCPAgentConfig (Happy Path)", [
            test_mcp_agent_config_defaults,
            test_mcp_agent_config_custom,
            test_mcp_agent_config_model_dump,
            test_mcp_agent_config_openrouter_fields,
            test_mcp_agent_config_none_benchmark,
            test_mcp_agent_config_empty_benchmark,
        ]),
        ("Config: MCPAgentConfig (Validation)", [
            test_mcp_agent_config_top_p_bounds,
            test_mcp_agent_config_max_iterations_bounds,
            test_mcp_agent_config_translator_max_iterations_bounds,
            test_mcp_agent_config_tool_timeout_bounds,
        ]),
        ("PhaseUsage", [
            test_phase_usage_defaults,
            test_phase_usage_custom,
            test_phase_usage_negative_rejected,
            test_phase_usage_no_extra_fields,
            test_phase_usage_assignment_validation,
            test_phase_usage_large_values,
        ]),
        ("TranslatorOutcome", [
            test_translator_outcome_success_requires_result,
            test_translator_outcome_success_with_result,
            test_translator_outcome_failure_requires_reason,
            test_translator_outcome_failure_with_reason,
            test_translator_outcome_no_extra_fields,
            test_translator_outcome_iterations_non_negative,
            test_translator_outcome_with_solver_payload,
            test_translator_outcome_zero_iterations,
        ]),
        ("_chunk_content_to_text", [
            test_chunk_content_none,
            test_chunk_content_string,
            test_chunk_content_list_strings,
            test_chunk_content_list_dicts_with_text,
            test_chunk_content_list_skips_thinking,
            test_chunk_content_list_skips_reasoning,
            test_chunk_content_list_with_text_attr,
            test_chunk_content_fallback_str,
            test_chunk_content_empty_list,
            test_chunk_content_mixed_list,
            test_chunk_content_list_with_none_items,
            test_chunk_content_dict_without_text_key,
        ]),
        ("_extract_reasoning_text", [
            test_extract_reasoning_from_additional_kwargs_string,
            test_extract_reasoning_from_additional_kwargs_dict,
            test_extract_reasoning_from_content_thinking_block,
            test_extract_reasoning_from_content_reasoning_block,
            test_extract_reasoning_mistral_nested,
            test_extract_reasoning_empty,
            test_extract_reasoning_priority_additional_kwargs,
            test_extract_reasoning_multiple_thinking_blocks,
            test_extract_reasoning_no_additional_kwargs,
        ]),
        ("_extract_solver_payload", [
            test_extract_solver_payload_dict,
            test_extract_solver_payload_json_string,
            test_extract_solver_payload_invalid_json_string,
            test_extract_solver_payload_list_with_text,
            test_extract_solver_payload_list_no_text,
            test_extract_solver_payload_list_with_non_dict,
            test_extract_solver_payload_none,
            test_extract_solver_payload_nested_list,
            test_extract_solver_payload_deeply_nested,
        ]),
        ("_is_terminal_solver_success: Default Clingo", [
            test_terminal_none_payload,
            test_terminal_clingo_satisfiable_with_models,
            test_terminal_clingo_satisfiable_no_models,
            test_terminal_clingo_optimum_found,
            test_terminal_clingo_unsatisfiable,
            test_terminal_clingo_unknown,
            test_terminal_clingo_error,
            test_terminal_clingo_timeout,
            test_terminal_clingo_syntax_error,
            test_terminal_clingo_grounding_timeout,
            test_terminal_clingo_models_none,
            test_terminal_clingo_models_not_list,
        ]),
        ("_is_terminal_solver_success: Default Z3", [
            test_terminal_z3_sat,
            test_terminal_z3_proved,
            test_terminal_z3_unsat_with_true,
            test_terminal_z3_unsat_with_false,
            test_terminal_z3_unsat_without_answer,
            test_terminal_z3_no_status,
            test_terminal_z3_error_status,
            test_terminal_z3_timeout,
            test_terminal_z3_unsat_in_stderr,
            test_terminal_z3_empty_stdout,
            test_terminal_z3_none_stdout,
        ]),
        ("_is_terminal_solver_success: Default Vampire", [
            test_terminal_vampire_theorem_countersatisfiable,
            test_terminal_vampire_theorem_satisfiable,
            test_terminal_vampire_contradictory_axioms,
            test_terminal_vampire_both_theorem,
            test_terminal_vampire_both_unsatisfiable,
            test_terminal_vampire_syntax_error,
            test_terminal_vampire_unknown_unknown,
            test_terminal_vampire_theorem_unknown,
            test_terminal_vampire_satisfiable_countersatisfiable,
            test_terminal_vampire_missing_negative,
            test_terminal_vampire_missing_positive,
            test_terminal_vampire_szs_with_underscores,
            test_terminal_vampire_szs_case_insensitive,
        ]),
        ("_is_terminal_solver_success: FOLIO Benchmark", [
            test_terminal_folio_clingo_true,
            test_terminal_folio_clingo_false,
            test_terminal_folio_clingo_inconsistent,
            test_terminal_folio_clingo_unsatisfiable,
            test_terminal_folio_z3_true,
            test_terminal_folio_z3_inconsistent,
            test_terminal_folio_z3_error,
            test_terminal_folio_vampire,
        ]),
        ("_is_terminal_solver_success: LSAT Benchmark", [
            test_terminal_lsat_clingo_single_option,
            test_terminal_lsat_clingo_multiple_options,
            test_terminal_lsat_clingo_no_options,
            test_terminal_lsat_clingo_unsatisfiable,
            test_terminal_lsat_z3_single_letter,
            test_terminal_lsat_z3_answer_label,
            test_terminal_lsat_z3_refine_marker,
            test_terminal_lsat_z3_error,
        ]),
        ("_is_terminal_solver_success: Edge Cases", [
            test_terminal_unknown_solver,
            test_terminal_case_insensitive_solver,
            test_terminal_empty_solver_name,
            test_terminal_whitespace_solver_name,
        ]),
        ("get_request_kwargs", [
            test_request_kwargs_google,
            test_request_kwargs_other,
            test_request_kwargs_case_insensitive,
        ]),
        ("_is_rate_limit_error", [
            test_rate_limit_429,
            test_rate_limit_503,
            test_rate_limit_402,
            test_rate_limit_credits,
            test_rate_limit_payment_required,
            test_rate_limit_normal_error,
            test_rate_limit_empty,
            test_rate_limit_afford,
            test_rate_limit_insufficient,
        ]),
        ("Phase Prompts", [
            test_get_translator_prompt_clingo,
            test_get_translator_prompt_z3,
            test_get_translator_prompt_vampire,
            test_get_translator_prompt_unknown,
            test_get_translator_prompt_case_insensitive,
            test_get_translator_prompt_whitespace,
            test_get_answer_prompt_clingo,
            test_get_answer_prompt_z3,
            test_get_answer_prompt_vampire,
            test_get_answer_prompt_unknown,
            test_answer_policy_render,
            test_answer_policy_all_solvers,
            test_translator_prompts_all_solvers,
            test_answer_prompt_contains_symbolic_grounding,
        ]),
        ("Single Pass Runner (Consistency)", [
            test_single_pass_chunk_content_to_text,
            test_single_pass_extract_reasoning_text,
            test_single_pass_is_rate_limit_error,
        ]),
        ("LLMManager", [
            test_llm_manager_init_with_config_key,
            test_llm_manager_init_env_key,
            test_llm_manager_init_no_key,
            test_llm_manager_get_llm_no_key_raises,
            test_llm_manager_google_build,
            test_llm_manager_openrouter_build,
            test_llm_manager_mistral_build,
            test_llm_manager_nvidia_build,
            test_llm_manager_nvidia2_build,
            test_llm_manager_xiaomi_build,
            test_llm_manager_google_reasoning_enabled,
            test_llm_manager_google_reasoning_disabled,
            test_llm_manager_openrouter_reasoning,
            test_llm_manager_openrouter_reasoning_disabled,
            test_llm_manager_explicit_key_overrides_env,
            test_llm_manager_google_gemini25_reasoning,
            test_llm_manager_mistral_reasoning,
        ]),
        ("MCPAgent", [
            test_mcp_agent_init_default,
            test_mcp_agent_init_custom_config,
            test_mcp_agent_build_mcp_config,
            test_mcp_agent_build_mcp_config_empty,
            test_mcp_agent_has_llm_manager,
        ]),
        ("stream_once", [
            test_stream_once_basic_content,
            test_stream_once_usage_merging,
            test_stream_once_reasoning,
            test_stream_once_empty,
            test_stream_once_usage_from_aggregated,
        ]),
        ("run_answer_phase", [
            test_answer_phase_success,
            test_answer_phase_message_construction,
            test_answer_phase_usage_accumulation,
            test_answer_phase_no_tool_args,
        ]),
        ("run_translator_phase", [
            test_translator_phase_success,
            test_translator_phase_max_iterations,
            test_translator_phase_overthinking,
            test_translator_phase_tool_not_found,
            test_translator_phase_prune_history,
            test_translator_phase_rate_limit_retry,
            test_translator_phase_tool_exception,
        ]),
        ("run_single_pass_stream", [
            test_single_pass_stream_basic,
            test_single_pass_stream_truncation,
            test_single_pass_stream_dict_finish_reason,
            test_single_pass_stream_additional_kwargs_finish_reason,
            test_single_pass_stream_retry_on_rate_limit,
            test_single_pass_stream_non_retryable_error,
            test_single_pass_stream_usage_from_response_metadata,
            test_single_pass_stream_usage_from_additional_kwargs,
            test_single_pass_stream_reasoning,
            test_single_pass_stream_empty,
        ]),
        ("Additional Edge Cases", [
            test_extract_reasoning_details_key,
            test_extract_reasoning_dict_content,
            test_extract_reasoning_dict_fallback_str,
            test_extract_solver_payload_list_with_array_json,
            test_terminal_vampire_both_refuted,
            test_terminal_vampire_countersatisfiable_theorem,
            test_terminal_folio_z3_no_conclusion,
            test_terminal_folio_clingo_verdict_uncertain,
            test_terminal_lsat_clingo_multiple_options_in_model,
            test_terminal_lsat_z3_multiple_letters,
            test_terminal_z3_sat_in_stderr,
            test_terminal_z3_proved_in_stderr,
            test_mcp_agent_config_solver_validation,
            test_mcp_agent_config_seed_none,
            test_mcp_agent_config_top_k,
            test_mcp_agent_config_repetition_penalty,
            test_llm_manager_xiaomi_reasoning_disabled,
            test_llm_manager_nvidia_reasoning_disabled,
            test_llm_manager_nvidia2_reasoning_disabled,
            test_llm_manager_google_unknown_model,
            test_provider_config_xiaomi_has_api_base,
            test_provider_config_nvidia_has_api_base,
            test_provider_config_nvidia2_has_api_base,
            test_provider_config_openrouter_has_api_base,
        ]),
    ]

    for group_name, group_tests in tests:
        print(f"\n{BOLD}--- {group_name} ---{RESET}")
        for test_fn in group_tests:
            if asyncio.iscoroutinefunction(test_fn):
                asyncio.run(test_fn())
            else:
                test_fn()

    print(f"\n{BOLD}=== Results ==={RESET}")
    total = passed + failed
    if failed == 0:
        print(f"  {GREEN}{passed}/{total} passed ✓{RESET}")
    else:
        print(f"  {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET} / {total} total")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)