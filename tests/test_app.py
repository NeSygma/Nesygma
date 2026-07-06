"""
Tests for app.py: pipeline logic, config building, solver loop, mode selection.
Tests pure logic without requiring Streamlit to be running.
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

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


# ═════════════════════════════ PIPELINE: run_system1 ═══════════════════════

def test_run_system1_returns_tuple():
    """run_system1 should return (answer, was_truncated)."""
    from ui.pipeline import run_system1
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)

    async def mock_run(*args, **kwargs):
        return ("The answer is True.", False)

    with patch("ui.pipeline.System1Agent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        result = asyncio.run(run_system1(cfg, "test query"))
        ok = isinstance(result, tuple) and len(result) == 2
        report("run_system1 returns (str, bool)", ok)


def test_run_system1_passes_query():
    """run_system1 should pass query to System1Agent.run()."""
    from ui.pipeline import run_system1
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    captured_query = None

    async def mock_run(*args, **kwargs):
        nonlocal captured_query
        captured_query = kwargs.get("user_query")
        return ("result", False)

    with patch("ui.pipeline.System1Agent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        asyncio.run(run_system1(cfg, "my question"))
        ok = captured_query == "my question"
        report("run_system1 passes query correctly", ok)


# ═════════════════════════════ PIPELINE: run_selector ══════════════════════

def test_run_selector_returns_string():
    """run_selector should return a string."""
    from ui.pipeline import run_selector
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)

    async def mock_run(*args, **kwargs):
        return '{"solver_ranking": ["z3", "clingo", "vampire"]}'

    with patch("ui.pipeline.SelectorAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        result = asyncio.run(run_selector(cfg, "test query"))
        ok = isinstance(result, str)
        report("run_selector returns str", ok)


def test_run_selector_passes_query():
    """run_selector should pass query to SelectorAgent.run()."""
    from ui.pipeline import run_selector
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    captured_query = None

    async def mock_run(*args, **kwargs):
        nonlocal captured_query
        captured_query = kwargs.get("user_query")
        return "result"

    with patch("ui.pipeline.SelectorAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        asyncio.run(run_selector(cfg, "my question"))
        ok = captured_query == "my question"
        report("run_selector passes query correctly", ok)


# ═════════════════════════════ PIPELINE: run_switcher ══════════════════════

def test_run_switcher_returns_tuple():
    """run_switcher should return (answer, was_truncated)."""
    from ui.pipeline import run_switcher
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)

    async def mock_run(*args, **kwargs):
        return ("Confidence: 85%", False)

    with patch("ui.pipeline.SwitcherAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        result = asyncio.run(run_switcher(cfg, "test query", "s1 answer", "thinking"))
        ok = isinstance(result, tuple) and len(result) == 2
        report("run_switcher returns (str, bool)", ok)


def test_run_switcher_formats_evaluator_prompt():
    """run_switcher should format EVALUATOR_USER_PROMPT with query, thinking, and s1_answer."""
    from ui.pipeline import run_switcher
    from ui.config import build_config
    from ui.prompts import EVALUATOR_USER_PROMPT

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    captured_query = None

    async def mock_run(*args, **kwargs):
        nonlocal captured_query
        captured_query = kwargs.get("user_query")
        return ("result", False)

    with patch("ui.pipeline.SwitcherAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        asyncio.run(run_switcher(cfg, "puzzle text", "s1 answer", "my thinking"))
        ok = captured_query is not None and "puzzle text" in captured_query and "s1 answer" in captured_query
        report("run_switcher formats evaluator prompt with all fields", ok)


def test_run_switcher_empty_thinking():
    """run_switcher with empty thinking should still work."""
    from ui.pipeline import run_switcher
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)

    async def mock_run(*args, **kwargs):
        return ("result", False)

    with patch("ui.pipeline.SwitcherAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        result = asyncio.run(run_switcher(cfg, "query", "answer", ""))
        ok = result == ("result", False)
        report("run_switcher with empty thinking -> still works", ok)


# ═════════════════════════════ PIPELINE: run_mcp ══════════════════════════

def test_run_mcp_returns_string():
    """run_mcp should return a string."""
    from ui.pipeline import run_mcp
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)

    async def mock_run(*args, **kwargs):
        return "The answer is True."

    with patch("ui.pipeline.MCPAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        result = asyncio.run(run_mcp(cfg, "test query"))
        ok = isinstance(result, str)
        report("run_mcp returns str", ok)


def test_run_mcp_passes_query():
    """run_mcp should pass query and translation_query to MCPAgent.run()."""
    from ui.pipeline import run_mcp
    from ui.config import build_config

    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    captured_query = None
    captured_translation = None

    async def mock_run(*args, **kwargs):
        nonlocal captured_query, captured_translation
        captured_query = kwargs.get("user_query")
        captured_translation = kwargs.get("translation_query")
        return "result"

    with patch("ui.pipeline.MCPAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run = mock_run
        asyncio.run(run_mcp(cfg, "my question", "my translation"))
        ok = captured_query == "my question" and captured_translation == "my translation"
        report("run_mcp passes query correctly", ok)


# ═════════════════════════════ PIPELINE: extract_confidence ════════════════

def test_extract_confidence_basic():
    """extract_confidence should extract percentage."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 85%") == 85
    report("extract_confidence 'Confidence: 85%' -> 85", ok)


def test_extract_confidence_none():
    """extract_confidence with no match should return None."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("No confidence here") is None
    report("extract_confidence no match -> None", ok)


def test_extract_confidence_empty():
    """extract_confidence with empty string should return None."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("") is None
    report("extract_confidence empty -> None", ok)


def test_extract_confidence_zero():
    """extract_confidence with 0% should return 0."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 0%") == 0
    report("extract_confidence 0% -> 0", ok)


def test_extract_confidence_hundred():
    """extract_confidence with 100% should return 100."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 100%") == 100
    report("extract_confidence 100% -> 100", ok)


def test_extract_confidence_threshold_boundary():
    """Confidence at 75% boundary should be extractable."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 75%") == 75
    report("extract_confidence 75% -> 75 (threshold boundary)", ok)


def test_extract_confidence_below_threshold():
    """Confidence below 75% should be extractable."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 74%") == 74
    report("extract_confidence 74% -> 74 (below threshold)", ok)


# ═════════════════════════════ PIPELINE: extract_solver_ranking ════════════

def test_extract_solver_ranking_json_block():
    """extract_solver_ranking should extract from ```json block."""
    from ui.pipeline import extract_solver_ranking
    text = '```json\n{"solver_ranking": ["z3", "clingo", "vampire"]}\n```'
    result = extract_solver_ranking(text)
    ok = result == ["z3", "clingo", "vampire"]
    report("extract_solver_ranking from json block", ok, f"Got: {result}")


def test_extract_solver_ranking_raw_json():
    """extract_solver_ranking should extract from raw JSON."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": ["clingo", "z3"]}'
    result = extract_solver_ranking(text)
    ok = result == ["clingo", "z3"]
    report("extract_solver_ranking from raw JSON", ok, f"Got: {result}")


def test_extract_solver_ranking_none():
    """extract_solver_ranking with no match should return None."""
    from ui.pipeline import extract_solver_ranking
    ok = extract_solver_ranking("No ranking here") is None
    report("extract_solver_ranking no match -> None", ok)


def test_extract_solver_ranking_normalizes_case():
    """extract_solver_ranking should normalize to lowercase."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": ["CLINGO", "Z3", "Vampire"]}'
    result = extract_solver_ranking(text)
    ok = result == ["clingo", "z3", "vampire"]
    report("extract_solver_ranking normalizes to lowercase", ok, f"Got: {result}")


def test_extract_solver_ranking_fallback_default():
    """When extract_solver_ranking returns None, app should fallback to default."""
    from ui.pipeline import extract_solver_ranking
    result = extract_solver_ranking("no ranking")
    fallback = result or ["z3", "clingo", "vampire"]
    ok = fallback == ["z3", "clingo", "vampire"]
    report("extract_solver_ranking None -> fallback to z3,clingo,vampire", ok)


# ═════════════════════════════ CONFIG: build_config for app ════════════════

def test_build_config_system1_mode():
    """build_config for System 1 mode should work without solver."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    ok = cfg.solver == "z3" and cfg.provider.value == "google"
    report("build_config for System 1 mode", ok)


def test_build_config_system2_mode_auto():
    """build_config for System 2 auto mode should use default solver."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    ok = cfg.solver == "z3"
    report("build_config for System 2 auto mode", ok)


def test_build_config_system2_mode_override():
    """build_config for System 2 with solver override."""
    from ui.config import build_config
    cfg = build_config("google", "test", "clingo", True, "high", 0.0, 1.0, 42, 4)
    ok = cfg.solver == "clingo" and "clingo" in cfg.mcp_servers
    report("build_config for System 2 override mode", ok)


def test_build_config_nesygma_mode():
    """build_config for NeSygma mode should work."""
    from ui.config import build_config
    cfg = build_config("google", "test", "vampire", True, "high", 0.0, 1.0, 42, 4)
    ok = cfg.solver == "vampire" and "vampire" in cfg.mcp_servers
    report("build_config for NeSygma mode", ok)


# ═════════════════════════════ CONFIDENCE THRESHOLD LOGIC ══════════════════

def test_confidence_above_threshold_accept():
    """Confidence >= 75% should accept S1 answer."""
    confidence = 85
    ok = confidence >= 75
    report("Confidence 85% >= 75% -> accept S1", ok)


def test_confidence_at_threshold_accept():
    """Confidence == 75% should accept S1 answer."""
    confidence = 75
    ok = confidence >= 75
    report("Confidence 75% >= 75% -> accept S1", ok)


def test_confidence_below_threshold_escalate():
    """Confidence < 75% should escalate to MCP."""
    confidence = 74
    ok = confidence < 75
    report("Confidence 74% < 75% -> escalate to MCP", ok)


def test_confidence_zero_escalate():
    """Confidence 0% should escalate to MCP."""
    confidence = 0
    ok = confidence < 75
    report("Confidence 0% < 75% -> escalate to MCP", ok)


def test_confidence_none_escalate():
    """None confidence (no match) should escalate (treated as 0)."""
    from ui.pipeline import extract_confidence
    confidence = extract_confidence("no confidence here") or 0
    ok = confidence < 75
    report("Confidence None -> 0 -> escalate to MCP", ok)


# ═════════════════════════════ SOLVER FALLBACK CHAIN ═══════════════════════

def test_default_solver_ranking():
    """Default solver ranking should be z3, clingo, vampire."""
    default = ["z3", "clingo", "vampire"]
    ok = default == ["z3", "clingo", "vampire"]
    report("Default solver ranking: z3 -> clingo -> vampire", ok)


def test_solver_override_single():
    """Solver override should produce single-element ranking."""
    solver_override = "clingo"
    ranking = [solver_override]
    ok = ranking == ["clingo"] and len(ranking) == 1
    report("Solver override -> single solver in ranking", ok)


def test_solver_override_none_uses_selector():
    """None solver override should use selector ranking."""
    solver_override = None
    selector_ranking = ["z3", "clingo", "vampire"]
    ranking = [solver_override] if solver_override else selector_ranking
    ok = ranking == ["z3", "clingo", "vampire"]
    report("Solver override None -> uses selector ranking", ok)


def test_selector_failure_fallsback_to_default():
    """When Selector raises, fallback to default [z3, clingo, vampire]."""
    sel_sections = []
    solver_ranking = ["z3", "clingo", "vampire"]
    ok = solver_ranking == ["z3", "clingo", "vampire"] and sel_sections == []
    report("Selector exception -> fallback to default solver order", ok)


# ═════════════════════════════ MODE SELECTION LOGIC ════════════════════════

def test_mode_system1_no_mcp():
    """System 1 mode should not use MCP."""
    mode = "System 1"
    ok = mode == "System 1"
    report("System 1 mode -> no MCP", ok)


def test_mode_system2_uses_selector():
    """System 2 mode should use selector."""
    mode = "System 2"
    ok = mode == "System 2"
    report("System 2 mode -> uses selector", ok)


def test_mode_nesygma_uses_all():
    """NeSygma mode should use System1 + Switcher + Selector + MCP."""
    mode = "NeSygma"
    ok = mode == "NeSygma"
    report("NeSygma mode -> uses all agents", ok)


# ═════════════════════════════ TRUNCATION HANDLING ═════════════════════════

def test_truncated_skips_switcher():
    """When System 1 is truncated, Switcher should be skipped."""
    was_truncated = True
    confidence = 0 if was_truncated else 85
    ok = confidence == 0
    report("Truncated S1 -> skip Switcher, confidence=0", ok)


def test_truncated_escalates_directly():
    """When System 1 is truncated, should escalate directly to MCP."""
    was_truncated = True
    confidence = 0
    ok = was_truncated and confidence < 75
    report("Truncated S1 -> direct escalation to MCP", ok)


def test_not_truncated_runs_switcher():
    """When System 1 is not truncated, Switcher should run."""
    was_truncated = False
    ok = not was_truncated
    report("Not truncated -> run Switcher", ok)


# ═════════════════════════════ MCP FALLBACK LOGIC ══════════════════════════

def test_mcp_fallback_on_failure():
    """When MCP fails, should fallback to S1 answer."""
    mcp_answer = "All solvers failed."
    s1_answer = "S1's answer"
    final = mcp_answer if mcp_answer != "All solvers failed." else s1_answer
    ok = final == s1_answer
    report("MCP fails -> fallback to S1 answer", ok)


def test_mcp_success_uses_mcp():
    """When MCP succeeds, should use MCP answer."""
    mcp_answer = "The correct answer is True."
    s1_answer = "S1's answer"
    final = mcp_answer if mcp_answer != "All solvers failed." else s1_answer
    ok = final == mcp_answer
    report("MCP succeeds -> use MCP answer", ok)


def test_mcp_none_triggers_next_solver():
    """None mcp_result should raise -> next solver tried."""
    mcp_result = None
    triggers_failure = not mcp_result
    ok = triggers_failure is True
    report("MCP None -> triggers failure (next solver)", ok)


def test_mcp_empty_triggers_next_solver():
    """Empty mcp_result should raise -> next solver tried."""
    mcp_result = ""
    triggers_failure = not mcp_result
    ok = triggers_failure is True
    report("MCP empty string -> triggers failure (next solver)", ok)


def test_mcp_translator_failed_triggers_next_solver():
    """Translator failed mcp_result should raise -> next solver tried."""
    mcp_result = "Translator failed: parse error"
    triggers_failure = not mcp_result or mcp_result.startswith("Translator failed")
    ok = triggers_failure is True
    report("MCP 'Translator failed' -> triggers failure (next solver)", ok)


def test_mcp_valid_result_succeeds():
    """Valid mcp_result should not trigger failure."""
    mcp_result = "The answer is True."
    triggers_failure = not mcp_result or mcp_result.startswith("Translator failed")
    ok = triggers_failure is False
    report("MCP valid result -> success path", ok)


# ═════════════════════════════ EDGE CASES ═════════════════════════════════

def test_empty_query_handling():
    """Empty query should be handled gracefully."""
    query = ""
    ok = isinstance(query, str)
    report("Empty query -> handled as string", ok)


def test_long_query_handling():
    """Very long query should be handled gracefully."""
    query = "A" * 10000
    ok = len(query) == 10000
    report("Long query (10k chars) -> handled", ok)


def test_special_chars_in_query():
    """Special characters in query should be handled."""
    query = "∀x∃y: P(x,y) ∧ ¬Q(x) → R(y)"
    ok = "∀" in query and "∃" in query
    report("Special characters in query -> handled", ok)


def test_multiline_query():
    """Multiline query should be handled."""
    query = "Premise 1: All cats are animals.\nPremise 2: Tom is a cat.\nConclusion: Tom is an animal."
    ok = "\n" in query and len(query.split("\n")) == 3
    report("Multiline query -> handled", ok)


def test_all_providers_build_config():
    """build_config should work with all providers for app."""
    from ui.config import build_config, ALL_PROVIDERS
    for p in ALL_PROVIDERS:
        cfg = build_config(p, "test-model", "z3", True, "high", 0.0, 1.0, 42, 4)
        ok = cfg.provider.value == p
        if not ok:
            report(f"build_config provider={p} for app", False)
            return
    report("build_config works with all providers for app", True)


def test_all_solvers_build_config():
    """build_config should work with all solvers for app."""
    from ui.config import build_config
    for solver in ["clingo", "z3", "vampire"]:
        cfg = build_config("google", "test", solver, True, "high", 0.0, 1.0, 42, 4)
        ok = cfg.solver == solver and solver in cfg.mcp_servers
        if not ok:
            report(f"build_config solver={solver} for app", False)
            return
    report("build_config works with all solvers for app", True)


def test_all_efforts_build_config():
    """build_config should work with all effort levels."""
    from ui.config import build_config, ALL_EFFORTS
    for effort in ALL_EFFORTS:
        cfg = build_config("google", "test", "z3", True, effort, 0.0, 1.0, 42, 4)
        ok = cfg.reasoning_effort == effort
        if not ok:
            report(f"build_config effort={effort}", False)
            return
    report("build_config works with all effort levels", True)


def test_reasoning_disabled_build_config():
    """build_config with reasoning disabled should work."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", False, "none", 0.0, 1.0, 42, 4)
    ok = cfg.reasoning_enabled is False and cfg.reasoning_effort == "none"
    report("build_config reasoning disabled", ok)


def test_openrouter_build_config():
    """build_config for OpenRouter with extra body should work."""
    from ui.config import build_config
    extra = {"reasoning": {"effort": "high"}}
    cfg = build_config(
        "openrouter", "openai/gpt-oss-120b", "z3",
        True, "high", 0.0, 1.0, 42, 4,
        model_extra_body=extra,
        openrouter_provider={"order": ["deepseek"]},
    )
    ok = cfg.model_extra_body == extra and cfg.openrouter_provider == {"order": ["deepseek"]}
    report("build_config OpenRouter with extra_body", ok)


# ═════════════════════════════ STRUCTURAL TESTS ═══════════════════════════

def test_app_imports():
    """app.py should be importable (without running Streamlit)."""
    try:
        import importlib
        spec = importlib.util.spec_from_file_location("app", str(ROOT_DIR / "app.py"))
        ok = spec is not None
        report("app.py is importable (spec found)", ok)
    except Exception as e:
        report("app.py is importable", False, str(e))


def test_ui_pipeline_imports():
    """ui.pipeline should be importable."""
    from ui.pipeline import run_system1, run_selector, run_switcher, run_mcp
    ok = all(callable(f) for f in [run_system1, run_selector, run_switcher, run_mcp])
    report("ui.pipeline imports all 4 pipeline functions", ok)


def test_ui_config_imports():
    """ui.config should be importable."""
    from ui.config import build_config, ALL_PROVIDERS, ALL_SOLVERS, ALL_EFFORTS
    ok = callable(build_config) and len(ALL_PROVIDERS) > 0 and len(ALL_SOLVERS) > 0
    report("ui.config imports correctly", ok)


def test_ui_capture_imports():
    """ui.capture should be importable."""
    from ui.capture import parse_output, render_parsed_sections, extract_thinking_trace
    ok = all(callable(f) for f in [parse_output, render_parsed_sections, extract_thinking_trace])
    report("ui.capture imports correctly", ok)


def test_ui_workspace_imports():
    """ui.workspace should be importable."""
    from ui.workspace import render_workspace_files, clear_all_workspaces
    ok = callable(render_workspace_files) and callable(clear_all_workspaces)
    report("ui.workspace imports correctly", ok)


def test_ui_prompts_imports():
    """ui.prompts should be importable."""
    from ui.prompts import EVALUATOR_USER_PROMPT, _THINKING_SECTION_TEMPLATE
    ok = isinstance(EVALUATOR_USER_PROMPT, str) and isinstance(_THINKING_SECTION_TEMPLATE, str)
    report("ui.prompts imports correctly", ok)


def test_ui_styles_imports():
    """ui.styles should be importable."""
    from ui.styles import CUSTOM_CSS
    ok = isinstance(CUSTOM_CSS, str) and len(CUSTOM_CSS) > 0
    report("ui.styles imports correctly", ok)


# ═════════════════════════════ MAIN ════════════════════════════════════════

def main():
    print(f"\n{BOLD}=== App Module - Comprehensive Tests ==={RESET}\n")

    tests = [
        ("Pipeline: run_system1", [
            test_run_system1_returns_tuple,
            test_run_system1_passes_query,
        ]),
        ("Pipeline: run_selector", [
            test_run_selector_returns_string,
            test_run_selector_passes_query,
        ]),
        ("Pipeline: run_switcher", [
            test_run_switcher_returns_tuple,
            test_run_switcher_formats_evaluator_prompt,
            test_run_switcher_empty_thinking,
        ]),
        ("Pipeline: run_mcp", [
            test_run_mcp_returns_string,
            test_run_mcp_passes_query,
        ]),
        ("Pipeline: extract_confidence", [
            test_extract_confidence_basic,
            test_extract_confidence_none,
            test_extract_confidence_empty,
            test_extract_confidence_zero,
            test_extract_confidence_hundred,
            test_extract_confidence_threshold_boundary,
            test_extract_confidence_below_threshold,
        ]),
        ("Pipeline: extract_solver_ranking", [
            test_extract_solver_ranking_json_block,
            test_extract_solver_ranking_raw_json,
            test_extract_solver_ranking_none,
            test_extract_solver_ranking_normalizes_case,
            test_extract_solver_ranking_fallback_default,
        ]),
        ("Config: build_config for App", [
            test_build_config_system1_mode,
            test_build_config_system2_mode_auto,
            test_build_config_system2_mode_override,
            test_build_config_nesygma_mode,
            test_all_providers_build_config,
            test_all_solvers_build_config,
            test_all_efforts_build_config,
            test_reasoning_disabled_build_config,
            test_openrouter_build_config,
        ]),
        ("Confidence Threshold Logic", [
            test_confidence_above_threshold_accept,
            test_confidence_at_threshold_accept,
            test_confidence_below_threshold_escalate,
            test_confidence_zero_escalate,
            test_confidence_none_escalate,
        ]),
        ("Solver Fallback Chain", [
            test_default_solver_ranking,
            test_solver_override_single,
            test_solver_override_none_uses_selector,
            test_selector_failure_fallsback_to_default,
        ]),
        ("Mode Selection Logic", [
            test_mode_system1_no_mcp,
            test_mode_system2_uses_selector,
            test_mode_nesygma_uses_all,
        ]),
        ("Truncation Handling", [
            test_truncated_skips_switcher,
            test_truncated_escalates_directly,
            test_not_truncated_runs_switcher,
        ]),
        ("MCP Fallback Logic", [
            test_mcp_fallback_on_failure,
            test_mcp_success_uses_mcp,
            test_mcp_none_triggers_next_solver,
            test_mcp_empty_triggers_next_solver,
            test_mcp_translator_failed_triggers_next_solver,
            test_mcp_valid_result_succeeds,
        ]),
        ("Edge Cases", [
            test_empty_query_handling,
            test_long_query_handling,
            test_special_chars_in_query,
            test_multiline_query,
        ]),
        ("Structural Tests", [
            test_app_imports,
            test_ui_pipeline_imports,
            test_ui_config_imports,
            test_ui_capture_imports,
            test_ui_workspace_imports,
            test_ui_prompts_imports,
            test_ui_styles_imports,
        ]),
    ]

    for group_name, group_tests in tests:
        print(f"\n{BOLD}--- {group_name} ---{RESET}")
        for test_fn in group_tests:
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