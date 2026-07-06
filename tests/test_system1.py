"""
Tests for the system1 module: System1Agent and PLAIN_SYSTEM_PROMPT.
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


# ═════════════════════════════ PLAIN_SYSTEM_PROMPT ══════════════════════════

def test_plain_prompt_is_string():
    """PLAIN_SYSTEM_PROMPT should be a non-empty string."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = isinstance(PLAIN_SYSTEM_PROMPT, str) and len(PLAIN_SYSTEM_PROMPT) > 10
    report("PLAIN_SYSTEM_PROMPT is non-empty string", ok, f"Length: {len(PLAIN_SYSTEM_PROMPT)}")


def test_plain_prompt_contains_step_by_step():
    """PLAIN_SYSTEM_PROMPT should instruct step-by-step reasoning."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = "step by step" in PLAIN_SYSTEM_PROMPT.lower() or "step-by-step" in PLAIN_SYSTEM_PROMPT.lower()
    report("PLAIN_SYSTEM_PROMPT has step-by-step instruction", ok)


def test_plain_prompt_contains_json_format():
    """PLAIN_SYSTEM_PROMPT should mention JSON format for output."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = "JSON" in PLAIN_SYSTEM_PROMPT
    report("PLAIN_SYSTEM_PROMPT mentions JSON format", ok)


def test_plain_prompt_contains_solve_instruction():
    """PLAIN_SYSTEM_PROMPT should instruct solving the problem."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = "Solve" in PLAIN_SYSTEM_PROMPT or "solve" in PLAIN_SYSTEM_PROMPT
    report("PLAIN_SYSTEM_PROMPT has solve instruction", ok)


def test_plain_prompt_contains_reasoning():
    """PLAIN_SYSTEM_PROMPT should mention reasoning."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = "reasoning" in PLAIN_SYSTEM_PROMPT.lower() or "reason" in PLAIN_SYSTEM_PROMPT.lower()
    report("PLAIN_SYSTEM_PROMPT mentions reasoning", ok)


def test_plain_prompt_contains_final_answer():
    """PLAIN_SYSTEM_PROMPT should mention final answer."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = "final answer" in PLAIN_SYSTEM_PROMPT.lower()
    report("PLAIN_SYSTEM_PROMPT mentions final answer", ok)


def test_plain_prompt_contains_must():
    """PLAIN_SYSTEM_PROMPT should use MUST for emphasis on output format."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = "MUST" in PLAIN_SYSTEM_PROMPT
    report("PLAIN_SYSTEM_PROMPT uses MUST for emphasis", ok)


# ═════════════════════════════ System1Agent INIT ════════════════════════════

def test_system1_init_default():
    """System1Agent with no config should use defaults."""
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig
    agent = System1Agent()
    ok = isinstance(agent.config, MCPAgentConfig) and agent.config.solver == "z3"
    report("System1Agent() default config", ok)


def test_system1_init_custom_config():
    """System1Agent with custom config should use it."""
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, solver="clingo")
    agent = System1Agent(config=cfg)
    ok = agent.config.provider == LLMProvider.NVIDIA and agent.config.solver == "clingo"
    report("System1Agent(custom config) works", ok)


def test_system1_has_llm_manager():
    """System1Agent should have an LLMManager instance."""
    from system1.system1_core import System1Agent
    from agent.llm_client import LLMManager
    agent = System1Agent()
    ok = isinstance(agent.llm_manager, LLMManager)
    report("System1Agent has LLMManager", ok)


def test_system1_messages_initially_empty():
    """System1Agent.messages should be initially empty."""
    from system1.system1_core import System1Agent
    agent = System1Agent()
    ok = agent.messages == []
    report("System1Agent.messages initially empty", ok)


def test_system1_init_none_config():
    """System1Agent with explicit None config should use defaults."""
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig
    agent = System1Agent(config=None)
    ok = isinstance(agent.config, MCPAgentConfig)
    report("System1Agent(config=None) uses defaults", ok)


def test_system1_init_google_config():
    """System1Agent with Google config should work."""
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.GOOGLE, model_name="gemini-3.1-flash-lite")
    agent = System1Agent(config=cfg)
    ok = agent.config.provider == LLMProvider.GOOGLE
    report("System1Agent(Google config) works", ok)


def test_system1_init_openrouter_config():
    """System1Agent with OpenRouter config should work."""
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.OPENROUTER)
    agent = System1Agent(config=cfg)
    ok = agent.config.provider == LLMProvider.OPENROUTER
    report("System1Agent(OpenRouter config) works", ok)


def test_system1_init_mistral_config():
    """System1Agent with Mistral config should work."""
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.MISTRAL)
    agent = System1Agent(config=cfg)
    ok = agent.config.provider == LLMProvider.MISTRAL
    report("System1Agent(Mistral config) works", ok)


# ═════════════════════════════ System1Agent.run() ═══════════════════════════

def test_system1_run_returns_tuple():
    """System1Agent.run() should return a tuple of (str, bool)."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("The answer is True.", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("test query"))
        ok = isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], str) and isinstance(result[1], bool)
        report("System1Agent.run() returns (str, bool)", ok, f"Got: {type(result)}")


def test_system1_run_passes_header_title():
    """System1Agent.run() should pass 'SYSTEM 1 PURE REASONING AGENT' as header."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    captured_kwargs = {}

    async def mock_stream(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        ok = captured_kwargs.get("header_title") == "SYSTEM 1 PURE REASONING AGENT"
        report("System1Agent passes correct header_title", ok)


def test_system1_run_passes_user_query():
    """System1Agent.run() should pass user_query to run_single_pass_stream."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    captured_kwargs = {}

    async def mock_stream(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("my test question"))
        ok = captured_kwargs.get("user_query") == "my test question"
        report("System1Agent passes user_query correctly", ok)


def test_system1_run_uses_plain_system_prompt():
    """System1Agent.run() should use PLAIN_SYSTEM_PROMPT as system message."""
    import asyncio
    from system1.system1_core import System1Agent
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    from agent.config import MCPAgentConfig
    from langchain_core.messages import SystemMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    captured_messages = []

    async def mock_stream(*args, **kwargs):
        captured_messages.extend(args[1] if len(args) > 1 else kwargs.get("messages", []))
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        system_msgs = [m for m in captured_messages if isinstance(m, SystemMessage)]
        ok = len(system_msgs) == 1 and system_msgs[0].content == PLAIN_SYSTEM_PROMPT
        report("System1Agent uses PLAIN_SYSTEM_PROMPT as system message", ok)


def test_system1_run_stores_messages():
    """System1Agent.run() should store messages on self.messages."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        ok = len(agent.messages) == 2  # SystemMessage + HumanMessage
        report("System1Agent stores 2 messages after run", ok)


def test_system1_run_messages_contain_query():
    """System1Agent.run() messages should contain the user query in HumanMessage."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("What is 2+2?"))
        human_msgs = [m for m in agent.messages if isinstance(m, HumanMessage)]
        ok = len(human_msgs) == 1 and human_msgs[0].content == "What is 2+2?"
        report("System1Agent messages contain user query", ok)


def test_system1_run_returns_truncated_flag():
    """System1Agent.run() should propagate was_truncated from stream."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("truncated result", True)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        _, was_truncated = asyncio.run(agent.run("test query"))
        ok = was_truncated is True
        report("System1Agent propagates was_truncated=True", ok)


def test_system1_run_returns_not_truncated():
    """System1Agent.run() should return False when not truncated."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("full result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        _, was_truncated = asyncio.run(agent.run("test query"))
        ok = was_truncated is False
        report("System1Agent returns was_truncated=False", ok)


def test_system1_run_passes_llm_manager():
    """System1Agent.run() should pass its own llm_manager."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    captured_manager = None

    async def mock_stream(*args, **kwargs):
        nonlocal captured_manager
        captured_manager = kwargs.get("llm_manager")
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test"))
        ok = captured_manager is agent.llm_manager
        report("System1Agent passes its own llm_manager", ok)


def test_system1_run_passes_messages_list():
    """System1Agent.run() should pass messages as a list."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    captured_messages = None

    async def mock_stream(*args, **kwargs):
        nonlocal captured_messages
        captured_messages = kwargs.get("messages")
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test"))
        ok = isinstance(captured_messages, list) and len(captured_messages) == 2
        report("System1Agent passes messages as list of 2", ok)


def test_system1_run_overwrites_messages():
    """System1Agent.run() should overwrite messages on each call."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("first query"))
        first_len = len(agent.messages)
        asyncio.run(agent.run("second query"))
        second_len = len(agent.messages)
        ok = first_len == 2 and second_len == 2
        report("System1Agent overwrites messages on each run", ok)


# ═════════════════════════════ EDGE CASES ═══════════════════════════════════

def test_system1_run_empty_query():
    """System1Agent.run() with empty query should still work."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(""))
        ok = result == "result"
        report("System1Agent empty query -> still works", ok)


def test_system1_run_long_query():
    """System1Agent.run() with very long query should still work."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    long_query = "A" * 10000

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(long_query))
        ok = result == "result"
        report("System1Agent long query (10k chars) -> still works", ok)


def test_system1_run_special_characters():
    """System1Agent.run() with special characters should still work."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    query = "∀x∃y: P(x,y) ∧ ¬Q(x) → R(y) | S(x,y)"

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(query))
        ok = result == "result"
        report("System1Agent special characters query -> still works", ok)


def test_system1_run_unicode_query():
    """System1Agent.run() with unicode query should still work."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    query = "如果所有猫都是动物，那么所有猫都是哺乳动物吗？"

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(query))
        ok = result == "result"
        report("System1Agent unicode query -> still works", ok)


def test_system1_run_whitespace_only_query():
    """System1Agent.run() with whitespace-only query should still work."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run("   \n\n   "))
        ok = result == "result"
        report("System1Agent whitespace-only query -> still works", ok)


def test_system1_run_multiline_query():
    """System1Agent.run() with multiline query should still work."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    query = "Premise 1: All cats are animals.\nPremise 2: Tom is a cat.\nConclusion: Tom is an animal."

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(query))
        ok = result == "result"
        report("System1Agent multiline query -> still works", ok)


def test_system1_run_json_answer():
    """System1Agent.run() should handle JSON answer response."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    json_answer = '{"answer": "True", "confidence": "high"}'

    async def mock_stream(*args, **kwargs):
        return (json_answer, False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run("test"))
        ok = result == json_answer
        report("System1Agent handles JSON answer", ok)


def test_system1_run_empty_response():
    """System1Agent.run() should handle empty response from stream."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run("test"))
        ok = result == ""
        report("System1Agent handles empty response", ok)


def test_system1_run_thinking_response():
    """System1Agent.run() should handle response with thinking tags."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    response = "<think>\nLet me think about this...\n</think>\nThe answer is True."

    async def mock_stream(*args, **kwargs):
        return (response, False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run("test"))
        ok = result == response
        report("System1Agent handles thinking response", ok)


def test_system1_run_long_response():
    """System1Agent.run() should handle very long response."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    long_response = "Step 1: ... " * 1000

    async def mock_stream(*args, **kwargs):
        return (long_response, False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run("test"))
        ok = result == long_response
        report("System1Agent handles long response", ok)


def test_system1_run_consecutive_calls():
    """System1Agent.run() should work correctly on consecutive calls."""
    import asyncio
    from system1.system1_core import System1Agent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = System1Agent(config=cfg)
    call_count = 0

    async def mock_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return (f"result_{call_count}", False)

    with patch("system1.system1_core.run_single_pass_stream", side_effect=mock_stream):
        r1, _ = asyncio.run(agent.run("query 1"))
        r2, _ = asyncio.run(agent.run("query 2"))
        r3, _ = asyncio.run(agent.run("query 3"))
        ok = r1 == "result_1" and r2 == "result_2" and r3 == "result_3" and call_count == 3
        report("System1Agent handles 3 consecutive calls", ok)


# ═════════════════════════════ STRUCTURAL TESTS ═════════════════════════════

def test_system1_module_exports():
    """system1 module should export System1Agent."""
    from system1.system1_core import System1Agent
    ok = callable(System1Agent)
    report("system1.system1_core exports System1Agent", ok)


def test_system1_prompts_module_exports():
    """system1.prompts should export PLAIN_SYSTEM_PROMPT."""
    from system1.prompts import PLAIN_SYSTEM_PROMPT
    ok = isinstance(PLAIN_SYSTEM_PROMPT, str)
    report("system1.prompts exports PLAIN_SYSTEM_PROMPT", ok)


def test_system1_agent_is_class():
    """System1Agent should be a class (not a function)."""
    from system1.system1_core import System1Agent
    ok = isinstance(System1Agent, type)
    report("System1Agent is a class", ok)


def test_system1_agent_has_run_method():
    """System1Agent should have a run method."""
    from system1.system1_core import System1Agent
    agent = System1Agent()
    ok = hasattr(agent, "run") and callable(agent.run)
    report("System1Agent has callable run method", ok)


def test_system1_agent_has_init_method():
    """System1Agent should have an __init__ method."""
    from system1.system1_core import System1Agent
    ok = hasattr(System1Agent, "__init__")
    report("System1Agent has __init__ method", ok)


# ═════════════════════════════ MAIN ════════════════════════════════════════

def main():
    print(f"\n{BOLD}=== System1 Module - Comprehensive Tests ==={RESET}\n")

    tests = [
        ("PLAIN_SYSTEM_PROMPT Content", [
            test_plain_prompt_is_string,
            test_plain_prompt_contains_step_by_step,
            test_plain_prompt_contains_json_format,
            test_plain_prompt_contains_solve_instruction,
            test_plain_prompt_contains_reasoning,
            test_plain_prompt_contains_final_answer,
            test_plain_prompt_contains_must,
        ]),
        ("System1Agent Initialization", [
            test_system1_init_default,
            test_system1_init_custom_config,
            test_system1_init_none_config,
            test_system1_init_google_config,
            test_system1_init_openrouter_config,
            test_system1_init_mistral_config,
            test_system1_has_llm_manager,
            test_system1_messages_initially_empty,
        ]),
        ("System1Agent.run() Behavior", [
            test_system1_run_returns_tuple,
            test_system1_run_passes_header_title,
            test_system1_run_passes_user_query,
            test_system1_run_uses_plain_system_prompt,
            test_system1_run_stores_messages,
            test_system1_run_messages_contain_query,
            test_system1_run_returns_truncated_flag,
            test_system1_run_returns_not_truncated,
            test_system1_run_passes_llm_manager,
            test_system1_run_passes_messages_list,
            test_system1_run_overwrites_messages,
        ]),
        ("Edge Cases", [
            test_system1_run_empty_query,
            test_system1_run_long_query,
            test_system1_run_special_characters,
            test_system1_run_unicode_query,
            test_system1_run_whitespace_only_query,
            test_system1_run_multiline_query,
            test_system1_run_json_answer,
            test_system1_run_empty_response,
            test_system1_run_thinking_response,
            test_system1_run_long_response,
            test_system1_run_consecutive_calls,
        ]),
        ("Structural Tests", [
            test_system1_module_exports,
            test_system1_prompts_module_exports,
            test_system1_agent_is_class,
            test_system1_agent_has_run_method,
            test_system1_agent_has_init_method,
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