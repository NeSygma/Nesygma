import asyncio
import json
import logging
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from agent.llm_client import LLMManager
from agent.translator.models import PhaseUsage, TranslatorOutcome
from agent.translator.utils import (
    _chunk_content_to_text,
    _extract_reasoning_text,
    _extract_solver_payload,
    _is_terminal_solver_success,
    _is_rate_limit_error,
)

logger = logging.getLogger(__name__)

def get_request_kwargs(provider: str) -> dict[str, Any]:
    request_kwargs: dict[str, Any] = {}
    if (provider or "").lower().strip() == "google":
        request_kwargs["automatic_function_calling"] = {"disable": True}
    return request_kwargs

async def stream_once(
    llm: Any,
    messages: list,
    request_kwargs: dict[str, Any],
    max_output_tokens: int = 10000,
) -> tuple[str, Any, PhaseUsage]:
    full_content = ""
    aggregated_chunk = None
    reasoning_active = False
    raw_usage_metadata = None

    async for chunk in llm.astream(messages, **request_kwargs):
        if aggregated_chunk is None:
            aggregated_chunk = chunk
        else:
            aggregated_chunk += chunk

        # Capture usage metadata from raw chunk — Google Gemini sends usage
        # across multiple chunks (input in one, output in another, zeros in
        # the final). Merge by keeping the max of each field.
        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
            new_meta = chunk.usage_metadata
            if raw_usage_metadata is None:
                raw_usage_metadata = dict(new_meta)
            else:
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    old_val = int(raw_usage_metadata.get(key, 0) or 0)
                    new_val = int(new_meta.get(key, 0) or 0)
                    if new_val > old_val:
                        raw_usage_metadata[key] = new_val

        reasoning_chunk = _extract_reasoning_text(chunk)
        if reasoning_chunk:
            if not reasoning_active:
                print("\n<THINKING>")
                reasoning_active = True
            print(reasoning_chunk, end="", flush=True)

        chunk_text = _chunk_content_to_text(getattr(chunk, "content", None))
        if chunk_text:
            if reasoning_active:
                print("\n</THINKING>\n")
                reasoning_active = False
            print(chunk_text, end="", flush=True)
            full_content += chunk_text

    if reasoning_active:
        print("\n</THINKING>\n")

    usage = PhaseUsage()
    if raw_usage_metadata:
        usage.input_tokens = int(raw_usage_metadata.get("input_tokens", 0) or 0)
        usage.output_tokens = int(raw_usage_metadata.get("output_tokens", 0) or 0)
        # Always compute total from input+output to avoid unreliable provider totals
        usage.total_tokens = usage.input_tokens + usage.output_tokens
    elif aggregated_chunk and hasattr(aggregated_chunk, "usage_metadata") and aggregated_chunk.usage_metadata:
        meta = aggregated_chunk.usage_metadata
        usage.input_tokens = int(meta.get("input_tokens", 0) or 0)
        usage.output_tokens = int(meta.get("output_tokens", 0) or 0)
        raw_total = int(meta.get("total_tokens", 0) or 0)
        usage.total_tokens = raw_total if raw_total > 0 else (usage.input_tokens + usage.output_tokens)

    return full_content, aggregated_chunk, usage

async def run_translator_phase(
    *,
    llm_manager: LLMManager,
    provider: str,
    solver: str,
    tools: list,
    system_prompt: str,
    user_query: str,
    max_iterations: int,
    prune_history: bool,
    tool_timeout_seconds: int,
    benchmark: Optional[str] = None,
) -> TranslatorOutcome:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query),
    ]

    usage = PhaseUsage()

    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---\n")

        if prune_history and iteration > 0 and len(messages) > 2:
            latest_ai_idx = -1
            for i in range(len(messages) - 1, 1, -1):
                if isinstance(messages[i], AIMessage):
                    latest_ai_idx = i
                    break
            if latest_ai_idx != -1:
                messages = messages[:2] + messages[latest_ai_idx:]

        current_llm = llm_manager.get_llm()
        llm_with_tools = current_llm.bind_tools(tools, tool_choice="auto") if tools else current_llm
        request_kwargs = get_request_kwargs(provider)

        full_content = ""
        aggregated_chunk = None
        last_error: Optional[Exception] = None
        for attempt in range(1, 5):
            try:
                full_content, aggregated_chunk, iter_usage = await stream_once(
                    llm_with_tools,
                    messages,
                    request_kwargs,
                    max_output_tokens=llm_manager.config.max_output_tokens,
                )
                usage.input_tokens += iter_usage.input_tokens
                usage.output_tokens += iter_usage.output_tokens
                usage.total_tokens += iter_usage.total_tokens
                break
            except Exception as e:
                last_error = e
                err_str = str(e)
                # Check for rate limit (429), unavailable (503), or payment required (402)
                is_retryable = _is_rate_limit_error(err_str)
                if is_retryable and attempt < 4:
                    err_code = next((c for c in ["429", "503", "402"] if c in err_str), "retryable error")
                    print(f"\nAPI Error (Error: {err_code}). Waiting 30s... (retry {attempt}/3)")
                    await asyncio.sleep(30)
                    current_llm = llm_manager.get_llm()
                    llm_with_tools = current_llm.bind_tools(tools, tool_choice="auto") if tools else current_llm
                    continue
                raise

        if last_error and aggregated_chunk is None and not full_content:
            return TranslatorOutcome(
                success=False,
                iterations_used=iteration + 1,
                messages=messages,
                usage=usage,
                failure_reason=str(last_error),
            )

        print()
        if aggregated_chunk and hasattr(aggregated_chunk, "usage_metadata") and aggregated_chunk.usage_metadata:
            print(f"\n[TOKEN USAGE - Iteration {iteration + 1}]")
            print(f"  Input tokens:  {iter_usage.input_tokens:,}")
            print(f"  Output tokens: {iter_usage.output_tokens:,}")
            print(f"  Total tokens:  {iter_usage.total_tokens:,}")
        else:
            print(f"\n[TOKEN USAGE - Iteration {iteration + 1}] Not available")

        # ── Overthinking guard ──────────────────────────────────
        _OVERTHINK_THRESHOLD = 32_000
        if iter_usage.output_tokens >= _OVERTHINK_THRESHOLD:
            logger.warning(
                "LLM overthinking detected at iteration %d: "
                "%d output tokens (threshold %d). Aborting translation.",
                iteration + 1,
                iter_usage.output_tokens,
                _OVERTHINK_THRESHOLD,
            )
            print(
                f"\n[OVERTHINKING] Output tokens ({iter_usage.output_tokens:,}) "
                f"exceeded threshold ({_OVERTHINK_THRESHOLD:,}). "
                f"LLM failed Translation because overthinking. "
                f"Stopping all iterations."
            )
            return TranslatorOutcome(
                success=False,
                iterations_used=max_iterations,
                messages=messages,
                usage=usage,
                failure_reason=(
                    f"Translator failed to reach definitive solver result within {max_iterations} iterations. (Token limit hit)"
                ),
            )

        tool_calls = aggregated_chunk.tool_calls if aggregated_chunk and hasattr(aggregated_chunk, "tool_calls") else []
        if not tool_calls:
            messages.append(AIMessage(content=full_content))
            continue

        ai_content = full_content
        ai_additional_kwargs = {}
        ai_response_metadata = {}
        if aggregated_chunk is not None:
            chunk_content = getattr(aggregated_chunk, "content", None)
            if chunk_content is not None:
                ai_content = chunk_content
            ai_additional_kwargs = getattr(aggregated_chunk, "additional_kwargs", {}) or {}
            ai_response_metadata = getattr(aggregated_chunk, "response_metadata", {}) or {}

        messages.append(
            AIMessage(
                content=ai_content,
                tool_calls=tool_calls,
                additional_kwargs=ai_additional_kwargs,
                response_metadata=ai_response_metadata,
            )
        )

        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_id = tc.get("id") or f"call_{iteration}"

            print(f"\n[MCP TOOL] {tool_name}")
            print(f"  Args: {json.dumps(tool_args, indent=2)}")

            selected_tool = next((t for t in tools if t.name == tool_name), None)
            if selected_tool:
                try:
                    result = await asyncio.wait_for(
                        selected_tool.ainvoke(tool_args),
                        timeout=tool_timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    result = {
                        "status": "timeout",
                        "error": f"Tool {tool_name} exceeded client timeout ({tool_timeout_seconds}s)",
                    }
                except Exception as e:
                    result = f"Error executing tool {tool_name}: {str(e)}"
            else:
                result = f"Error: Tool {tool_name} not found."

            result_str = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
            print(f"\n[RESULT]\n{result_str}\n")

            messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))

            payload = _extract_solver_payload(result)
            if _is_terminal_solver_success(payload, solver, benchmark):
                return TranslatorOutcome(
                    success=True,
                    iterations_used=iteration + 1,
                    messages=messages,
                    usage=usage,
                    definitive_result_text=result_str,
                    solver_payload=payload,
                    last_tool_name=tool_name,
                    last_tool_args=tool_args if isinstance(tool_args, dict) else None,
                )

    return TranslatorOutcome(
        success=False,
        iterations_used=max_iterations,
        messages=messages,
        usage=usage,
        failure_reason=(
            f"Translator failed to reach definitive solver result within {max_iterations} iterations."
        ),
    )