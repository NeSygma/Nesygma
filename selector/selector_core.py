import logging
from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import MCPAgentConfig
from agent.single_pass_runner import run_single_pass_stream
from selector.prompts import SELECTOR_SYSTEM_PROMPT, SELECTOR_USER_PROMPT
from agent.llm_client import LLMManager

logger = logging.getLogger(__name__)

class SelectorAgent:
    """
    Selector Reasoning Agent (LLM-as-a-Judge Evaluator).
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

    async def run(self, user_query: str) -> str:
        """Run the Selector agent (zero tools, single inference with SELECTOR_SYSTEM_PROMPT)."""
        self.messages = [
            SystemMessage(content=SELECTOR_SYSTEM_PROMPT),
            HumanMessage(content=SELECTOR_USER_PROMPT.format(user_query=user_query))
        ]
        content, _ = await run_single_pass_stream(
            llm_manager=self.llm_manager,
            messages=self.messages,
            header_title="SELECTOR META EVALUATOR AGENT",
            user_query=user_query,
        )
        return content
