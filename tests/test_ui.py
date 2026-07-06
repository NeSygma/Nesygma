"""
Tests for the UI module: config, capture, pipeline, workspace, prompts.
Tests pure logic without requiring Streamlit to be running.
"""
import json
import os
import sys
from pathlib import Path

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


# ═════════════════════════════ CONFIG TESTS ═══════════════════════════

def test_provider_models_keys():
    """ALL_PROVIDERS should match PROVIDER_MODELS keys."""
    from ui.config import ALL_PROVIDERS, PROVIDER_MODELS
    ok = ALL_PROVIDERS == list(PROVIDER_MODELS.keys())
    report("ALL_PROVIDERS matches PROVIDER_MODELS keys", ok, f"Got: {ALL_PROVIDERS}")


def test_all_providers_valid_enum():
    """Every provider string should map to a valid LLMProvider enum."""
    from ui.config import ALL_PROVIDERS
    from agent.config import LLMProvider
    for p in ALL_PROVIDERS:
        try:
            LLMProvider(p)
        except ValueError:
            report(f"Provider '{p}' maps to LLMProvider enum", False, f"Invalid provider: {p}")
            return
    report("All providers map to valid LLMProvider enum", True)


def test_build_config_google():
    """build_config with google provider should produce valid MCPAgentConfig."""
    from ui.config import build_config
    from agent.config import LLMProvider
    cfg = build_config(
        "google", "gemini-3.1-flash-lite", "z3",
        True, "high", 0.0, 1.0, 42, 4,
    )
    ok = (
        cfg.provider == LLMProvider.GOOGLE
        and cfg.model_name == "gemini-3.1-flash-lite"
        and cfg.solver == "z3"
        and cfg.reasoning_enabled is True
        and cfg.reasoning_effort == "high"
        and cfg.max_iterations == 4
    )
    report("build_config google -> valid config", ok, str(cfg.model_dump()) if not ok else "")


def test_build_config_openrouter_with_extra_body():
    """build_config with model_extra_body should set it on config."""
    from ui.config import build_config
    extra = {"reasoning": {"effort": "high"}}
    cfg = build_config(
        "openrouter", "openai/gpt-oss-120b", "z3",
        True, "high", 0.0, 1.0, 42, 4,
        model_extra_body=extra,
        openrouter_provider={"order": ["deepseek"]},
    )
    ok = (
        cfg.model_extra_body == extra
        and cfg.openrouter_provider == {"order": ["deepseek"]}
    )
    report("build_config openrouter with extra_body + provider", ok)


def test_build_config_mcp_servers():
    """build_config should create MCP server config for the specified solver."""
    from ui.config import build_config
    cfg = build_config("google", "test", "clingo", True, "high", 0.0, 1.0, 42, 4)
    ok = "clingo" in cfg.mcp_servers and cfg.mcp_servers["clingo"].command == "python"
    report("build_config creates MCP server for solver", ok)


def test_build_config_no_extra_body():
    """build_config without model_extra_body should leave it as None."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
    ok = cfg.model_extra_body is None and cfg.openrouter_provider is None
    report("build_config without extra_body -> None", ok)


def test_openrouter_models_unique_labels():
    """OPENROUTER_MODEL_LABELS should have no duplicates."""
    from ui.config import OPENROUTER_MODEL_LABELS
    ok = len(OPENROUTER_MODEL_LABELS) == len(set(OPENROUTER_MODEL_LABELS))
    report("OpenRouter model labels are unique", ok, f"Got: {OPENROUTER_MODEL_LABELS}")


def test_openrouter_models_have_required_keys():
    """Each OpenRouter model entry should have required keys."""
    from ui.config import OPENROUTER_MODELS
    required = {"label", "model", "openrouter_provider", "default_reasoning"}
    for entry in OPENROUTER_MODELS:
        missing = required - set(entry.keys())
        if missing:
            report(f"OpenRouter model '{entry.get('label')}' has required keys", False, f"Missing: {missing}")
            return
    report("All OpenRouter models have required keys", True)


def test_all_efforts_contains_xhigh():
    """ALL_EFFORTS should include xhigh."""
    from ui.config import ALL_EFFORTS
    ok = ALL_EFFORTS == ["none", "minimal", "low", "medium", "high", "xhigh"]
    report("ALL_EFFORTS has all 6 levels", ok, f"Got: {ALL_EFFORTS}")


# ═════════════════════════════ CAPTURE TESTS ═════════════════════════

def test_parse_output_empty():
    """Empty input should return empty sections."""
    from ui.capture import parse_output
    sections = parse_output("")
    ok = len(sections) == 0
    report("parse_output empty -> no sections", ok)


def test_parse_output_thinking_tags():
    """<THINKING>...</THINKING> should produce a thinking section."""
    from ui.capture import parse_output
    raw = "Hello\n<THINKING>\nreasoning here\n</THINKING>\nWorld"
    sections = parse_output(raw)
    types = [s.type for s in sections]
    ok = "thinking" in types and "text" in types
    thinking = [s for s in sections if s.type == "thinking"]
    ok = ok and len(thinking) == 1 and "reasoning here" in thinking[0].content
    report("parse_output <THINKING> tags -> thinking section", ok)


def test_parse_output_think_tags():
    """<think>...</think> should also produce a thinking section."""
    from ui.capture import parse_output
    raw = "<think>\nreasoning\n</think>\nanswer"
    sections = parse_output(raw)
    thinking = [s for s in sections if s.type == "thinking"]
    ok = len(thinking) == 1 and "reasoning" in thinking[0].content
    report("parse_output <think> tags -> thinking section", ok)


def test_parse_output_tool_call():
    """[MCP TOOL] line should produce a tool_call section."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] write_file\nArgs: {\"filename\": \"test.lp\", \"code\": \"a.\"}\n"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "write_file" in tool_calls[0].label
    report("parse_output [MCP TOOL] -> tool_call section", ok)


def test_parse_output_tool_result():
    """[RESULT] should produce a tool_result section."""
    from ui.capture import parse_output
    raw = "[RESULT]\nsome result text\n--- Iteration 2 ---"
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    ok = len(results) == 1 and "some result text" in results[0].content
    report("parse_output [RESULT] -> tool_result section", ok)


def test_parse_output_token_usage():
    """TOKEN USAGE SUMMARY should produce a token_usage section."""
    from ui.capture import parse_output
    raw = "TOKEN USAGE SUMMARY\n  Total input tokens:  100\n  Total output tokens: 200\n  Total tokens:        300"
    sections = parse_output(raw)
    tokens = [s for s in sections if s.type == "token_usage"]
    ok = len(tokens) == 1 and "100" in tokens[0].content
    report("parse_output TOKEN USAGE SUMMARY -> token_usage section", ok)


def test_parse_output_token_usage_bracket():
    """[TOKEN USAGE] should also produce a token_usage section."""
    from ui.capture import parse_output
    raw = "[TOKEN USAGE]\n  Input tokens:  100\n  Output tokens: 200"
    sections = parse_output(raw)
    tokens = [s for s in sections if s.type == "token_usage"]
    ok = len(tokens) == 1
    report("parse_output [TOKEN USAGE] -> token_usage section", ok)


def test_parse_output_iteration_header():
    """--- Iteration N --- should produce a header section."""
    from ui.capture import parse_output
    raw = "--- Iteration 3 ---\nsome content"
    sections = parse_output(raw)
    headers = [s for s in sections if s.type == "header"]
    ok = any("Iteration 3" in h.content for h in headers)
    report("parse_output --- Iteration N --- -> header", ok)


def test_parse_output_complete_header():
    """COMPLETE should produce a header section."""
    from ui.capture import parse_output
    raw = "COMPLETE"
    sections = parse_output(raw)
    headers = [s for s in sections if s.type == "header"]
    ok = len(headers) == 1 and "COMPLETE" in headers[0].content
    report("parse_output COMPLETE -> header", ok)


def test_parse_output_result_then_token_usage():
    """[RESULT] content followed by TOKEN USAGE should not merge them."""
    from ui.capture import parse_output
    raw = "[RESULT]\nresult content\nTOKEN USAGE SUMMARY\n  Total input tokens:  100\n  Total output tokens: 200\n  Total tokens:        300\nCOMPLETE"
    sections = parse_output(raw)
    types = [s.type for s in sections]
    ok = "tool_result" in types and "token_usage" in types and "header" in types
    results = [s for s in sections if s.type == "tool_result"]
    ok = ok and all("Total input tokens" not in s.content for s in results)
    report("parse_output [RESULT] then TOKEN USAGE -> separate sections", ok, f"Types: {types}")


def test_parse_output_no_separator_in_token_usage():
    """Token usage section should not contain === separator lines."""
    from ui.capture import parse_output
    raw = "TOKEN USAGE SUMMARY\n  Total input tokens:  100\n  Total output tokens: 200\n  Total tokens:        300\n============================================================"
    sections = parse_output(raw)
    tokens = [s for s in sections if s.type == "token_usage"]
    ok = len(tokens) == 1 and "====" not in tokens[0].content
    report("parse_output token_usage has no separator lines", ok, f"Content: {tokens[0].content if tokens else 'N/A'}")


def test_parse_output_mcp_agent_header():
    """MCP CLINGO AGENT line should produce a header."""
    from ui.capture import parse_output
    raw = "MCP CLINGO AGENT - Symbolic Reasoning"
    sections = parse_output(raw)
    headers = [s for s in sections if s.type == "header"]
    ok = len(headers) >= 1
    report("parse_output MCP AGENT line -> header", ok)


def test_parse_output_query_text():
    """Query: line should produce a text section."""
    from ui.capture import parse_output
    raw = "Query: What is 2+2?"
    sections = parse_output(raw)
    texts = [s for s in sections if s.type == "text"]
    ok = any("Query:" in t.content for t in texts)
    report("parse_output Query: -> text section", ok)


def test_extract_thinking_trace():
    """extract_thinking_trace should extract content between thinking tags."""
    from ui.capture import extract_thinking_trace
    raw = "Hello\n<THINKING>\nline 1\nline 2\n</THINKING>\nWorld"
    trace = extract_thinking_trace(raw)
    ok = "line 1" in trace and "line 2" in trace and "Hello" not in trace and "World" not in trace
    report("extract_thinking_trace extracts thinking content", ok)


def test_extract_thinking_trace_think_tags():
    """extract_thinking_trace should also work with <think> tags."""
    from ui.capture import extract_thinking_trace
    raw = "<think>\nreasoning text\n</think>"
    trace = extract_thinking_trace(raw)
    ok = "reasoning text" in trace
    report("extract_thinking_trace with <think> tags", ok)


def test_extract_thinking_trace_empty():
    """extract_thinking_trace with no thinking tags should return empty."""
    from ui.capture import extract_thinking_trace
    trace = extract_thinking_trace("Hello World")
    ok = trace == ""
    report("extract_thinking_trace no tags -> empty", ok)


def test_parse_output_tool_call_with_json_args():
    """Tool call with JSON args containing code should render as python code block."""
    from ui.capture import parse_output
    raw = '[MCP TOOL] write_file\nArgs: {"filename": "test.lp", "code": "a. b."}\n'
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "test.lp" in tool_calls[0].content and "a. b." in tool_calls[0].content
    report("parse_output tool call with JSON code args -> python block", ok)


def test_parse_output_tool_call_with_plain_args():
    """Tool call with non-JSON args should render as plain code block."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] run_solver\nArgs: some plain text args\n"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "some plain text args" in tool_calls[0].content
    report("parse_output tool call with plain args -> code block", ok)


# ═════════════════════════════ PIPELINE TESTS ════════════════════════

def test_extract_confidence_basic():
    """extract_confidence should extract percentage from text."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 85%") == 85
    report("extract_confidence 'Confidence: 85%' -> 85", ok)


def test_extract_confidence_case_insensitive():
    """extract_confidence should be case insensitive."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("confidence: 42%") == 42
    report("extract_confidence lowercase -> 42", ok)


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


def test_extract_solver_ranking_json_block():
    """extract_solver_ranking should extract from ```json block."""
    from ui.pipeline import extract_solver_ranking
    text = 'Here is my analysis:\n```json\n{"solver_ranking": ["z3", "clingo", "vampire"]}\n```'
    result = extract_solver_ranking(text)
    ok = result == ["z3", "clingo", "vampire"]
    report("extract_solver_ranking from json block", ok, f"Got: {result}")


def test_extract_solver_ranking_raw_json():
    """extract_solver_ranking should extract from raw JSON in text."""
    from ui.pipeline import extract_solver_ranking
    text = 'Based on analysis {"solver_ranking": ["clingo", "z3"]}'
    result = extract_solver_ranking(text)
    ok = result == ["clingo", "z3"]
    report("extract_solver_ranking from raw JSON", ok, f"Got: {result}")


def test_extract_solver_ranking_none():
    """extract_solver_ranking with no match should return None."""
    from ui.pipeline import extract_solver_ranking
    ok = extract_solver_ranking("No ranking here") is None
    report("extract_solver_ranking no match -> None", ok)


def test_extract_solver_ranking_empty():
    """extract_solver_ranking with empty string should return None."""
    from ui.pipeline import extract_solver_ranking
    ok = extract_solver_ranking("") is None
    report("extract_solver_ranking empty -> None", ok)


def test_extract_solver_ranking_normalizes_case():
    """extract_solver_ranking should normalize solver names to lowercase."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": ["CLINGO", "Z3", "Vampire"]}'
    result = extract_solver_ranking(text)
    ok = result == ["clingo", "z3", "vampire"]
    report("extract_solver_ranking normalizes to lowercase", ok, f"Got: {result}")


def test_extract_solver_ranking_strips_whitespace():
    """extract_solver_ranking should strip whitespace from solver names."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": [" clingo ", "  z3"]}'
    result = extract_solver_ranking(text)
    ok = result == ["clingo", "z3"]
    report("extract_solver_ranking strips whitespace", ok, f"Got: {result}")


# ═════════════════════════════ WORKSPACE TESTS ═══════════════════════

def test_workspace_map_keys():
    """WORKSPACE_MAP should have entries for all 3 solvers."""
    from ui.workspace import WORKSPACE_MAP
    ok = set(WORKSPACE_MAP.keys()) == {"clingo", "z3", "vampire"}
    report("WORKSPACE_MAP has all 3 solvers", ok)


def test_solver_extensions_complete():
    """SOLVER_EXTENSIONS should have entries for all 3 solvers."""
    from ui.workspace import SOLVER_EXTENSIONS
    ok = set(SOLVER_EXTENSIONS.keys()) == {"clingo", "z3", "vampire"}
    report("SOLVER_EXTENSIONS has all 3 solvers", ok)


def test_get_workspace_files_nonexistent():
    """get_workspace_files for nonexistent dir should return empty list."""
    from ui.workspace import get_workspace_files
    result = get_workspace_files("clingo")
    ok = isinstance(result, list)
    report("get_workspace_files returns list", ok)


def test_get_workspace_files_unknown_solver():
    """get_workspace_files for unknown solver should return empty list."""
    from ui.workspace import get_workspace_files
    result = get_workspace_files("unknown_solver")
    ok = result == []
    report("get_workspace_files unknown solver -> empty", ok)


# ═════════════════════════════ PROMPTS TESTS ═════════════════════════

def test_evaluator_prompt_format():
    """EVALUATOR_USER_PROMPT should be formattable with required keys."""
    from ui.prompts import EVALUATOR_USER_PROMPT
    result = EVALUATOR_USER_PROMPT.format(
        puzzle_text="test puzzle",
        thinking_section="test thinking",
        system1_answer="test answer",
    )
    ok = "test puzzle" in result and "test thinking" in result and "test answer" in result
    report("EVALUATOR_USER_PROMPT formats correctly", ok)


def test_thinking_section_template_format():
    """_THINKING_SECTION_TEMPLATE should be formattable with thinking key."""
    from ui.prompts import _THINKING_SECTION_TEMPLATE
    result = _THINKING_SECTION_TEMPLATE.format(thinking="my reasoning")
    ok = "my reasoning" in result and "SYSTEM 1 INTERNAL REASONING" in result
    report("_THINKING_SECTION_TEMPLATE formats correctly", ok)


def test_evaluator_prompt_anti_anchoring():
    """EVALUATOR_USER_PROMPT should contain anti-anchoring reminder."""
    from ui.prompts import EVALUATOR_USER_PROMPT
    ok = "ANTI-ANCHORING" in EVALUATOR_USER_PROMPT and "Confidence:" in EVALUATOR_USER_PROMPT
    report("EVALUATOR_USER_PROMPT has anti-anchoring + confidence format", ok)


# ═════════════════════════════ EDGE CASES ════════════════════════════

def test_parse_output_multiple_thinking_blocks():
    """Multiple thinking blocks should each produce separate sections."""
    from ui.capture import parse_output
    raw = "<THINKING>\nfirst\n</THINKING>\nanswer\n<THINKING>\nsecond\n</THINKING>"
    sections = parse_output(raw)
    thinking = [s for s in sections if s.type == "thinking"]
    ok = len(thinking) == 2
    report("parse_output multiple thinking blocks -> 2 sections", ok, f"Got {len(thinking)}")


def test_parse_output_nested_json_in_tool_result():
    """Tool result with valid JSON should be preserved."""
    from ui.capture import parse_output
    raw = '[RESULT]\n{"status": "satisfiable", "models": [["a", "b"]]}\n--- Iteration 2 ---'
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    ok = len(results) == 1
    try:
        json.loads(results[0].content)
        ok = ok and True
    except json.JSONDecodeError:
        ok = False
    report("parse_output tool result with JSON -> preserved", ok)


def test_parse_output_plain_text_between_sections():
    """Plain text between structured sections should be captured as text."""
    from ui.capture import parse_output
    raw = "Some intro text\n<THINKING>\nreasoning\n</THINKING>\nSome outro text"
    sections = parse_output(raw)
    texts = [s for s in sections if s.type == "text"]
    contents = " ".join(t.content for t in texts)
    ok = "intro text" in contents and "outro text" in contents
    report("parse_output plain text between sections -> text type", ok)


def test_parse_output_only_whitespace():
    """Only whitespace should produce no sections."""
    from ui.capture import parse_output
    sections = parse_output("   \n\n   \n")
    ok = len(sections) == 0
    report("parse_output only whitespace -> no sections", ok)


def test_build_config_all_solvers():
    """build_config should work with all 3 solvers."""
    from ui.config import build_config
    for solver in ["clingo", "z3", "vampire"]:
        cfg = build_config("google", "test", solver, True, "high", 0.0, 1.0, 42, 4)
        ok = cfg.solver == solver and solver in cfg.mcp_servers
        report(f"build_config solver={solver}", ok)


def test_build_config_max_output_tokens():
    """build_config should respect max_output_tokens parameter."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4, max_output_tokens=8192)
    ok = cfg.max_output_tokens == 8192
    report("build_config max_output_tokens=8192", ok)


def test_build_config_temperature():
    """build_config should pass temperature correctly."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 1.5, 1.0, 42, 4)
    ok = cfg.temperature == 1.5
    report("build_config temperature=1.5", ok)


# ═════════════════════════════ HAPPY PATH TESTS ══════════════════════

def test_build_config_all_providers():
    """build_config should work with every provider."""
    from ui.config import build_config, ALL_PROVIDERS
    for p in ALL_PROVIDERS:
        cfg = build_config(p, "test-model", "z3", True, "high", 0.0, 1.0, 42, 4)
        ok = cfg.provider.value == p
        report(f"build_config provider={p}", ok)


def test_build_config_reasoning_disabled():
    """build_config with reasoning disabled should set reasoning_enabled=False."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", False, "none", 0.0, 1.0, 42, 4)
    ok = cfg.reasoning_enabled is False and cfg.reasoning_effort == "none"
    report("build_config reasoning disabled", ok)


def test_build_config_seed():
    """build_config should pass seed correctly."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 99, 4)
    ok = cfg.seed == 99
    report("build_config seed=99", ok)


def test_build_config_top_p():
    """build_config should pass top_p correctly."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 0.95, 42, 4)
    ok = cfg.top_p == 0.95
    report("build_config top_p=0.95", ok)


def test_build_config_max_iterations():
    """build_config should pass max_iterations correctly."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 7)
    ok = cfg.max_iterations == 7
    report("build_config max_iterations=7", ok)


def test_build_config_with_benchmark():
    """build_config with benchmark should set it on config."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4, benchmark="FOLIO")
    ok = cfg.benchmark == "FOLIO"
    report("build_config benchmark=FOLIO", ok)


def test_build_config_mcp_server_args():
    """MCP server args should include -m <solver>_mcp_server."""
    from ui.config import build_config
    cfg = build_config("google", "test", "vampire", True, "high", 0.0, 1.0, 42, 4)
    server = cfg.mcp_servers["vampire"]
    ok = server.args == ["-m", "vampire_mcp_server"] and server.transport == "stdio"
    report("build_config MCP server args correct", ok)


def test_parse_output_unclosed_thinking():
    """Unclosed <THINKING> tag should capture everything after as thinking."""
    from ui.capture import parse_output
    raw = "before\n<THINKING>\nline 1\nline 2"
    sections = parse_output(raw)
    thinking = [s for s in sections if s.type == "thinking"]
    ok = len(thinking) == 1 and "line 1" in thinking[0].content and "line 2" in thinking[0].content
    report("parse_output unclosed <THINKING> -> captures rest", ok)


def test_parse_output_consecutive_tool_calls():
    """Multiple consecutive tool calls should each produce separate sections."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] tool_a\nArgs: {}\n[RESULT]\nresult_a\n[MCP TOOL] tool_b\nArgs: {}\n[RESULT]\nresult_b"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    results = [s for s in sections if s.type == "tool_result"]
    ok = len(tool_calls) == 2 and len(results) == 2
    report("parse_output consecutive tool calls -> 2 calls + 2 results", ok, f"Got {len(tool_calls)} calls, {len(results)} results")


def test_parse_output_tool_call_no_args():
    """Tool call with no Args line should still produce a section."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] list_files\n[RESULT]\nfile list"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "list_files" in tool_calls[0].label
    report("parse_output tool call no Args -> still works", ok)


def test_parse_output_mixed_thinking_and_tools():
    """Full MCP output with thinking, tools, results, and token usage."""
    from ui.capture import parse_output
    raw = """MCP CLINGO AGENT - Symbolic Reasoning

Query: test query

<THINKING>
I need to translate this to ASP.
</THINKING>

--- Iteration 1 ---
[MCP TOOL] write_file
Args: {"filename": "test.lp", "code": "a."}
[RESULT]
{"status": "success"}
[MCP TOOL] run_solver
Args: {"filename": "test.lp"}
[RESULT]
{"status": "satisfiable", "models": [["a"]]}

TOKEN USAGE SUMMARY
  Total input tokens:  100
  Total output tokens: 200
  Total tokens:        300

COMPLETE"""
    sections = parse_output(raw)
    types = [s.type for s in sections]
    ok = (
        "header" in types
        and "thinking" in types
        and "tool_call" in types
        and "tool_result" in types
        and "token_usage" in types
    )
    report("parse_output full MCP output -> all section types", ok, f"Types: {types}")


def test_parse_output_special_characters():
    """Special characters in content should be preserved."""
    from ui.capture import parse_output
    raw = "<THINKING>\n∀x∃y: P(x,y) ∧ ¬Q(x)\n</THINKING>"
    sections = parse_output(raw)
    thinking = [s for s in sections if s.type == "thinking"]
    ok = len(thinking) == 1 and "∀x∃y" in thinking[0].content and "¬Q" in thinking[0].content
    report("parse_output preserves special characters", ok)


def test_extract_thinking_trace_multiple():
    """extract_thinking_trace with multiple blocks should concatenate them."""
    from ui.capture import extract_thinking_trace
    raw = "<THINKING>\nfirst\n</THINKING>\nmid\n<THINKING>\nsecond\n</THINKING>"
    trace = extract_thinking_trace(raw)
    ok = "first" in trace and "second" in trace and "mid" not in trace
    report("extract_thinking_trace multiple blocks -> concatenated", ok)


def test_extract_confidence_in_long_text():
    """extract_confidence should find confidence in a long response."""
    from ui.pipeline import extract_confidence
    text = "After careful analysis of all the premises and applying logical deduction, " * 10 + "Confidence: 73%"
    ok = extract_confidence(text) == 73
    report("extract_confidence in long text -> 73", ok)


def test_extract_confidence_multiple_matches():
    """extract_confidence uses re.search which returns the first match."""
    from ui.pipeline import extract_confidence
    text = "Initial: Confidence: 50%\nAfter review: Confidence: 90%"
    ok = extract_confidence(text) == 50
    report("extract_confidence multiple matches -> first (50)", ok)


def test_extract_solver_ranking_with_surrounding_text():
    """extract_solver_ranking should work with lots of surrounding text."""
    from ui.pipeline import extract_solver_ranking
    text = "Based on my analysis of the problem structure, I recommend:\n" * 5 + '{"solver_ranking": ["vampire", "z3"]}'
    result = extract_solver_ranking(text)
    ok = result == ["vampire", "z3"]
    report("extract_solver_ranking with surrounding text", ok, f"Got: {result}")


def test_extract_solver_ranking_single_solver():
    """extract_solver_ranking with single solver should return list of one."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": ["clingo"]}'
    result = extract_solver_ranking(text)
    ok = result == ["clingo"]
    report("extract_solver_ranking single solver -> list of one", ok, f"Got: {result}")


def test_extract_solver_ranking_json_block_with_extra():
    """extract_solver_ranking from json block with extra fields should still work."""
    from ui.pipeline import extract_solver_ranking
    text = '```json\n{"solver_ranking": ["z3", "clingo"], "reason": "constraint-based"}\n```'
    result = extract_solver_ranking(text)
    ok = result == ["z3", "clingo"]
    report("extract_solver_ranking json block with extra fields", ok, f"Got: {result}")


def test_evaluator_prompt_empty_thinking():
    """EVALUATOR_USER_PROMPT with empty thinking_section should still format."""
    from ui.prompts import EVALUATOR_USER_PROMPT
    result = EVALUATOR_USER_PROMPT.format(
        puzzle_text="test",
        thinking_section="",
        system1_answer="answer",
    )
    ok = "test" in result and "answer" in result and "ANTI-ANCHORING" in result
    report("EVALUATOR_USER_PROMPT empty thinking -> still formats", ok)


def test_thinking_template_empty():
    """_THINKING_SECTION_TEMPLATE with empty thinking should still format."""
    from ui.prompts import _THINKING_SECTION_TEMPLATE
    result = _THINKING_SECTION_TEMPLATE.format(thinking="")
    ok = "SYSTEM 1 INTERNAL REASONING" in result
    report("_THINKING_SECTION_TEMPLATE empty thinking -> still formats", ok)


def test_solver_extensions_correct_types():
    """SOLVER_EXTENSIONS values should be lists of strings starting with dot."""
    from ui.workspace import SOLVER_EXTENSIONS
    for solver, exts in SOLVER_EXTENSIONS.items():
        for ext in exts:
            if not ext.startswith("."):
                report(f"SOLVER_EXTENSIONS {solver} ext '{ext}' starts with dot", False)
                return
    report("SOLVER_EXTENSIONS all values start with dot", True)


def test_solver_lang_complete():
    """SOLVER_LANG should have entries for all 3 solvers."""
    from ui.workspace import SOLVER_LANG
    ok = set(SOLVER_LANG.keys()) == {"clingo", "z3", "vampire"}
    report("SOLVER_LANG has all 3 solvers", ok)


def test_workspace_paths_are_absolute():
    """WORKSPACE_MAP values should be absolute paths."""
    from ui.workspace import WORKSPACE_MAP
    for solver, path in WORKSPACE_MAP.items():
        if not path.is_absolute():
            report(f"WORKSPACE_MAP {solver} is absolute", False, f"Got: {path}")
            return
    report("WORKSPACE_MAP all paths are absolute", True)


def test_clear_all_workspaces_no_error():
    """clear_all_workspaces should not raise even if dirs don't exist."""
    from ui.workspace import clear_all_workspaces
    try:
        clear_all_workspaces()
        ok = True
    except Exception as e:
        ok = False
    report("clear_all_workspaces no error on empty dirs", ok)


def test_streaming_capture_write():
    """StreamingCapture.write should capture text and return length."""
    from ui.capture import StreamingCapture
    import sys
    cap = StreamingCapture()
    old_stdout = sys.stdout
    sys.stdout = cap
    try:
        n = cap.write("hello world")
        ok = n == 11 and "hello world" in cap.getvalue()
    finally:
        sys.stdout = old_stdout
    report("StreamingCapture.write captures text", ok)


def test_streaming_capture_thread_safe():
    """StreamingCapture.getvalue should be thread-safe."""
    from ui.capture import StreamingCapture
    import threading
    cap = StreamingCapture()
    results = []
    def writer():
        for i in range(100):
            cap.write(f"line{i}\n")
    threads = [threading.Thread(target=writer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    val = cap.getvalue()
    ok = len(val) > 0 and val.count("line") == 400
    report("StreamingCapture thread-safe write from 4 threads", ok, f"Got {val.count('line')} lines")


def test_build_config_with_workspace_path():
    """build_config with workspace_path should set env vars."""
    from ui.config import build_config
    from pathlib import Path
    ws = Path("/tmp/test_ws")
    cfg = build_config("google", "test", "vampire", True, "high", 0.0, 1.0, 42, 4, workspace_path=ws)
    server = cfg.mcp_servers.get("vampire")
    ok = server is not None and server.env is not None and server.env.get("VAMPIRE_WORKSPACE") == str(ws)
    report("build_config workspace_path sets VAMPIRE_WORKSPACE env", ok)


def test_build_config_workspace_path_clingo():
    """build_config with workspace_path for clingo should set CLINGO_WORKSPACE."""
    from ui.config import build_config
    from pathlib import Path
    ws = Path("/tmp/clingo_ws")
    cfg = build_config("google", "test", "clingo", True, "high", 0.0, 1.0, 42, 4, workspace_path=ws)
    server = cfg.mcp_servers.get("clingo")
    ok = server is not None and server.env is not None and server.env.get("CLINGO_WORKSPACE") == str(ws)
    report("build_config workspace_path sets CLINGO_WORKSPACE env", ok)


def test_build_config_workspace_path_z3():
    """build_config with workspace_path for z3 should set Z3_WORKSPACE."""
    from ui.config import build_config
    from pathlib import Path
    ws = Path("/tmp/z3_ws")
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4, workspace_path=ws)
    server = cfg.mcp_servers.get("z3")
    ok = server is not None and server.env is not None and server.env.get("Z3_WORKSPACE") == str(ws)
    report("build_config workspace_path sets Z3_WORKSPACE env", ok)


def test_build_config_benchmark_sets_env():
    """build_config with benchmark should set NESYGMA_BENCHMARK env."""
    from ui.config import build_config
    cfg = build_config("google", "test", "z3", True, "high", 0.0, 1.0, 42, 4, benchmark="FOLIO")
    server = cfg.mcp_servers.get("z3")
    ok = server is not None and server.env is not None and server.env.get("NESYGMA_BENCHMARK") == "FOLIO"
    report("build_config benchmark sets NESYGMA_BENCHMARK env", ok)


def test_parse_output_tool_result_multiline():
    """Multi-line tool result should be captured as single section."""
    from ui.capture import parse_output
    raw = "[RESULT]\nline 1\nline 2\nline 3\n--- Iteration 2 ---"
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    ok = len(results) == 1 and "line 1" in results[0].content and "line 3" in results[0].content
    report("parse_output multi-line tool result -> single section", ok)


def test_parse_output_iteration_high_number():
    """Iteration with high number should parse correctly."""
    from ui.capture import parse_output
    raw = "--- Iteration 99 ---"
    sections = parse_output(raw)
    headers = [s for s in sections if s.type == "header"]
    ok = any("Iteration 99" in h.content for h in headers)
    report("parse_output Iteration 99 -> header", ok)


def test_parse_output_equals_header():
    """=== HEADER === should produce a header section."""
    from ui.capture import parse_output
    raw = "=== MY SECTION ==="
    sections = parse_output(raw)
    headers = [s for s in sections if s.type == "header"]
    ok = len(headers) >= 1 and "MY SECTION" in headers[0].content
    report("parse_output === HEADER === -> header section", ok)


def test_parse_output_truncated_token_usage():
    """Token usage with missing total line should still parse."""
    from ui.capture import parse_output
    raw = "TOKEN USAGE SUMMARY\n  Total input tokens:  100"
    sections = parse_output(raw)
    tokens = [s for s in sections if s.type == "token_usage"]
    ok = len(tokens) == 1 and "100" in tokens[0].content
    report("parse_output partial token usage -> still parses", ok)


def test_parse_output_token_usage_data_missing():
    """[TOKEN USAGE] Data missing message should parse as token_usage."""
    from ui.capture import parse_output
    raw = "[TOKEN USAGE] Data missing. Total tokens evaluated to 0."
    sections = parse_output(raw)
    tokens = [s for s in sections if s.type == "token_usage"]
    ok = len(tokens) == 1 and "Data missing" in tokens[0].content
    report("parse_output token usage data missing -> token_usage", ok)


def test_parse_output_tool_call_json_no_code():
    """Tool call with JSON args but no code key should render as JSON block."""
    from ui.capture import parse_output
    raw = '[MCP TOOL] run_solver\nArgs: {"filename": "test.lp"}\n'
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "filename" in tool_calls[0].content
    report("parse_output tool call JSON no code -> JSON block", ok)


def test_parse_output_tool_call_malformed_json():
    """Tool call with malformed JSON args should render as plain code block."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] run_solver\nArgs: {not valid json}\n"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "not valid json" in tool_calls[0].content
    report("parse_output tool call malformed JSON -> plain block", ok)


def test_parse_output_thinking_immediately_closed():
    """Same-line <THINKING></THINKING> — parser consumes whole line on open tag,
    so close tag is never seen. Subsequent text becomes thinking content."""
    from ui.capture import parse_output
    raw = "<THINKING></THINKING>\nanswer"
    sections = parse_output(raw)
    thinking = [s for s in sections if s.type == "thinking"]
    ok = len(thinking) == 1 and "answer" in thinking[0].content
    report("parse_output same-line open/close -> subsequent text as thinking", ok, f"Got {len(thinking)} thinking sections")


def test_parse_output_tool_call_with_multiline_args():
    """Tool call with multi-line args should capture all args lines."""
    from ui.capture import parse_output
    raw = '[MCP TOOL] write_file\nArgs: {\n  "filename": "test.lp",\n  "code": "a."\n}\n'
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "test.lp" in tool_calls[0].content
    report("parse_output tool call multiline args -> captured", ok)


# ═════════════════════════════ UNHAPPY PATH TESTS ════════════════════

def test_build_config_invalid_provider():
    """build_config with invalid provider should raise ValueError."""
    from ui.config import build_config
    try:
        build_config("invalid_provider", "test", "z3", True, "high", 0.0, 1.0, 42, 4)
        report("build_config invalid provider -> raises ValueError", False, "No exception raised")
    except ValueError:
        report("build_config invalid provider -> raises ValueError", True)


def test_extract_confidence_negative():
    """extract_confidence with negative number should still extract."""
    from ui.pipeline import extract_confidence
    # The regex only matches \d+ so negative numbers won't match
    ok = extract_confidence("Confidence: -5%") is None
    report("extract_confidence negative -> None (no match)", ok)


def test_extract_confidence_over_100():
    """extract_confidence with value over 100 should still extract."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 150%") == 150
    report("extract_confidence 150% -> 150 (no upper bound)", ok)


def test_extract_confidence_float():
    """extract_confidence with float should not match."""
    from ui.pipeline import extract_confidence
    ok = extract_confidence("Confidence: 85.5%") is None
    report("extract_confidence float -> None (no match)", ok)


def test_extract_solver_ranking_empty_list():
    """extract_solver_ranking with empty ranking list should return empty list."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": []}'
    result = extract_solver_ranking(text)
    ok = result == []
    report("extract_solver_ranking empty list -> empty list", ok, f"Got: {result}")


def test_extract_solver_ranking_invalid_json():
    """extract_solver_ranking with invalid JSON should return None."""
    from ui.pipeline import extract_solver_ranking
    text = '{"solver_ranking": [invalid}'
    result = extract_solver_ranking(text)
    ok = result is None
    report("extract_solver_ranking invalid JSON -> None", ok)


def test_extract_solver_ranking_no_solver_ranking_key():
    """extract_solver_ranking with JSON but no solver_ranking key should return None."""
    from ui.pipeline import extract_solver_ranking
    text = '{"other_key": ["z3"]}'
    result = extract_solver_ranking(text)
    ok = result is None
    report("extract_solver_ranking no solver_ranking key -> None", ok)


def test_parse_output_only_newlines():
    """Only newlines should produce no sections."""
    from ui.capture import parse_output
    sections = parse_output("\n\n\n")
    ok = len(sections) == 0
    report("parse_output only newlines -> no sections", ok)


def test_parse_output_result_at_end():
    """[RESULT] at end of input with no content should produce empty result."""
    from ui.capture import parse_output
    raw = "[RESULT]"
    sections = parse_output(raw)
    # Should have no sections since the result content is empty
    ok = len(sections) == 0
    report("parse_output [RESULT] at end -> no sections", ok)


def test_parse_output_tool_call_at_end():
    """Tool call at end of input with no args should still produce section."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] my_tool"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(tool_calls) == 1 and "my_tool" in tool_calls[0].label
    report("parse_output tool call at end -> still works", ok)


def test_parse_output_thinking_with_tool_inside():
    """Thinking block containing [MCP TOOL] text should be treated as thinking."""
    from ui.capture import parse_output
    raw = "<THINKING>\nI should call [MCP TOOL] write_file\n</THINKING>"
    sections = parse_output(raw)
    thinking = [s for s in sections if s.type == "thinking"]
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = len(thinking) == 1 and len(tool_calls) == 0
    report("parse_output [MCP TOOL] inside thinking -> stays thinking", ok)


def test_parse_output_result_with_iteration_exit():
    """[RESULT] should exit on --- Iteration --- line."""
    from ui.capture import parse_output
    raw = "[RESULT]\nresult 1\n--- Iteration 2 ---\nmore text"
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    ok = len(results) == 1 and "result 1" in results[0].content and "more text" not in results[0].content
    report("parse_output [RESULT] exits on Iteration", ok)


def test_parse_output_result_with_mcp_tool_exit():
    """[RESULT] should exit on [MCP TOOL] line."""
    from ui.capture import parse_output
    raw = "[RESULT]\nresult 1\n[MCP TOOL] next_tool\nArgs: {}"
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    ok = len(results) == 1 and "result 1" in results[0].content
    report("parse_output [RESULT] exits on [MCP TOOL]", ok)


def test_parse_output_result_with_token_usage_exit():
    """[RESULT] should exit on TOKEN USAGE line."""
    from ui.capture import parse_output
    raw = "[RESULT]\nresult 1\nTOKEN USAGE SUMMARY\n  Total input tokens:  100"
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    tokens = [s for s in sections if s.type == "token_usage"]
    ok = len(results) == 1 and len(tokens) == 1
    report("parse_output [RESULT] exits on TOKEN USAGE", ok)


def test_parse_output_result_with_complete_exit():
    """[RESULT] should exit on COMPLETE line."""
    from ui.capture import parse_output
    raw = "[RESULT]\nresult 1\nCOMPLETE"
    sections = parse_output(raw)
    results = [s for s in sections if s.type == "tool_result"]
    headers = [s for s in sections if s.type == "header"]
    ok = len(results) == 1 and len(headers) == 1
    report("parse_output [RESULT] exits on COMPLETE", ok)


def test_parse_output_label_preserved():
    """Tool call label should be preserved across sections."""
    from ui.capture import parse_output
    raw = "[MCP TOOL] write_clingo_file\nArgs: {}\n[RESULT]\nok\n[MCP TOOL] run_clingo\nArgs: {}"
    sections = parse_output(raw)
    tool_calls = [s for s in sections if s.type == "tool_call"]
    ok = (
        len(tool_calls) == 2
        and tool_calls[0].label == "write_clingo_file"
        and tool_calls[1].label == "run_clingo"
    )
    report("parse_output tool labels preserved", ok)


def test_parse_output_current_type_resets():
    """After thinking block, text should be 'text' type not 'thinking'."""
    from ui.capture import parse_output
    raw = "<THINKING>\nreasoning\n</THINKING>\nnormal text here"
    sections = parse_output(raw)
    texts = [s for s in sections if s.type == "text"]
    ok = len(texts) >= 1 and "normal text" in texts[0].content
    report("parse_output type resets after thinking -> text", ok)


# ═════════════════════════════ MAIN ══════════════════════════════════

def main():
    print(f"\n{BOLD}=== UI Module - Comprehensive Tests ==={RESET}\n")

    tests = [
        ("Config: Provider Models", [
            test_provider_models_keys,
            test_all_providers_valid_enum,
            test_all_efforts_contains_xhigh,
        ]),
        ("Config: build_config (Happy Path)", [
            test_build_config_google,
            test_build_config_openrouter_with_extra_body,
            test_build_config_mcp_servers,
            test_build_config_no_extra_body,
            test_build_config_all_solvers,
            test_build_config_max_output_tokens,
            test_build_config_temperature,
            test_build_config_all_providers,
            test_build_config_reasoning_disabled,
            test_build_config_seed,
            test_build_config_top_p,
            test_build_config_max_iterations,
            test_build_config_with_benchmark,
            test_build_config_mcp_server_args,
        ]),
        ("Config: build_config (Unhappy Path)", [
            test_build_config_invalid_provider,
        ]),
        ("Config: OpenRouter Models", [
            test_openrouter_models_unique_labels,
            test_openrouter_models_have_required_keys,
        ]),
        ("Capture: parse_output (Happy Path)", [
            test_parse_output_empty,
            test_parse_output_thinking_tags,
            test_parse_output_think_tags,
            test_parse_output_tool_call,
            test_parse_output_tool_result,
            test_parse_output_token_usage,
            test_parse_output_token_usage_bracket,
            test_parse_output_iteration_header,
            test_parse_output_complete_header,
            test_parse_output_result_then_token_usage,
            test_parse_output_no_separator_in_token_usage,
            test_parse_output_mcp_agent_header,
            test_parse_output_query_text,
            test_parse_output_tool_call_with_json_args,
            test_parse_output_tool_call_with_plain_args,
            test_parse_output_mixed_thinking_and_tools,
            test_parse_output_special_characters,
            test_parse_output_equals_header,
            test_parse_output_truncated_token_usage,
            test_parse_output_token_usage_data_missing,
            test_parse_output_tool_call_json_no_code,
            test_parse_output_tool_call_malformed_json,
            test_parse_output_tool_call_with_multiline_args,
            test_parse_output_tool_result_multiline,
            test_parse_output_iteration_high_number,
            test_parse_output_label_preserved,
            test_parse_output_current_type_resets,
        ]),
        ("Capture: parse_output (Edge Cases)", [
            test_parse_output_multiple_thinking_blocks,
            test_parse_output_nested_json_in_tool_result,
            test_parse_output_plain_text_between_sections,
            test_parse_output_only_whitespace,
            test_parse_output_only_newlines,
            test_parse_output_unclosed_thinking,
            test_parse_output_consecutive_tool_calls,
            test_parse_output_tool_call_no_args,
            test_parse_output_thinking_immediately_closed,
            test_parse_output_thinking_with_tool_inside,
            test_parse_output_result_at_end,
            test_parse_output_tool_call_at_end,
            test_parse_output_result_with_iteration_exit,
            test_parse_output_result_with_mcp_tool_exit,
            test_parse_output_result_with_token_usage_exit,
            test_parse_output_result_with_complete_exit,
        ]),
        ("Capture: extract_thinking_trace", [
            test_extract_thinking_trace,
            test_extract_thinking_trace_think_tags,
            test_extract_thinking_trace_empty,
            test_extract_thinking_trace_multiple,
        ]),
        ("Pipeline: extract_confidence (Happy Path)", [
            test_extract_confidence_basic,
            test_extract_confidence_case_insensitive,
            test_extract_confidence_zero,
            test_extract_confidence_hundred,
            test_extract_confidence_in_long_text,
            test_extract_confidence_multiple_matches,
        ]),
        ("Pipeline: extract_confidence (Unhappy Path)", [
            test_extract_confidence_none,
            test_extract_confidence_empty,
            test_extract_confidence_negative,
            test_extract_confidence_over_100,
            test_extract_confidence_float,
        ]),
        ("Pipeline: extract_solver_ranking (Happy Path)", [
            test_extract_solver_ranking_json_block,
            test_extract_solver_ranking_raw_json,
            test_extract_solver_ranking_normalizes_case,
            test_extract_solver_ranking_strips_whitespace,
            test_extract_solver_ranking_single_solver,
            test_extract_solver_ranking_json_block_with_extra,
            test_extract_solver_ranking_with_surrounding_text,
        ]),
        ("Pipeline: extract_solver_ranking (Unhappy Path)", [
            test_extract_solver_ranking_none,
            test_extract_solver_ranking_empty,
            test_extract_solver_ranking_empty_list,
            test_extract_solver_ranking_invalid_json,
            test_extract_solver_ranking_no_solver_ranking_key,
        ]),
        ("Workspace", [
            test_workspace_map_keys,
            test_solver_extensions_complete,
            test_solver_extensions_correct_types,
            test_solver_lang_complete,
            test_workspace_paths_are_absolute,
            test_get_workspace_files_nonexistent,
            test_get_workspace_files_unknown_solver,
            test_clear_all_workspaces_no_error,
        ]),
        ("Prompts", [
            test_evaluator_prompt_format,
            test_thinking_section_template_format,
            test_evaluator_prompt_anti_anchoring,
            test_evaluator_prompt_empty_thinking,
            test_thinking_template_empty,
        ]),
        ("StreamingCapture", [
            test_streaming_capture_write,
            test_streaming_capture_thread_safe,
        ]),
        ("build_config Edge Cases", [
            test_build_config_with_workspace_path,
            test_build_config_workspace_path_clingo,
            test_build_config_workspace_path_z3,
            test_build_config_benchmark_sets_env,
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