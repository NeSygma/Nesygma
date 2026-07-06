import asyncio
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm_client import LLMManager
from agent.phase_translator import PhaseUsage, TranslatorOutcome, get_request_kwargs, stream_once


async def run_answer_phase(
    *,
    llm_manager: LLMManager,
    provider: str,
    solver: str,
    answer_prompt: str,
    user_query: str,
    translator_outcome: TranslatorOutcome,
) -> tuple[str, PhaseUsage]:
    usage = PhaseUsage()
    request_kwargs = get_request_kwargs(provider)

    payload_str = translator_outcome.definitive_result_text or ""

    messages = [
        SystemMessage(content=answer_prompt),
        HumanMessage(
            content=(
                "Original problem:\n"
                f"{user_query}\n\n"
                "Solver:\n"
                f"{solver}\n\n"
                "Solver output:\n"
                f"{payload_str}\n\n"
                "Produce the final answer now."
            )
        ),
    ]

    print(f"\n--- Iteration {translator_outcome.iterations_used + 1} ---\n")

    # Intentionally do not bind tools in answer phase.
    current_llm = llm_manager.get_llm()
    full_content = ""
    last_error: Optional[Exception] = None
    for attempt in range(1, 5):
        try:
            full_content, _aggregated_chunk, iter_usage = await stream_once(
                current_llm,
                messages,
                request_kwargs,
            )
            usage.input_tokens += iter_usage.input_tokens
            usage.output_tokens += iter_usage.output_tokens
            usage.total_tokens += iter_usage.total_tokens
            last_error = None
            break
        except Exception as e:
            last_error = e
            err_str = str(e)
            # Check for rate limit (429), unavailable (503), or payment required (402)
            is_retryable = (
                any(c in err_str for c in ["429", "503", "402"]) or
                any(x in err_str.lower() for x in ["rate limit", "unavailable", "payment", "credits", "afford", "insufficient"])
            )
            if is_retryable and attempt < 4:
                err_code = next((c for c in ["429", "503", "402"] if c in err_str), "retryable error")
                print(f"\nAPI Error (Error: {err_code}). Waiting 30s... (retry {attempt}/3)")
                await asyncio.sleep(30)
                current_llm = llm_manager.get_llm()
                continue
            raise

    if last_error is not None and not full_content:
        raise RuntimeError(f"Answer phase failed after retries: {last_error}")

    print()
    if iter_usage.total_tokens > 0 or iter_usage.input_tokens > 0 or iter_usage.output_tokens > 0:
        print(f"\n[TOKEN USAGE - Iteration {translator_outcome.iterations_used + 1}]")
        print(f"  Input tokens:  {iter_usage.input_tokens:,}")
        print(f"  Output tokens: {iter_usage.output_tokens:,}")
        print(f"  Total tokens:  {iter_usage.total_tokens:,}")
    else:
        print(f"\n[TOKEN USAGE - Iteration {translator_outcome.iterations_used + 1}] Not available")

    return (full_content or "").strip(), usage