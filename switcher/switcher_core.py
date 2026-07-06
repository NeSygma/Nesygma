import logging
from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import MCPAgentConfig
from agent.single_pass_runner import run_single_pass_stream
from switcher.prompts import META_SYSTEM_PROMPT
from agent.llm_client import LLMManager

logger = logging.getLogger(__name__)

class SwitcherAgent:
    """
    Switcher Reasoning Agent (LLM-as-a-Judge Evaluator).
    Uses the specified LLM (e.g. DeepSeek/Cerebras) for evaluating reasoning via the Meta Prompt.
    No MCP tools. Exactly 1 iteration.
    """
    
    def __init__(self, config: MCPAgentConfig = None):
        if config is None:
            self.config = MCPAgentConfig()
        else:
            self.config = config
            
        self.llm_manager = LLMManager(self.config)
        self.messages = []

    async def run(self, user_query: str) -> tuple[str, bool]:
        """Run the Switcher agent (zero tools, single inference with META_SYSTEM_PROMPT).
        
        Returns (answer, was_truncated).
        """
        self.messages = [
            SystemMessage(content=META_SYSTEM_PROMPT),
            HumanMessage(content=user_query)
        ]
        return await run_single_pass_stream(
            llm_manager=self.llm_manager,
            messages=self.messages,
            header_title="SWITCHER META EVALUATOR AGENT",
            user_query=user_query,
        )
