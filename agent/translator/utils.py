import json
import re
from typing import Any, Optional

def _chunk_content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # Skip thinking/reasoning blocks — handled by _extract_reasoning_text
                if item.get("type") in ("thinking", "reasoning"):
                    continue
                text_value = item.get("text")
                if isinstance(text_value, str):
                    parts.append(text_value)
            else:
                text_value = getattr(item, "text", None)
                if isinstance(text_value, str):
                    parts.append(text_value)
        return "".join(parts)
    return str(content)

def _extract_reasoning_text(chunk: Any) -> str:
    if hasattr(chunk, "additional_kwargs") and chunk.additional_kwargs:
        reasoning = (
            chunk.additional_kwargs.get("reasoning_content")
            or chunk.additional_kwargs.get("reasoning")
            or chunk.additional_kwargs.get("reasoning_details")
        )
        if isinstance(reasoning, str):
            return reasoning
        if isinstance(reasoning, dict):
            # Handle cases where it might be {"text": "..."} or similar
            return reasoning.get("text") or reasoning.get("content") or str(reasoning)

    content = getattr(chunk, "content", None)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                block_type = item.get("type", "")
                if block_type == "thinking":
                    # Google Gemini format: {"type": "thinking", "thinking": "..."}
                    # Mistral format: {"type": "thinking", "thinking": [{"type": "text", "text": "..."}]}
                    thought = item.get("thinking") or item.get("text")
                    if isinstance(thought, str):
                        parts.append(thought)
                    elif isinstance(thought, list):
                        # Mistral nested list of text chunks
                        for sub in thought:
                            if isinstance(sub, dict):
                                t = sub.get("text", "")
                                if t:
                                    parts.append(t)
                elif block_type == "reasoning":
                    # OpenRouter / ChatOpenRouter format
                    thought = item.get("reasoning") or item.get("text")
                    if isinstance(thought, str):
                        parts.append(thought)
        if parts:
            return "".join(parts)

    return ""

def _extract_solver_payload(tool_result: Any) -> Optional[dict[str, Any]]:
    if isinstance(tool_result, dict):
        return tool_result

    if isinstance(tool_result, str):
        try:
            parsed = json.loads(tool_result)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None

    if isinstance(tool_result, list):
        for item in tool_result:
            if isinstance(item, dict):
                text_blob = item.get("text")
                if isinstance(text_blob, str):
                    try:
                        parsed = json.loads(text_blob)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        continue
    return None

def _is_terminal_solver_success(payload: Optional[dict[str, Any]], solver: str, benchmark: Optional[str] = None) -> bool:
    """Determine if a solver run produced a terminal (hand-off worthy) result.
    
    Fully segregated by (benchmark, solver) combination:
      - agieval_lsat + clingo
      - agieval_lsat + z3
      - FOLIO + clingo
      - FOLIO + z3
      - FOLIO + vampire
      - Default fallback (ASPBench, etc.)
    """
    if not payload:
        return False

    solver_name = (solver or "").lower().strip()
    bm = (benchmark or "").strip()

    # ─────────────────────────────────────────────────
    # Helper: Clingo base checks (shared across benchmarks)
    # ─────────────────────────────────────────────────
    def _clingo_base_ok() -> bool:
        status = str(payload.get("status", "")).lower().strip()
        models = payload.get("models")
        has_models = isinstance(models, list) and len(models) > 0
        return status in {"satisfiable", "optimum_found"} and has_models

    # ─────────────────────────────────────────────────
    # Helper: Z3 base checks (shared across benchmarks)
    # ─────────────────────────────────────────────────
    def _z3_base_ok() -> bool:
        status = str(payload.get("status", "")).lower().strip()
        if status != "success":
            return False
        stdout = payload.get("stdout")
        stderr = payload.get("stderr")
        text = f"{stdout or ''}\n{stderr or ''}".lower()

        if "status: sat" in text or "status: proved" in text:
            return True
        elif "status: unsat" in text:
            if "true" in text or "false" in text or "proved" in text:
                return True
        return False

    # ─────────────────────────────────────────────────
    # Helper: Vampire base checks (shared across benchmarks)
    # ─────────────────────────────────────────────────
    def _vampire_base_ok() -> bool:
        positive = payload.get("positive") if isinstance(payload.get("positive"), dict) else {}
        negative = payload.get("negative") if isinstance(payload.get("negative"), dict) else {}

        def _szs(run: dict[str, Any]) -> str:
            return str(run.get("szs_status", "unknown")).lower().strip().replace("_", "")

        pos_szs = _szs(positive)
        neg_szs = _szs(negative)

        if pos_szs == "contradictoryaxioms" or neg_szs == "contradictoryaxioms":
            return False
        if "syntaxerror" in pos_szs or "syntaxerror" in neg_szs:
            return False

        decisive = {"theorem", "unsatisfiable"}
        if pos_szs in decisive and neg_szs in decisive:
            return False  # Inconsistent premises

        valid_statuses = {"theorem", "unsatisfiable", "satisfiable", "countersatisfiable"}
        if pos_szs in valid_statuses and neg_szs in valid_statuses:
            return True
        if (pos_szs in decisive and neg_szs not in decisive) or (neg_szs in decisive and pos_szs not in decisive):
            return True

        return False

    # ═════════════════════════════════════════════════
    #  CASE: agieval_lsat + clingo
    # ═════════════════════════════════════════════════
    if bm == "agieval_lsat" and solver_name == "clingo":
        if not _clingo_base_ok():
            return False

        models = payload.get("models", [])
        possible_options = {"A", "B", "C", "D", "E"}
        for model_symbols in models:
            model_options = set()
            for sym in model_symbols:
                # Universal: any atom ending in _x or (x) where x in {a-e}
                match = re.search(r'[_\(]([a-e])[\)]?$', str(sym), re.IGNORECASE)
                if match:
                    model_options.add(match.group(1).upper())
            possible_options = possible_options.intersection(model_options)

        if len(possible_options) != 1:
            print(f"\n[LSAT] Clingo intersection yielded {len(possible_options)} valid options: {possible_options}. Refining to find exactly 1 definitive choice...")
            return False
        return True

    # ═════════════════════════════════════════════════
    #  CASE: agieval_lsat + z3
    # ═════════════════════════════════════════════════
    if bm == "agieval_lsat" and solver_name == "z3":
        if str(payload.get("status", "")).lower().strip() != "success":
            return False

        stdout = str(payload.get("stdout", "")).strip()

        # Fast path: output is exactly a single letter
        if re.fullmatch(r'[A-E]', stdout, re.IGNORECASE):
            return True

        stdout_lower = stdout.lower()
        if "status: unsat" in stdout_lower and "refine:" in stdout_lower:
            print("\n[LSAT] Z3 triggered explicit refinement...")
            return False
        
        # 1. Primary check: Look for explicit "answer: X" or "option: X" labels
        # We prioritize "answer:" as it's the most definitive tag
        ans_matches = re.findall(r'answer[\s]*[:=]?[\s]*([A-E])\b', stdout, re.IGNORECASE)
        if not ans_matches:
            ans_matches = re.findall(r'option[\s]*[:=]?[\s]*([A-E])\b', stdout, re.IGNORECASE)

        if ans_matches:
            # If we found an explicit label, we check if it is unique.
            # We filter the stdout to remove negative mentions (e.g. "Option A is not satisfiable")
            # to see if the "answer: X" we found is actually the only one claimed to be satisfiable.
            unique_options = list(set([m.upper() for m in ans_matches]))
            if len(unique_options) == 1:
                return True

        # 2. Fallback: Parse the text for valid options while filtering out negative claims
        # Filter out negative phrases first
        clean_stdout = re.sub(r'option\s+[A-E]\s+(?:is\s+)?(?:invalid|not satisfiable|unsatisfiable)', '', stdout, flags=re.IGNORECASE)
        
        # Check for "valid options" specifically
        valid_opt_matches = re.findall(r'valid options?[^\[A-E]*([A-E])\b', clean_stdout, re.IGNORECASE)
        if valid_opt_matches:
            unique_options = list(set([m.upper() for m in valid_opt_matches]))
        else:
            # Find standalone letters in the cleaned output
            options = re.findall(r'(?:^|[\r\n]|\\r|\\n)\s*([A-E])\s*(?:$|[\r\n]|\\r|\\n)', clean_stdout, re.IGNORECASE)
            if not options:
                options = re.findall(r'\b([A-E])\b', clean_stdout, re.IGNORECASE)
            unique_options = list(set([opt.upper() for opt in options]))

        if len(unique_options) != 1:
            reason = "multiple options" if len(unique_options) > 1 else "no options"
            print(f"\n[LSAT] Z3 extracted {len(unique_options)} options {unique_options} ({reason}). Refining to find unique solution...")
            return False
        return True

    # ═════════════════════════════════════════════════
    #  CASE: FOLIO + clingo
    # ═════════════════════════════════════════════════
    if bm == "FOLIO" and solver_name == "clingo":
        if not _clingo_base_ok():
            return False

        models = payload.get("models", [])
        possible_verdicts = {"True", "False", "Uncertain", "Inconsistent"}
        has_inconsistent = False
        for model_symbols in models:
            model_verdicts = set()
            for sym in model_symbols:
                v_match = re.search(r'(?:verdict|answer)[_\(](true|false|uncertain|inconsistent)', str(sym), re.IGNORECASE)
                if v_match:
                    val = v_match.group(1).capitalize()
                    model_verdicts.add(val)
                    if val == "Inconsistent":
                        has_inconsistent = True
            possible_verdicts = possible_verdicts.intersection(model_verdicts)

        if has_inconsistent or "Inconsistent" in possible_verdicts:
            print("\n[FOLIO] Clingo premise evaluation returned Inconsistent. Refining...")
            return False

        if len(possible_verdicts) != 1:
            print(f"\n[FOLIO] Clingo intersection yielded {len(possible_verdicts)} valid verdicts: {possible_verdicts}. Refining to find unique solution...")
            return False
        return True

    # ═════════════════════════════════════════════════
    #  CASE: FOLIO + z3
    # ═════════════════════════════════════════════════
    if bm == "FOLIO" and solver_name == "z3":
        if not _z3_base_ok():
            return False

        stdout = str(payload.get("stdout", ""))
        conclusion_match = re.search(r'CONCLUSION:\s*(True|False|Uncertain|Inconsistent)', stdout, re.IGNORECASE)
        if conclusion_match and conclusion_match.group(1).capitalize() == "Inconsistent":
            print("\n[FOLIO] Z3 premise evaluation returned Inconsistent. Refining...")
            return False
        return True

    # ═════════════════════════════════════════════════
    #  CASE: FOLIO + vampire
    # ═════════════════════════════════════════════════
    if bm == "FOLIO" and solver_name == "vampire":
        return _vampire_base_ok()

    # ═════════════════════════════════════════════════
    #  DEFAULT FALLBACK (ASPBench, other benchmarks)
    # ═════════════════════════════════════════════════
    if solver_name == "clingo":
        return _clingo_base_ok()
    if solver_name == "z3":
        return _z3_base_ok()
    if solver_name == "vampire":
        return _vampire_base_ok()

    return False

def _is_rate_limit_error(err_text: str) -> bool:
    """Check if the error is a rate limit or payment error."""
    return (
        any(c in err_text for c in ["429", "503", "402"]) or
        any(x in err_text.lower() for x in ["rate limit", "unavailable", "payment", "credits", "afford", "insufficient", "paymentrequired"])
    )
