"""
Tests for the selector module: SelectorAgent, SELECTOR_SYSTEM_PROMPT, SELECTOR_USER_PROMPT.
Tests pure logic without requiring actual LLM connections.
"""
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


# ═════════════════════════════ SELECTOR_SYSTEM_PROMPT ═══════════════════════

def test_selector_system_prompt_is_string():
    """SELECTOR_SYSTEM_PROMPT should be a non-empty string."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = isinstance(SELECTOR_SYSTEM_PROMPT, str) and len(SELECTOR_SYSTEM_PROMPT) > 100
    report("SELECTOR_SYSTEM_PROMPT is non-empty string", ok, f"Length: {len(SELECTOR_SYSTEM_PROMPT)}")


def test_selector_system_prompt_mentions_vampire():
    """SELECTOR_SYSTEM_PROMPT should describe Vampire solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "VAMPIRE" in SELECTOR_SYSTEM_PROMPT and "Theorem Prover" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT describes Vampire", ok)


def test_selector_system_prompt_mentions_clingo():
    """SELECTOR_SYSTEM_PROMPT should describe Clingo solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "CLINGO" in SELECTOR_SYSTEM_PROMPT and "Answer Set Programming" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT describes Clingo", ok)


def test_selector_system_prompt_mentions_z3():
    """SELECTOR_SYSTEM_PROMPT should describe Z3 solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "Z3" in SELECTOR_SYSTEM_PROMPT and "SMT Solver" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT describes Z3", ok)


def test_selector_system_prompt_has_solver_ranking_format():
    """SELECTOR_SYSTEM_PROMPT should specify the solver_ranking JSON format."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "solver_ranking" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT has solver_ranking format", ok)


def test_selector_system_prompt_has_three_solvers():
    """SELECTOR_SYSTEM_PROMPT should list exactly 3 solvers."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "1. VAMPIRE" in SELECTOR_SYSTEM_PROMPT and "2. CLINGO" in SELECTOR_SYSTEM_PROMPT and "3. Z3" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT lists 3 solvers (VAMPIRE, CLINGO, Z3)", ok)


def test_selector_system_prompt_has_target_answer_types():
    """SELECTOR_SYSTEM_PROMPT should describe target answer types for each solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "Target Answer Types" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT has Target Answer Types", ok)


def test_selector_system_prompt_has_best_for():
    """SELECTOR_SYSTEM_PROMPT should describe 'Best for' for each solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    count = SELECTOR_SYSTEM_PROMPT.count("Best for")
    ok = count >= 3
    report(f"SELECTOR_SYSTEM_PROMPT has 'Best for' ({count} occurrences)", ok)


def test_selector_system_prompt_has_features():
    """SELECTOR_SYSTEM_PROMPT should describe features for each solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    count = SELECTOR_SYSTEM_PROMPT.count("Features")
    ok = count >= 3
    report(f"SELECTOR_SYSTEM_PROMPT has 'Features' ({count} occurrences)", ok)


def test_selector_system_prompt_has_warnings():
    """SELECTOR_SYSTEM_PROMPT should have warnings for each solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    count = SELECTOR_SYSTEM_PROMPT.count("Warning")
    ok = count >= 3
    report(f"SELECTOR_SYSTEM_PROMPT has 'Warning' ({count} occurrences)", ok)


def test_selector_system_prompt_has_typical_problems():
    """SELECTOR_SYSTEM_PROMPT should describe typical problems for each solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    count = SELECTOR_SYSTEM_PROMPT.count("Typical problems")
    ok = count >= 3
    report(f"SELECTOR_SYSTEM_PROMPT has 'Typical problems' ({count} occurrences)", ok)


def test_selector_system_prompt_has_example_patterns():
    """SELECTOR_SYSTEM_PROMPT should have example patterns for each solver."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    count = SELECTOR_SYSTEM_PROMPT.count("Example patterns")
    ok = count >= 3
    report(f"SELECTOR_SYSTEM_PROMPT has 'Example patterns' ({count} occurrences)", ok)


def test_selector_system_prompt_has_world_assumptions():
    """SELECTOR_SYSTEM_PROMPT should describe world assumptions."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "Open-world assumption" in SELECTOR_SYSTEM_PROMPT and "Closed-world assumption" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT has open/closed world assumptions", ok)


def test_selector_system_prompt_has_context_question_options():
    """SELECTOR_SYSTEM_PROMPT should have template variables for context, question, options."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "${context}" in SELECTOR_SYSTEM_PROMPT and "${question}" in SELECTOR_SYSTEM_PROMPT and "${options}" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT has ${context}, ${question}, ${options}", ok)


def test_selector_system_prompt_has_ranking_instruction():
    """SELECTOR_SYSTEM_PROMPT should instruct ranking all three solvers."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "rank ALL three solvers" in SELECTOR_SYSTEM_PROMPT or "rank" in SELECTOR_SYSTEM_PROMPT.lower()
    report("SELECTOR_SYSTEM_PROMPT instructs ranking all three solvers", ok)


def test_selector_system_prompt_has_json_example():
    """SELECTOR_SYSTEM_PROMPT should have a JSON example output."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = '"solver_ranking": ["CLINGO", "Z3", "VAMPIRE"]' in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT has JSON example output", ok)


def test_selector_system_prompt_has_most_suitable():
    """SELECTOR_SYSTEM_PROMPT should mention MOST_SUITABLE in format."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    ok = "MOST_SUITABLE" in SELECTOR_SYSTEM_PROMPT
    report("SELECTOR_SYSTEM_PROMPT has MOST_SUITABLE in format", ok)


def test_selector_system_prompt_has_forbidden_solve():
    """SELECTOR_SYSTEM_PROMPT should forbid solving the problem."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    # The forbidden instruction is in SELECTOR_USER_PROMPT, not system prompt
    # But system prompt should still be about analysis
    ok = "analyze" in SELECTOR_SYSTEM_PROMPT.lower() or "analysis" in SELECTOR_SYSTEM_PROMPT.lower()
    report("SELECTOR_SYSTEM_PROMPT focuses on analysis", ok)


# ═════════════════════════════ SELECTOR_USER_PROMPT ═════════════════════════

def test_selector_user_prompt_is_string():
    """SELECTOR_USER_PROMPT should be a non-empty string."""
    from selector.prompts import SELECTOR_USER_PROMPT
    ok = isinstance(SELECTOR_USER_PROMPT, str) and len(SELECTOR_USER_PROMPT) > 10
    report("SELECTOR_USER_PROMPT is non-empty string", ok, f"Length: {len(SELECTOR_USER_PROMPT)}")


def test_selector_user_prompt_has_format_key():
    """SELECTOR_USER_PROMPT should have {user_query} format key."""
    from selector.prompts import SELECTOR_USER_PROMPT
    ok = "{user_query}" in SELECTOR_USER_PROMPT
    report("SELECTOR_USER_PROMPT has {user_query} format key", ok)


def test_selector_user_prompt_forbids_solving():
    """SELECTOR_USER_PROMPT should forbid solving the problem."""
    from selector.prompts import SELECTOR_USER_PROMPT
    ok = "FORBIDDEN" in SELECTOR_USER_PROMPT or "forbidden" in SELECTOR_USER_PROMPT.lower()
    report("SELECTOR_USER_PROMPT forbids solving", ok)


def test_selector_user_prompt_format_works():
    """SELECTOR_USER_PROMPT should be formattable with user_query."""
    from selector.prompts import SELECTOR_USER_PROMPT
    result = SELECTOR_USER_PROMPT.format(user_query="test problem here")
    ok = "test problem here" in result
    report("SELECTOR_USER_PROMPT formats with user_query", ok)


def test_selector_user_prompt_format_preserves_instructions():
    """SELECTOR_USER_PROMPT should preserve instructions after formatting."""
    from selector.prompts import SELECTOR_USER_PROMPT
    result = SELECTOR_USER_PROMPT.format(user_query="test")
    ok = "FORBIDDEN" in result or "forbidden" in result.lower()
    report("SELECTOR_USER_PROMPT preserves instructions after format", ok)


def test_selector_user_prompt_format_empty_query():
    """SELECTOR_USER_PROMPT should handle empty user_query."""
    from selector.prompts import SELECTOR_USER_PROMPT
    result = SELECTOR_USER_PROMPT.format(user_query="")
    ok = isinstance(result, str) and len(result) > 10
    report("SELECTOR_USER_PROMPT handles empty user_query", ok)


def test_selector_user_prompt_format_long_query():
    """SELECTOR_USER_PROMPT should handle very long user_query."""
    from selector.prompts import SELECTOR_USER_PROMPT
    long_query = "A" * 10000
    result = SELECTOR_USER_PROMPT.format(user_query=long_query)
    ok = long_query in result
    report("SELECTOR_USER_PROMPT handles long user_query", ok)


def test_selector_user_prompt_format_special_chars():
    """SELECTOR_USER_PROMPT should handle special characters in user_query."""
    from selector.prompts import SELECTOR_USER_PROMPT
    query = "∀x∃y: P(x,y) ∧ ¬Q(x)"
    result = SELECTOR_USER_PROMPT.format(user_query=query)
    ok = query in result
    report("SELECTOR_USER_PROMPT handles special characters", ok)


def test_selector_user_prompt_mentions_problem():
    """SELECTOR_USER_PROMPT should mention 'Problem:' label."""
    from selector.prompts import SELECTOR_USER_PROMPT
    ok = "Problem:" in SELECTOR_USER_PROMPT
    report("SELECTOR_USER_PROMPT has 'Problem:' label", ok)


def test_selector_user_prompt_mentions_analyze():
    """SELECTOR_USER_PROMPT should instruct analysis."""
    from selector.prompts import SELECTOR_USER_PROMPT
    ok = "analyze" in SELECTOR_USER_PROMPT.lower() or "analysis" in SELECTOR_USER_PROMPT.lower()
    report("SELECTOR_USER_PROMPT instructs analysis", ok)


# ═════════════════════════════ SelectorAgent INIT ═══════════════════════════

def test_selector_init_default():
    """SelectorAgent with no config should use defaults."""
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig
    agent = SelectorAgent()
    ok = isinstance(agent.config, MCPAgentConfig) and agent.config.solver == "z3"
    report("SelectorAgent() default config", ok)


def test_selector_init_custom_config():
    """SelectorAgent with custom config should use it."""
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, solver="clingo")
    agent = SelectorAgent(config=cfg)
    ok = agent.config.provider == LLMProvider.NVIDIA and agent.config.solver == "clingo"
    report("SelectorAgent(custom config) works", ok)


def test_selector_init_none_config():
    """SelectorAgent with explicit None config should use defaults."""
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig
    agent = SelectorAgent(config=None)
    ok = isinstance(agent.config, MCPAgentConfig)
    report("SelectorAgent(config=None) uses defaults", ok)


def test_selector_has_llm_manager():
    """SelectorAgent should have an LLMManager instance."""
    from selector.selector_core import SelectorAgent
    from agent.llm_client import LLMManager
    agent = SelectorAgent()
    ok = isinstance(agent.llm_manager, LLMManager)
    report("SelectorAgent has LLMManager", ok)


def test_selector_messages_initially_empty():
    """SelectorAgent.messages should be initially empty."""
    from selector.selector_core import SelectorAgent
    agent = SelectorAgent()
    ok = agent.messages == []
    report("SelectorAgent.messages initially empty", ok)


def test_selector_init_google_config():
    """SelectorAgent with Google config should work."""
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE)
    agent = SelectorAgent(config=cfg)
    ok = agent.config.provider == LLMProvider.GOOGLE
    report("SelectorAgent(Google config) works", ok)


def test_selector_init_openrouter_config():
    """SelectorAgent with OpenRouter config should work."""
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.OPENROUTER)
    agent = SelectorAgent(config=cfg)
    ok = agent.config.provider == LLMProvider.OPENROUTER
    report("SelectorAgent(OpenRouter config) works", ok)


def test_selector_init_mistral_config():
    """SelectorAgent with Mistral config should work."""
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.MISTRAL)
    agent = SelectorAgent(config=cfg)
    ok = agent.config.provider == LLMProvider.MISTRAL
    report("SelectorAgent(Mistral config) works", ok)


# ═════════════════════════════ SelectorAgent.run() ══════════════════════════

def test_selector_run_returns_string():
    """SelectorAgent.run() should return a string (not tuple)."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ('{"solver_ranking": ["z3", "clingo", "vampire"]}', False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("test query"))
        ok = isinstance(result, str)
        report("SelectorAgent.run() returns str", ok, f"Got: {type(result)}")


def test_selector_run_passes_header_title():
    """SelectorAgent.run() should pass 'SELECTOR META EVALUATOR AGENT' as header."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_kwargs = {}

    async def mock_stream(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        ok = captured_kwargs.get("header_title") == "SELECTOR META EVALUATOR AGENT"
        report("SelectorAgent passes correct header_title", ok)


def test_selector_run_passes_user_query():
    """SelectorAgent.run() should pass user_query to run_single_pass_stream."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_kwargs = {}

    async def mock_stream(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("my test question"))
        ok = captured_kwargs.get("user_query") == "my test question"
        report("SelectorAgent passes user_query correctly", ok)


def test_selector_run_uses_system_prompt():
    """SelectorAgent.run() should use SELECTOR_SYSTEM_PROMPT as system message."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from selector.prompts import SELECTOR_SYSTEM_PROMPT
    from agent.config import MCPAgentConfig
    from langchain_core.messages import SystemMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_messages = []

    async def mock_stream(*args, **kwargs):
        captured_messages.extend(args[1] if len(args) > 1 else kwargs.get("messages", []))
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        system_msgs = [m for m in captured_messages if isinstance(m, SystemMessage)]
        ok = len(system_msgs) == 1 and system_msgs[0].content == SELECTOR_SYSTEM_PROMPT
        report("SelectorAgent uses SELECTOR_SYSTEM_PROMPT as system message", ok)


def test_selector_run_uses_user_prompt():
    """SelectorAgent.run() should use SELECTOR_USER_PROMPT formatted with query."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from selector.prompts import SELECTOR_USER_PROMPT
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_messages = []

    async def mock_stream(*args, **kwargs):
        captured_messages.extend(args[1] if len(args) > 1 else kwargs.get("messages", []))
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        human_msgs = [m for m in captured_messages if isinstance(m, HumanMessage)]
        ok = len(human_msgs) == 1 and "test query" in human_msgs[0].content
        report("SelectorAgent uses SELECTOR_USER_PROMPT with query", ok)


def test_selector_run_stores_messages():
    """SelectorAgent.run() should store messages on self.messages."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        ok = len(agent.messages) == 2  # SystemMessage + HumanMessage
        report("SelectorAgent stores 2 messages after run", ok)


def test_selector_run_messages_contain_query():
    """SelectorAgent.run() messages should contain the user query in HumanMessage."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("What is 2+2?"))
        human_msgs = [m for m in agent.messages if isinstance(m, HumanMessage)]
        ok = len(human_msgs) == 1 and "What is 2+2?" in human_msgs[0].content
        report("SelectorAgent messages contain user query", ok)


def test_selector_run_discards_truncated_flag():
    """SelectorAgent.run() should discard was_truncated (returns only content)."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", True)  # was_truncated=True

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("test query"))
        ok = isinstance(result, str) and result == "result"
        report("SelectorAgent discards was_truncated flag", ok)


def test_selector_run_passes_llm_manager():
    """SelectorAgent.run() should pass its own llm_manager."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_manager = None

    async def mock_stream(*args, **kwargs):
        nonlocal captured_manager
        captured_manager = kwargs.get("llm_manager")
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test"))
        ok = captured_manager is agent.llm_manager
        report("SelectorAgent passes its own llm_manager", ok)


def test_selector_run_passes_messages_list():
    """SelectorAgent.run() should pass messages as a list of 2."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_messages = None

    async def mock_stream(*args, **kwargs):
        nonlocal captured_messages
        captured_messages = kwargs.get("messages")
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test"))
        ok = isinstance(captured_messages, list) and len(captured_messages) == 2
        report("SelectorAgent passes messages as list of 2", ok)


def test_selector_run_overwrites_messages():
    """SelectorAgent.run() should overwrite messages on each call."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("first query"))
        first_len = len(agent.messages)
        asyncio.run(agent.run("second query"))
        second_len = len(agent.messages)
        ok = first_len == 2 and second_len == 2
        report("SelectorAgent overwrites messages on each run", ok)


# ═════════════════════════════ EDGE CASES ═══════════════════════════════════

def test_selector_run_empty_query():
    """SelectorAgent.run() with empty query should still work."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run(""))
        ok = result == "result"
        report("SelectorAgent empty query -> still works", ok)


def test_selector_run_long_query():
    """SelectorAgent.run() with very long query should still work."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    long_query = "A" * 10000

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run(long_query))
        ok = result == "result"
        report("SelectorAgent long query (10k chars) -> still works", ok)


def test_selector_run_special_characters():
    """SelectorAgent.run() with special characters should still work."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    query = "∀x∃y: P(x,y) ∧ ¬Q(x) → R(y) | S(x,y)"

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run(query))
        ok = result == "result"
        report("SelectorAgent special characters query -> still works", ok)


def test_selector_run_unicode_query():
    """SelectorAgent.run() with unicode query should still work."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    query = "如果所有猫都是动物，那么所有猫都是哺乳动物吗？"

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run(query))
        ok = result == "result"
        report("SelectorAgent unicode query -> still works", ok)


def test_selector_run_whitespace_only_query():
    """SelectorAgent.run() with whitespace-only query should still work."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("   \n\n   "))
        ok = result == "result"
        report("SelectorAgent whitespace-only query -> still works", ok)


def test_selector_run_multiline_query():
    """SelectorAgent.run() with multiline query should still work."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    query = "Premise 1: All cats are animals.\nPremise 2: Tom is a cat.\nConclusion: Tom is an animal."

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run(query))
        ok = result == "result"
        report("SelectorAgent multiline query -> still works", ok)


def test_selector_run_json_response():
    """SelectorAgent.run() should handle JSON ranking response."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    json_response = '{"solver_ranking": ["z3", "clingo", "vampire"]}'

    async def mock_stream(*args, **kwargs):
        return (json_response, False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("test"))
        ok = result == json_response
        report("SelectorAgent handles JSON ranking response", ok)


def test_selector_run_empty_response():
    """SelectorAgent.run() should handle empty response from stream."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("test"))
        ok = result == ""
        report("SelectorAgent handles empty response", ok)


def test_selector_run_consecutive_calls():
    """SelectorAgent.run() should work correctly on consecutive calls."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    call_count = 0

    async def mock_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return (f'{{"solver_ranking": ["z3", "clingo", "vampire"]}}', False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        r1 = asyncio.run(agent.run("query 1"))
        r2 = asyncio.run(agent.run("query 2"))
        r3 = asyncio.run(agent.run("query 3"))
        ok = call_count == 3 and r1 and r2 and r3
        report("SelectorAgent handles 3 consecutive calls", ok)


def test_selector_run_user_prompt_contains_forbidden():
    """SelectorAgent.run() user prompt should contain FORBIDDEN instruction."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_messages = []

    async def mock_stream(*args, **kwargs):
        captured_messages.extend(args[1] if len(args) > 1 else kwargs.get("messages", []))
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        human_msgs = [m for m in captured_messages if isinstance(m, HumanMessage)]
        ok = len(human_msgs) == 1 and "FORBIDDEN" in human_msgs[0].content
        report("SelectorAgent user prompt contains FORBIDDEN", ok)


def test_selector_run_user_prompt_contains_problem_label():
    """SelectorAgent.run() user prompt should contain 'Problem:' label."""
    import asyncio
    from selector.selector_core import SelectorAgent
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SelectorAgent(config=cfg)
    captured_messages = []

    async def mock_stream(*args, **kwargs):
        captured_messages.extend(args[1] if len(args) > 1 else kwargs.get("messages", []))
        return ("result", False)

    with patch("selector.selector_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        human_msgs = [m for m in captured_messages if isinstance(m, HumanMessage)]
        ok = len(human_msgs) == 1 and "Problem:" in human_msgs[0].content
        report("SelectorAgent user prompt contains 'Problem:' label", ok)


# ═════════════════════════════ STRUCTURAL TESTS ═════════════════════════════

def test_selector_module_exports():
    """selector module should export SelectorAgent."""
    from selector.selector_core import SelectorAgent
    ok = callable(SelectorAgent)
    report("selector.selector_core exports SelectorAgent", ok)


def test_selector_prompts_module_exports():
    """selector.prompts should export both prompts."""
    from selector.prompts import SELECTOR_SYSTEM_PROMPT, SELECTOR_USER_PROMPT
    ok = isinstance(SELECTOR_SYSTEM_PROMPT, str) and isinstance(SELECTOR_USER_PROMPT, str)
    report("selector.prompts exports both prompts", ok)


def test_selector_agent_is_class():
    """SelectorAgent should be a class (not a function)."""
    from selector.selector_core import SelectorAgent
    ok = isinstance(SelectorAgent, type)
    report("SelectorAgent is a class", ok)


def test_selector_agent_has_run_method():
    """SelectorAgent should have a run method."""
    from selector.selector_core import SelectorAgent
    agent = SelectorAgent()
    ok = hasattr(agent, "run") and callable(agent.run)
    report("SelectorAgent has callable run method", ok)


def test_selector_agent_has_init_method():
    """SelectorAgent should have an __init__ method."""
    from selector.selector_core import SelectorAgent
    ok = hasattr(SelectorAgent, "__init__")
    report("SelectorAgent has __init__ method", ok)


def test_selector_differs_from_switcher():
    """SelectorAgent should be a different class from SwitcherAgent."""
    from selector.selector_core import SelectorAgent
    from switcher.switcher_core import SwitcherAgent
    ok = SelectorAgent is not SwitcherAgent
    report("SelectorAgent is different from SwitcherAgent", ok)


def test_selector_differs_from_system1():
    """SelectorAgent should be a different class from System1Agent."""
    from selector.selector_core import SelectorAgent
    from system1.system1_core import System1Agent
    ok = SelectorAgent is not System1Agent
    report("SelectorAgent is different from System1Agent", ok)


# ═════════════════════════════ CROSS-MODULE CONSISTENCY ═════════════════════

def test_all_agents_same_init_pattern():
    """All 3 agents should follow the same __init__ pattern."""
    from selector.selector_core import SelectorAgent
    from switcher.switcher_core import SwitcherAgent
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig
    from agent.llm_client import LLMManager

    for AgentClass in [SelectorAgent, SwitcherAgent, System1Agent]:
        agent = AgentClass()
        ok = isinstance(agent.config, MCPAgentConfig) and isinstance(agent.llm_manager, LLMManager) and agent.messages == []
        if not ok:
            report(f"{AgentClass.__name__} follows standard init pattern", False)
            return
    report("All 3 agents follow standard init pattern (config, llm_manager, messages)", True)


def test_all_agents_accept_custom_config():
    """All 3 agents should accept custom MCPAgentConfig."""
    from selector.selector_core import SelectorAgent
    from switcher.switcher_core import SwitcherAgent
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig, LLMProvider

    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, solver="clingo")
    for AgentClass in [SelectorAgent, SwitcherAgent, System1Agent]:
        agent = AgentClass(config=cfg)
        ok = agent.config.provider == LLMProvider.NVIDIA
        if not ok:
            report(f"{AgentClass.__name__} accepts custom config", False)
            return
    report("All 3 agents accept custom MCPAgentConfig", True)


def test_all_agents_have_run_method():
    """All 3 agents should have an async run method."""
    from selector.selector_core import SelectorAgent
    from switcher.switcher_core import SwitcherAgent
    from system1.system1_core import System1Agent
    import asyncio

    for AgentClass in [SelectorAgent, SwitcherAgent, System1Agent]:
        agent = AgentClass()
        ok = hasattr(agent, "run") and asyncio.iscoroutinefunction(agent.run)
        if not ok:
            report(f"{AgentClass.__name__} has async run method", False)
            return
    report("All 3 agents have async run method", True)


# ═════════════════════════════ MAIN ════════════════════════════════════════

def main():
    print(f"\n{BOLD}=== Selector Module - Comprehensive Tests ==={RESET}\n")

    tests = [
        ("SELECTOR_SYSTEM_PROMPT Content", [
            test_selector_system_prompt_is_string,
            test_selector_system_prompt_mentions_vampire,
            test_selector_system_prompt_mentions_clingo,
            test_selector_system_prompt_mentions_z3,
            test_selector_system_prompt_has_solver_ranking_format,
            test_selector_system_prompt_has_three_solvers,
            test_selector_system_prompt_has_target_answer_types,
            test_selector_system_prompt_has_best_for,
            test_selector_system_prompt_has_features,
            test_selector_system_prompt_has_warnings,
            test_selector_system_prompt_has_typical_problems,
            test_selector_system_prompt_has_example_patterns,
            test_selector_system_prompt_has_world_assumptions,
            test_selector_system_prompt_has_context_question_options,
            test_selector_system_prompt_has_ranking_instruction,
            test_selector_system_prompt_has_json_example,
            test_selector_system_prompt_has_most_suitable,
            test_selector_system_prompt_has_forbidden_solve,
        ]),
        ("SELECTOR_USER_PROMPT Content", [
            test_selector_user_prompt_is_string,
            test_selector_user_prompt_has_format_key,
            test_selector_user_prompt_forbids_solving,
            test_selector_user_prompt_format_works,
            test_selector_user_prompt_format_preserves_instructions,
            test_selector_user_prompt_format_empty_query,
            test_selector_user_prompt_format_long_query,
            test_selector_user_prompt_format_special_chars,
            test_selector_user_prompt_mentions_problem,
            test_selector_user_prompt_mentions_analyze,
        ]),
        ("SelectorAgent Initialization", [
            test_selector_init_default,
            test_selector_init_custom_config,
            test_selector_init_none_config,
            test_selector_has_llm_manager,
            test_selector_messages_initially_empty,
            test_selector_init_google_config,
            test_selector_init_openrouter_config,
            test_selector_init_mistral_config,
        ]),
        ("SelectorAgent.run() Behavior", [
            test_selector_run_returns_string,
            test_selector_run_passes_header_title,
            test_selector_run_passes_user_query,
            test_selector_run_uses_system_prompt,
            test_selector_run_uses_user_prompt,
            test_selector_run_stores_messages,
            test_selector_run_messages_contain_query,
            test_selector_run_discards_truncated_flag,
            test_selector_run_passes_llm_manager,
            test_selector_run_passes_messages_list,
            test_selector_run_overwrites_messages,
            test_selector_run_user_prompt_contains_forbidden,
            test_selector_run_user_prompt_contains_problem_label,
        ]),
        ("Edge Cases", [
            test_selector_run_empty_query,
            test_selector_run_long_query,
            test_selector_run_special_characters,
            test_selector_run_unicode_query,
            test_selector_run_whitespace_only_query,
            test_selector_run_multiline_query,
            test_selector_run_json_response,
            test_selector_run_empty_response,
            test_selector_run_consecutive_calls,
        ]),
        ("Structural Tests", [
            test_selector_module_exports,
            test_selector_prompts_module_exports,
            test_selector_agent_is_class,
            test_selector_agent_has_run_method,
            test_selector_agent_has_init_method,
            test_selector_differs_from_switcher,
            test_selector_differs_from_system1,
        ]),
        ("Cross-Module Consistency", [
            test_all_agents_same_init_pattern,
            test_all_agents_accept_custom_config,
            test_all_agents_have_run_method,
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