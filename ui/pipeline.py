"""
Async pipeline functions for running agents.
"""
import json
import re
from typing import Optional, Tuple, List

from system1.system1_core import System1Agent
from selector.selector_core import SelectorAgent
from switcher.switcher_core import SwitcherAgent
from agent.mcp_core import MCPAgent
from ui.prompts import EVALUATOR_USER_PROMPT, _THINKING_SECTION_TEMPLATE


async def run_system1(cfg, query: str) -> Tuple[str, bool]:
    """Run System 1. Returns (answer, was_truncated)."""
    return await System1Agent(cfg).run(user_query=query)


async def run_selector(cfg, query: str) -> str:
    return await SelectorAgent(cfg).run(user_query=query)


async def run_switcher(cfg, query: str, s1_answer: str, thinking: str) -> Tuple[str, bool]:
    """Run Switcher. Returns (answer, was_truncated)."""
    ts = _THINKING_SECTION_TEMPLATE.format(thinking=thinking) if thinking else ""
    eq = EVALUATOR_USER_PROMPT.format(
        puzzle_text=query, thinking_section=ts, system1_answer=s1_answer
    )
    return await SwitcherAgent(cfg).run(user_query=eq)


async def run_mcp(cfg, query: str, translation_query: Optional[str] = None) -> str:
    return await MCPAgent(cfg).run(user_query=query, translation_query=translation_query)


def extract_confidence(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"Confidence:\s*(\d+)%", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def extract_solver_ranking(text: str) -> Optional[List[str]]:
    if not text:
        return None
    for block in re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL):
        try:
            d = json.loads(block)
            if "solver_ranking" in d:
                return [s.lower().strip() for s in d["solver_ranking"]]
        except json.JSONDecodeError:
            continue
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            if isinstance(obj, dict) and "solver_ranking" in obj:
                return [s.lower().strip() for s in obj["solver_ranking"]]
        except json.JSONDecodeError:
            continue
    return None