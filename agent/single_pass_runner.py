import asyncio
from typing import Any


from agent.translator.utils import (
    _chunk_content_to_text,
    _extract_reasoning_text,
    _is_rate_limit_error,
)


async def run_single_pass_stream(
    llm_manager: Any,
    messages: list,
    header_title: str,
    user_query: str,
    max_retries: int = 3,
    retry_delay_s: int = 30,
) -> tuple[str, bool]:
    """Run a single-pass, no-tools LLM stream with retry and token usage logging.
    
    Returns (content, was_truncated) where was_truncated is True if the model
    hit max output tokens (finish_reason == 'length').
    """
    print(f"\n{'='*60}")
    print(f" {header_title}")
    print(f"{'='*60}")
    print(f"\n Query: {user_query}\n")

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0

    current_llm = llm_manager.get_llm()
    full_content = ""
    reasoning_active = False
    aggregated_chunk = None
    raw_usage_metadata = None

    for attempt in range(1, max_retries + 1):
        try:
            async for chunk in current_llm.astream(messages):
                if aggregated_chunk is None:
                    aggregated_chunk = chunk
                else:
                    aggregated_chunk += chunk

                # Capture usage metadata from the raw chunk directly to avoid LangChain's 
                # AIMessageChunk.__add__ bug which can duplicate token counts if the API
                # sends usage metadata in multiple terminal chunks.
                # NOTE: Google Gemini sends usage across multiple chunks (input in one,
                # output in another, zeros in the final). Merge by keeping the max of
                # each field.
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
                elif hasattr(chunk, "response_metadata") and chunk.response_metadata and "token_usage" in chunk.response_metadata:
                    raw_usage_metadata = chunk.response_metadata["token_usage"]
                elif hasattr(chunk, "additional_kwargs") and chunk.additional_kwargs and "usage" in chunk.additional_kwargs:
                    raw_usage_metadata = chunk.additional_kwargs["usage"]

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

            break

        except Exception as api_err:
            err_str = str(api_err)
            if _is_rate_limit_error(err_str) and attempt < max_retries:
                err_code = next((c for c in ["429", "503", "402"] if c in err_str), "rate limit/unavailable/payment")
                print(f"\nAPI Error (Error: {err_code}). Waiting {retry_delay_s}s... (retry {attempt}/{max_retries})")
                await asyncio.sleep(retry_delay_s)
                full_content = ""
                reasoning_active = False
                aggregated_chunk = None
                # Stay on the same API key to accommodate top-ups or cooling down
                current_llm = llm_manager.get_llm()
            else:
                raise

    if reasoning_active:
        print("\n</THINKING>\n")

    print()

    # Extract aggregated token usage
    if raw_usage_metadata:
        total_input_tokens = int(raw_usage_metadata.get("prompt_tokens", raw_usage_metadata.get("input_tokens", 0)) or 0)
        total_output_tokens = int(raw_usage_metadata.get("completion_tokens", raw_usage_metadata.get("output_tokens", 0)) or 0)
        # Always compute total from input+output to avoid unreliable provider totals
        total_tokens = total_input_tokens + total_output_tokens
    elif aggregated_chunk:
        if hasattr(aggregated_chunk, "usage_metadata") and aggregated_chunk.usage_metadata:
            meta = aggregated_chunk.usage_metadata
            total_input_tokens = int(meta.get("input_tokens", 0) or 0)
            total_output_tokens = int(meta.get("output_tokens", 0) or 0)
            raw_total = int(meta.get("total_tokens", 0) or 0)
            total_tokens = raw_total if raw_total > 0 else (total_input_tokens + total_output_tokens)
        elif hasattr(aggregated_chunk, "response_metadata") and aggregated_chunk.response_metadata and "token_usage" in aggregated_chunk.response_metadata:
            token_usage = aggregated_chunk.response_metadata["token_usage"]
            total_input_tokens = int(token_usage.get("prompt_tokens", 0) or 0)
            total_output_tokens = int(token_usage.get("completion_tokens", 0) or 0)
            total_tokens = int(token_usage.get("total_tokens", 0) or 0)
        elif hasattr(aggregated_chunk, "additional_kwargs") and aggregated_chunk.additional_kwargs and "usage" in aggregated_chunk.additional_kwargs:
            token_usage = aggregated_chunk.additional_kwargs["usage"]
            total_input_tokens = int(token_usage.get("prompt_tokens", 0) or 0)
            total_output_tokens = int(token_usage.get("completion_tokens", 0) or 0)
            total_tokens = int(token_usage.get("total_tokens", 0) or 0)


    if total_tokens > 0:
        print("\n[TOKEN USAGE]")
        print(f"  Input tokens:  {total_input_tokens:,}")
        print(f"  Output tokens: {total_output_tokens:,}")
        print(f"  Total tokens:  {total_tokens:,}")
    else:
        print("\n[TOKEN USAGE] Data missing. Total tokens evaluated to 0.")

    # Detect truncation (max output tokens hit)
    was_truncated = False
    if aggregated_chunk:
        # Check finish_reason from various provider formats
        finish_reason = None
        if hasattr(aggregated_chunk, "response_metadata") and aggregated_chunk.response_metadata:
            finish_reason = aggregated_chunk.response_metadata.get("finish_reason")
        if hasattr(aggregated_chunk, "additional_kwargs") and aggregated_chunk.additional_kwargs:
            fr = aggregated_chunk.additional_kwargs.get("finish_reason")
            if fr:
                finish_reason = fr
        if isinstance(finish_reason, str) and finish_reason.lower() == "length":
            was_truncated = True
        elif isinstance(finish_reason, dict):
            reason = finish_reason.get("reason") or finish_reason.get("type") or ""
            if "length" in str(reason).lower():
                was_truncated = True

    if was_truncated:
        print("\n TRUNCATED — Model hit max output tokens")

    print(f"\n{'='*60}")
    print("COMPLETE")
    print(f"{'='*60}")

    return full_content, was_truncated
