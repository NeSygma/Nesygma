import logging
import textwrap
from typing import Optional
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.config import MCPAgentConfig
from agent.llm_client import LLMManager
from agent.phase_prompts import get_translator_prompt, get_answer_prompt
from agent.phase_answer import run_answer_phase
from agent.phase_translator import run_translator_phase, PhaseUsage

logger = logging.getLogger(__name__)

class MCPAgent:
    """
    LangGraph agent that consumes MCP tools directly.
    Supports both native tool calling and text-based tool call parsing.
    Supports multiple LLM providers (NVIDIA, OpenRouter) via config.
    """
    
    def __init__(self, config: Optional[MCPAgentConfig] = None):
        if config is None:
            self.config = MCPAgentConfig()
        else:
            self.config = config
            
        self.llm_manager = LLMManager(self.config)

    def _build_mcp_config(self) -> dict:
        """Build MCP client configuration from Pydantic models."""
        return {
            name: server.model_dump(exclude_none=True)
            for name, server in self.config.mcp_servers.items()
        }
    
    async def run(self, user_query: str, translation_query: Optional[str] = None) -> str:
        """Run a decoupled two-phase pipeline: translator (tools) then answer (no tools)."""
        print(f"\n{'='*60}")
        print(f" MCP {self.config.solver.upper()} AGENT - Symbolic Reasoning")
        print(f"{'='*60}")

        clean_query = " ".join(user_query.split())
        wrapped_query = textwrap.fill(clean_query, width=100)
        print(f"\nQuery: {wrapped_query}\n")

        mcp_config = self._build_mcp_config()
        logger.info(f"Connecting to MCP servers: {list(mcp_config.keys())}")
        client = MultiServerMCPClient(mcp_config)

        try:
            tools = await client.get_tools()
            logger.info(f"Loaded {len(tools)} tools from MCP servers")
            for tool in tools:
                desc = tool.description if tool.description else "No description"
                print(f"  - {tool.name}: {desc}")

            translator_prompt = get_translator_prompt(self.config.solver, self.config.benchmark)
            answer_prompt = get_answer_prompt(self.config.solver)

            translator_limit = min(self.config.max_iterations, self.config.translator_max_iterations)
            
            # Inject solver skeletons for benchmarks directly into the agent logic to avoid duplicate code
            final_translation_query = translation_query if translation_query else user_query
            if getattr(self.config, "benchmark", None) == "agieval_lsat":
                if self.config.solver == "z3":
                    final_translation_query += """

CRITICAL REQUIREMENT:
Your objective is to find the single correct answer among the choices (A, B, C, D, E).
You MUST use the exact skeleton below for evaluating the multiple choice options. Failure to use this EXACT logic string will result in your execution being marked as a FAILURE.

```python
from z3 import *
solver = Solver()
# ... add base constraints ...

found_options = []
for letter, constr in [("A", opt_a_constr), ("B", opt_b_constr), ...]:
    solver.push()
    solver.add(constr)
    if solver.check() == sat:
        found_options.append(letter)
    solver.pop()

if len(found_options) == 1:
    print("STATUS: sat")
    print(f"answer:{found_options[0]}")
elif len(found_options) > 1:
    print("STATUS: unsat")
    print(f"Refine: Multiple options found {found_options}")
else:
    print("STATUS: unsat")
    print("Refine: No options found")
```
"""
                elif self.config.solver == "clingo":
                    final_translation_query += """

CRITICAL REQUIREMENT:
Your objective is to find the single correct answer among the choices (A, B, C, D, E).
You MUST use the exact skeleton below for evaluating the multiple choice options. Failure to use this EXACT logic string will result in your execution being marked as a FAILURE.

```lp
% ... add base constraints and rules ...

% Map the correct answer to option/1 (MANDATORY)
option(a) :- ... % condition for A
option(b) :- ... % condition for B
option(c) :- ... % condition for C
option(d) :- ... % condition for D
option(e) :- ... % condition for E

#show option/1.
```
"""

            translator_outcome = await run_translator_phase(
                llm_manager=self.llm_manager,
                provider=self.config.provider.value,
                solver=self.config.solver,
                tools=tools,
                system_prompt=translator_prompt,
                user_query=final_translation_query,
                max_iterations=translator_limit,
                prune_history=self.config.prune_history,
                tool_timeout_seconds=self.config.tool_timeout_seconds,
                benchmark=self.config.benchmark,
            )

            usage = PhaseUsage(
                input_tokens=translator_outcome.usage.input_tokens,
                output_tokens=translator_outcome.usage.output_tokens,
                total_tokens=translator_outcome.usage.total_tokens,
            )

            if not translator_outcome.success:
                final_response = (
                    f"Translator failed after {translator_limit} iterations. "
                    f"{translator_outcome.failure_reason or 'No definitive solver result.'}"
                )
            elif getattr(self.config, "benchmark", None) == "FOLIO":
                # For FOLIO, solver output contains the final answer (True/False/Uncertain) directly.
                print("\n[NOTE] Skipping Answer Phase for FOLIO benchmark as solver returns verdict directly.")
                final_response = translator_outcome.definitive_result_text or ""
            elif getattr(self.config, "benchmark", None) == "agieval_lsat" and self.config.solver in ["z3", "clingo"]:
                print(f"\n[NOTE] Skipping Answer Phase for LSAT with {self.config.solver.upper()} as solver returns the option choice directly.")
                final_response = translator_outcome.definitive_result_text or ""
            else:
                answer_text, answer_usage = await run_answer_phase(
                    llm_manager=self.llm_manager,
                    provider=self.config.provider.value,
                    solver=self.config.solver,
                    answer_prompt=answer_prompt,
                    user_query=user_query,
                    translator_outcome=translator_outcome,
                )
                usage.input_tokens += answer_usage.input_tokens
                usage.output_tokens += answer_usage.output_tokens
                usage.total_tokens += answer_usage.total_tokens

                final_response = (
                    answer_text
                    or (translator_outcome.definitive_result_text or "")
                    or "Unable to produce final answer text from solver output."
                )

            print(f"\n{'='*60}")
            print("TOKEN USAGE SUMMARY")
            print(f"{'='*60}")
            print(f"  Total input tokens:  {usage.input_tokens:,}")
            print(f"  Total output tokens: {usage.output_tokens:,}")
            print(f"  Total tokens:        {usage.total_tokens:,}")

            print(f"\n{'='*60}")
            print("COMPLETE")
            print(f"{'='*60}")

            return final_response

        except Exception as e:
            logger.error(f"Agent error: {e}")
            print(f"\nERROR: {e}")
            raise
