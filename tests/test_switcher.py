"""
Tests for the switcher module: SwitcherAgent and META_SYSTEM_PROMPT.
Tests pure logic without requiring actual LLM connections.
"""
import os
import sys
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


# ═════════════════════════════ META_SYSTEM_PROMPT ═══════════════════════════

def test_meta_prompt_is_string():
    """META_SYSTEM_PROMPT should be a non-empty string."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = isinstance(META_SYSTEM_PROMPT, str) and len(META_SYSTEM_PROMPT) > 100
    report("META_SYSTEM_PROMPT is non-empty string", ok, f"Length: {len(META_SYSTEM_PROMPT)}")


def test_meta_prompt_contains_confidence_rubric():
    """META_SYSTEM_PROMPT should contain the confidence rubric."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Confidence Rubric" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has Confidence Rubric", ok)


def test_meta_prompt_contains_confidence_format():
    """META_SYSTEM_PROMPT should specify the Confidence: XX% output format."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Confidence:" in META_SYSTEM_PROMPT and "%" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has Confidence: XX% format", ok)


def test_meta_prompt_contains_five_stages():
    """META_SYSTEM_PROMPT should reference all 5 metacognitive stages."""
    from switcher.prompts import META_SYSTEM_PROMPT
    stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5"]
    ok = all(s in META_SYSTEM_PROMPT for s in stages)
    report("META_SYSTEM_PROMPT has all 5 metacognitive stages", ok)


def test_meta_prompt_contains_anti_anchoring():
    """META_SYSTEM_PROMPT should contain anti-anchoring protocol."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Anchoring" in META_SYSTEM_PROMPT and "Anti-Anchoring" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has anti-anchoring protocol", ok)


def test_meta_prompt_contains_anti_confirmation():
    """META_SYSTEM_PROMPT should contain anti-confirmation bias."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Confirmation" in META_SYSTEM_PROMPT and "Anti-Confirmation" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has anti-confirmation bias", ok)


def test_meta_prompt_contains_anti_overconfidence():
    """META_SYSTEM_PROMPT should contain anti-overconfidence bias."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Overconfidence" in META_SYSTEM_PROMPT and "Anti-Overconfidence" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has anti-overconfidence bias", ok)


def test_meta_prompt_contains_step_type_classification():
    """META_SYSTEM_PROMPT should contain the 4-type step classification."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Type A" in META_SYSTEM_PROMPT and "Type B" in META_SYSTEM_PROMPT and "Type C" in META_SYSTEM_PROMPT and "Type D" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has step types A/B/C/D", ok)


def test_meta_prompt_contains_stop_rules():
    """META_SYSTEM_PROMPT should contain stop rules."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "STOP" in META_SYSTEM_PROMPT and "STOP RULES" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has stop rules", ok)


def test_meta_prompt_contains_zero_tolerance():
    """META_SYSTEM_PROMPT should contain zero tolerance for hallucination."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Zero Tolerance" in META_SYSTEM_PROMPT and "Hallucination" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has zero tolerance for hallucination", ok)


def test_meta_prompt_contains_adversarial():
    """META_SYSTEM_PROMPT should contain adversarial mindset."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Adversarial" in META_SYSTEM_PROMPT and "skepticism" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has adversarial mindset", ok)


def test_meta_prompt_contains_principle_of_explosion():
    """META_SYSTEM_PROMPT should ban the Principle of Explosion."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Principle of Explosion" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT bans Principle of Explosion", ok)


def test_meta_prompt_contains_red_teaming():
    """META_SYSTEM_PROMPT should require red teaming / self-doubt check."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "RED TEAMING" in META_SYSTEM_PROMPT or "red teaming" in META_SYSTEM_PROMPT.lower()
    report("META_SYSTEM_PROMPT has red teaming check", ok)


def test_meta_prompt_contains_confidence_definition():
    """META_SYSTEM_PROMPT should define confidence as S1 correctness belief."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "SYSTEM 1 ANSWER IS CORRECT" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT defines confidence as S1 correctness", ok)


def test_meta_prompt_contains_low_confidence_on_disagree():
    """META_SYSTEM_PROMPT should mandate low confidence when Stage 2 disagrees."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "DISAGREES" in META_SYSTEM_PROMPT and "0%" in META_SYSTEM_PROMPT and "40%" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT mandates low confidence on disagreement", ok)


def test_meta_prompt_contains_satisficing_check():
    """META_SYSTEM_PROMPT should contain satisficing and optimality checks."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Satisficing" in META_SYSTEM_PROMPT and "30%" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has satisficing check with 30% penalty", ok)


def test_meta_prompt_contains_algorithmic_laziness():
    """META_SYSTEM_PROMPT should acknowledge algorithmic laziness for large checks."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Algorithmic Laziness" in META_SYSTEM_PROMPT or "Partial Verification" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has algorithmic laziness guard", ok)


def test_meta_prompt_contains_charitable_idioms():
    """META_SYSTEM_PROMPT should instruct charitable interpretation of idioms."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Charitable" in META_SYSTEM_PROMPT and "idiom" in META_SYSTEM_PROMPT.lower()
    report("META_SYSTEM_PROMPT has charitable idiom interpretation", ok)


def test_meta_prompt_contains_domain_mapping():
    """META_SYSTEM_PROMPT should require explicit domain mapping."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Domain Mapping" in META_SYSTEM_PROMPT or "Explicit Domain" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT has explicit domain mapping", ok)


def test_meta_prompt_confidence_range_0_to_100():
    """META_SYSTEM_PROMPT should define confidence from 0% to 100%."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "0%" in META_SYSTEM_PROMPT and "100%" in META_SYSTEM_PROMPT
    report("META_SYSTEM_PROMPT defines 0%-100% range", ok)


def test_meta_prompt_contains_metacognitive_humility():
    """META_SYSTEM_PROMPT should mention metacognitive humility."""
    from switcher.prompts import META_SYSTEM_PROMPT
    ok = "Metacognitive Humility" in META_SYSTEM_PROMPT or "metacognitive" in META_SYSTEM_PROMPT.lower()
    report("META_SYSTEM_PROMPT has metacognitive humility", ok)


# ═════════════════════════════ SwitcherAgent INIT ═══════════════════════════

def test_switcher_init_default():
    """SwitcherAgent with no config should use defaults."""
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig
    agent = SwitcherAgent()
    ok = isinstance(agent.config, MCPAgentConfig) and agent.config.solver == "z3"
    report("SwitcherAgent() default config", ok)


def test_switcher_init_custom_config():
    """SwitcherAgent with custom config should use it."""
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig, LLMProvider
    cfg = MCPAgentConfig(provider=LLMProvider.NVIDIA, solver="clingo")
    agent = SwitcherAgent(config=cfg)
    ok = agent.config.provider == LLMProvider.NVIDIA and agent.config.solver == "clingo"
    report("SwitcherAgent(custom config) works", ok)


def test_switcher_has_llm_manager():
    """SwitcherAgent should have an LLMManager instance."""
    from switcher.switcher_core import SwitcherAgent
    from agent.llm_client import LLMManager
    agent = SwitcherAgent()
    ok = isinstance(agent.llm_manager, LLMManager)
    report("SwitcherAgent has LLMManager", ok)


def test_switcher_messages_initially_empty():
    """SwitcherAgent.messages should be initially empty."""
    from switcher.switcher_core import SwitcherAgent
    agent = SwitcherAgent()
    ok = agent.messages == []
    report("SwitcherAgent.messages initially empty", ok)


def test_switcher_run_returns_tuple():
    """SwitcherAgent.run() should return a tuple of (str, bool)."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    # Mock run_single_pass_stream to avoid actual LLM call
    async def mock_stream(*args, **kwargs):
        return ("Confidence: 85%", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result = asyncio.run(agent.run("test query"))
        ok = isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], str) and isinstance(result[1], bool)
        report("SwitcherAgent.run() returns (str, bool)", ok, f"Got: {type(result)}")


def test_switcher_run_passes_header_title():
    """SwitcherAgent.run() should pass 'SWITCHER META EVALUATOR AGENT' as header."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    captured_kwargs = {}

    async def mock_stream(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        ok = captured_kwargs.get("header_title") == "SWITCHER META EVALUATOR AGENT"
        report("SwitcherAgent passes correct header_title", ok)


def test_switcher_run_passes_user_query():
    """SwitcherAgent.run() should pass user_query to run_single_pass_stream."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    captured_kwargs = {}

    async def mock_stream(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("my test question"))
        ok = captured_kwargs.get("user_query") == "my test question"
        report("SwitcherAgent passes user_query correctly", ok)


def test_switcher_run_uses_meta_system_prompt():
    """SwitcherAgent.run() should use META_SYSTEM_PROMPT as system message."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from switcher.prompts import META_SYSTEM_PROMPT
    from agent.config import MCPAgentConfig
    from langchain_core.messages import SystemMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    captured_messages = []

    async def mock_stream(*args, **kwargs):
        captured_messages.extend(args[1] if len(args) > 1 else kwargs.get("messages", []))
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        system_msgs = [m for m in captured_messages if isinstance(m, SystemMessage)]
        ok = len(system_msgs) == 1 and system_msgs[0].content == META_SYSTEM_PROMPT
        report("SwitcherAgent uses META_SYSTEM_PROMPT as system message", ok)


def test_switcher_run_stores_messages():
    """SwitcherAgent.run() should store messages on self.messages."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test query"))
        ok = len(agent.messages) == 2  # SystemMessage + HumanMessage
        report("SwitcherAgent stores 2 messages after run", ok)


def test_switcher_run_messages_contain_query():
    """SwitcherAgent.run() messages should contain the user query in HumanMessage."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig
    from langchain_core.messages import HumanMessage

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("What is 2+2?"))
        human_msgs = [m for m in agent.messages if isinstance(m, HumanMessage)]
        ok = len(human_msgs) == 1 and human_msgs[0].content == "What is 2+2?"
        report("SwitcherAgent messages contain user query", ok)


def test_switcher_run_returns_truncated_flag():
    """SwitcherAgent.run() should propagate was_truncated from stream."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("truncated result", True)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        _, was_truncated = asyncio.run(agent.run("test query"))
        ok = was_truncated is True
        report("SwitcherAgent propagates was_truncated=True", ok)


def test_switcher_run_returns_not_truncated():
    """SwitcherAgent.run() should return False when not truncated."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("full result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        _, was_truncated = asyncio.run(agent.run("test query"))
        ok = was_truncated is False
        report("SwitcherAgent returns was_truncated=False", ok)


# ═════════════════════════════ EDGE CASES ═══════════════════════════════════

def test_switcher_run_empty_query():
    """SwitcherAgent.run() with empty query should still work."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(""))
        ok = result == "result"
        report("SwitcherAgent empty query -> still works", ok)


def test_switcher_run_long_query():
    """SwitcherAgent.run() with very long query should still work."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    long_query = "A" * 10000

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(long_query))
        ok = result == "result"
        report("SwitcherAgent long query (10k chars) -> still works", ok)


def test_switcher_run_special_characters():
    """SwitcherAgent.run() with special characters should still work."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    query = "∀x∃y: P(x,y) ∧ ¬Q(x) → R(y) | S(x,y)"

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(query))
        ok = result == "result"
        report("SwitcherAgent special characters query -> still works", ok)


def test_switcher_run_unicode_query():
    """SwitcherAgent.run() with unicode query should still work."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    query = "如果所有猫都是动物，那么所有猫都是哺乳动物吗？"

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(query))
        ok = result == "result"
        report("SwitcherAgent unicode query -> still works", ok)


def test_switcher_run_whitespace_only_query():
    """SwitcherAgent.run() with whitespace-only query should still work."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run("   \n\n   "))
        ok = result == "result"
        report("SwitcherAgent whitespace-only query -> still works", ok)


def test_switcher_run_multiline_query():
    """SwitcherAgent.run() with multiline query should still work."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    query = "Premise 1: All cats are animals.\nPremise 2: Tom is a cat.\nConclusion: Tom is an animal."

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        result, _ = asyncio.run(agent.run(query))
        ok = result == "result"
        report("SwitcherAgent multiline query -> still works", ok)


def test_switcher_run_overwrites_messages():
    """SwitcherAgent.run() should overwrite messages on each call."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)

    async def mock_stream(*args, **kwargs):
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("first query"))
        first_len = len(agent.messages)
        asyncio.run(agent.run("second query"))
        second_len = len(agent.messages)
        ok = first_len == 2 and second_len == 2
        report("SwitcherAgent overwrites messages on each run", ok)


def test_switcher_run_passes_llm_manager():
    """SwitcherAgent.run() should pass its own llm_manager."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    captured_manager = None

    async def mock_stream(*args, **kwargs):
        nonlocal captured_manager
        captured_manager = kwargs.get("llm_manager")
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test"))
        ok = captured_manager is agent.llm_manager
        report("SwitcherAgent passes its own llm_manager", ok)


def test_switcher_run_passes_messages_list():
    """SwitcherAgent.run() should pass messages as a list."""
    import asyncio
    from switcher.switcher_core import SwitcherAgent
    from agent.config import MCPAgentConfig

    cfg = MCPAgentConfig(openai_api_key="test-key")
    agent = SwitcherAgent(config=cfg)
    captured_messages = None

    async def mock_stream(*args, **kwargs):
        nonlocal captured_messages
        captured_messages = kwargs.get("messages")
        return ("result", False)

    with patch("switcher.switcher_core.run_single_pass_stream", side_effect=mock_stream):
        asyncio.run(agent.run("test"))
        ok = isinstance(captured_messages, list) and len(captured_messages) == 2
        report("SwitcherAgent passes messages as list of 2", ok)


# ═════════════════════════════ MAIN ════════════════════════════════════════

def main():
    print(f"\n{BOLD}=== Switcher Module - Comprehensive Tests ==={RESET}\n")

    tests = [
        ("META_SYSTEM_PROMPT Content", [
            test_meta_prompt_is_string,
            test_meta_prompt_contains_confidence_rubric,
            test_meta_prompt_contains_confidence_format,
            test_meta_prompt_contains_five_stages,
            test_meta_prompt_contains_anti_anchoring,
            test_meta_prompt_contains_anti_confirmation,
            test_meta_prompt_contains_anti_overconfidence,
            test_meta_prompt_contains_step_type_classification,
            test_meta_prompt_contains_stop_rules,
            test_meta_prompt_contains_zero_tolerance,
            test_meta_prompt_contains_adversarial,
            test_meta_prompt_contains_principle_of_explosion,
            test_meta_prompt_contains_red_teaming,
            test_meta_prompt_contains_confidence_definition,
            test_meta_prompt_contains_low_confidence_on_disagree,
            test_meta_prompt_contains_satisficing_check,
            test_meta_prompt_contains_algorithmic_laziness,
            test_meta_prompt_contains_charitable_idioms,
            test_meta_prompt_contains_domain_mapping,
            test_meta_prompt_confidence_range_0_to_100,
            test_meta_prompt_contains_metacognitive_humility,
        ]),
        ("SwitcherAgent Initialization", [
            test_switcher_init_default,
            test_switcher_init_custom_config,
            test_switcher_has_llm_manager,
            test_switcher_messages_initially_empty,
        ]),
        ("SwitcherAgent.run() Behavior", [
            test_switcher_run_returns_tuple,
            test_switcher_run_passes_header_title,
            test_switcher_run_passes_user_query,
            test_switcher_run_uses_meta_system_prompt,
            test_switcher_run_stores_messages,
            test_switcher_run_messages_contain_query,
            test_switcher_run_returns_truncated_flag,
            test_switcher_run_returns_not_truncated,
            test_switcher_run_passes_llm_manager,
            test_switcher_run_passes_messages_list,
            test_switcher_run_overwrites_messages,
        ]),
        ("Edge Cases", [
            test_switcher_run_empty_query,
            test_switcher_run_long_query,
            test_switcher_run_special_characters,
            test_switcher_run_unicode_query,
            test_switcher_run_whitespace_only_query,
            test_switcher_run_multiline_query,
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