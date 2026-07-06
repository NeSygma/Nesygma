import asyncio
import json
import re
import ast
import io
from datetime import datetime
from contextlib import redirect_stdout

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from benchmark_utils import (
    load_problem_spec, create_agent_config, setup_argparser, BenchmarkOutput, format_log, extract_solution_json, check_validation
)
from system1.system1_core import System1Agent
from switcher.switcher_core import SwitcherAgent
from selector.selector_core import SelectorAgent
from agent.mcp_core import MCPAgent
from ui.prompts import EVALUATOR_USER_PROMPT, _THINKING_SECTION_TEMPLATE


class TeeStream(io.StringIO):
    """A stream that writes to both a buffer and the original stdout."""
    def __init__(self, buffer, original_stdout):
        super().__init__()
        self.buffer = buffer
        self.original_stdout = original_stdout

    def write(self, s):
        self.buffer.write(s)
        self.original_stdout.write(s)
        self.original_stdout.flush()

    def flush(self):
        self.buffer.flush()
        self.original_stdout.flush()


def extract_ranking_from_result(result_text: str) -> list:
    """Extract solver_ranking from raw selector result text (mirrors ui/pipeline.py logic)."""
    if not result_text:
        return None
    for block in re.findall(r"```json\s*(.*?)\s*```", result_text, re.DOTALL):
        try:
            d = json.loads(block)
            if "solver_ranking" in d:
                return [s.lower().strip() for s in d["solver_ranking"]]
        except json.JSONDecodeError:
            continue
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(result_text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(result_text[idx:])
            if isinstance(obj, dict) and "solver_ranking" in obj:
                return [s.lower().strip() for s in obj["solver_ranking"]]
        except json.JSONDecodeError:
            continue
    return None


def extract_confidence(text: str) -> int:
    """Extract confidence percentage from switcher output."""
    if not text:
        return 0
    m = re.search(r"Confidence:\s*(\d+)%", text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def parse_solver_ranking(model_answer) -> list:
    """Parse solver ranking from selector model_answer field."""
    if isinstance(model_answer, list) and len(model_answer) > 0:
        return [str(s).lower().strip() for s in model_answer]
    if isinstance(model_answer, str):
        try:
            parsed = ast.literal_eval(model_answer)
            if isinstance(parsed, list) and len(parsed) > 0:
                return [str(s).lower().strip() for s in parsed]
        except Exception:
            pass
        try:
            d = json.loads(model_answer)
            if isinstance(d, dict) and "solver_ranking" in d:
                return [str(s).lower().strip() for s in d["solver_ranking"]]
            if isinstance(d, list):
                return [str(s).lower().strip() for s in d]
        except Exception:
            pass
    return None


def load_system1_data(args, problem_spec, problem_id):
    """Try to load existing system1 output. Returns data or None."""
    s1_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="system1")
    return s1_output.load_jsonl()


def load_switcher_data(args, problem_spec, problem_id):
    """Try to load existing switcher output. Returns data or None."""
    sw_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="switcher")
    return sw_output.load_jsonl()


def load_selector_data(args, problem_spec, problem_id):
    """Try to load existing selector output. Returns (solver_ranking, data) or (None, None)."""
    sel_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="selector")
    sel_data = sel_output.load_jsonl()
    if not sel_data or not sel_data.get("model_answer"):
        return None, None
    ranking = parse_solver_ranking(sel_data["model_answer"])
    return ranking, sel_data


def load_mcp_data(args, problem_spec, problem_id, solver_str):
    """Try to load existing MCP output for a specific solver. Returns data or None."""
    mcp_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="mcp", solver=solver_str)
    return mcp_output.load_jsonl()


async def run_mcp_with_solver(args, problem_spec, solver_str, output, user_query):
    """Run MCP with a single solver. Returns (result, raw_output, config)."""
    config = create_agent_config(
        args.provider, solver_str, args.model,
        workspace_path=output.workspace_dir,
        or_provider=getattr(args, 'or_provider', None),
        benchmark=problem_spec["benchmark"],
        key_index=args.key_index
    )
    agent = MCPAgent(config)
    output.clear_workspace(solver_str)

    log_buffer = io.StringIO()
    original_stdout = sys.stdout
    tee = TeeStream(log_buffer, original_stdout)

    translation_query = problem_spec.get("puzzle_translation")

    with redirect_stdout(tee):
        result = await agent.run(
            user_query=user_query,
            translation_query=translation_query
        )
    raw_output = log_buffer.getvalue()

    if not result:
        raise RuntimeError("MCP returned no result — treating as failure")
    if result.startswith("Translator failed"):
        raise RuntimeError(result)

    return result, raw_output, config


async def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    parser = setup_argparser(description="NeSygma Full Pipeline Benchmark (System1 → Switcher → System2 Fallback)")
    args = parser.parse_args()
    if not args.problem and (args.start is None or args.end is None):
        parser.error("Either --problem or both --start and --end must be specified.")

    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")

    import logging
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

    problems = []
    if args.problem:
        problems = [args.problem]
    else:
        problems = [str(i) for i in range(args.start, args.end + 1)]

    for problem_id in problems:
        print(f"\n================ Running Problem {problem_id} ================")
        start_time = datetime.now()
        error = None
        final_result = None
        status = "error"
        problem_spec = None
        config = None
        output = None
        system1_raw_output = ""
        switcher_raw_output = ""
        selector_raw_output = ""
        mcp_raw_output = ""
        confidence = None
        escalated = False
        solver_ranking = []
        used_solver = None
        solvers_tried = []
        s1_answer = None
        thinking_trace = ""
        was_truncated = False

        try:
            problem_spec = load_problem_spec(args.benchmark, problem_id)
            solver_str = args.solver if args.solver else problem_spec.get("type", "clingo")
            output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="nesygma")

            if not args.problem and output.jsonl_file.exists():
                print(f"Problem {problem_id} already has a result.jsonl. Skipping.")
                continue

            # ── Stage 1: System 1 (reuse existing or run fresh) ────
            cached_s1 = load_system1_data(args, problem_spec, problem_id)
            if cached_s1 and cached_s1.get("status") == "success":
                s1_answer = cached_s1.get("system1_result", "")
                thinking_trace = cached_s1.get("thinking_trace", "")
                was_truncated = False  # If it was saved successfully, treat as not truncated
                config = create_agent_config(
                    args.provider, solver_str, args.model,
                    workspace_path=output.workspace_dir,
                    or_provider=getattr(args, 'or_provider', None),
                    benchmark=problem_spec["benchmark"],
                    key_index=args.key_index
                )
                print(f"✓ Reusing existing System 1 output")
            else:
                print("\n── Running System 1 ──")
                config = create_agent_config(
                    args.provider, solver_str, args.model,
                    workspace_path=output.workspace_dir,
                    or_provider=getattr(args, 'or_provider', None),
                    benchmark=problem_spec["benchmark"],
                    key_index=args.key_index
                )
                agent = System1Agent(config)
                user_query = problem_spec["puzzle_system1"]

                f = io.StringIO()
                with redirect_stdout(f):
                    s1_result, was_truncated = await agent.run(user_query=user_query)
                system1_raw_output = f.getvalue()
                print(system1_raw_output)

                s1_answer = s1_result

                # Extract thinking trace
                thinking_lines = []
                in_thinking = False
                for line in system1_raw_output.splitlines():
                    if "<THINKING>" in line or "<think>" in line: in_thinking = True
                    elif "</THINKING>" in line or "</think>" in line: in_thinking = False
                    elif in_thinking: thinking_lines.append(line)
                thinking_trace = "\n".join(thinking_lines).strip()

            # ── Stage 2: Switcher (reuse existing or run fresh) ────
            if was_truncated:
                print("\n── Switcher SKIPPED (System 1 truncated) — escalating directly ──")
                confidence = 0
            else:
                cached_sw = load_switcher_data(args, problem_spec, problem_id)
                if cached_sw and cached_sw.get("status") == "success" and cached_sw.get("switcher_confidence") is not None:
                    confidence = cached_sw["switcher_confidence"]
                    print(f"✓ Reusing existing Switcher output (Confidence: {confidence}%)")
                else:
                    print("\n── Running Switcher ──")
                    thinking_section = _THINKING_SECTION_TEMPLATE.format(thinking=thinking_trace) if thinking_trace else ""
                    puzzle_text = problem_spec.get("puzzle_selector", problem_spec["puzzle"])
                    evaluator_query = EVALUATOR_USER_PROMPT.format(
                        puzzle_text=puzzle_text,
                        thinking_section=thinking_section,
                        system1_answer=s1_answer
                    )

                    sw_agent = SwitcherAgent(config)
                    f = io.StringIO()
                    with redirect_stdout(f):
                        sw_result, sw_truncated = await sw_agent.run(user_query=evaluator_query)
                    switcher_raw_output = f.getvalue()
                    print(switcher_raw_output)

                    if sw_truncated:
                        confidence = 0
                        print("Switcher hit max output tokens — confidence set to 0%")
                    else:
                        confidence = extract_confidence(sw_result)

                    print(f"Switcher Confidence: {confidence}%")

            # ── Stage 3: Decision — escalate or keep System 1 answer ──
            if confidence >= 75:
                print(f"\n✓ Confidence {confidence}% ≥ 75% — keeping System 1 answer (no escalation)")
                final_result = s1_answer
                status = "success_system1"
                escalated = False
            else:
                print(f"\n✗ Confidence {confidence}% < 75% — escalating to System 2 (Selector → MCP)")
                escalated = True

                # ── Stage 3a: Selector (reuse existing or run fresh) ──
                if args.solver:
                    solver_ranking = [args.solver.lower()]
                    print(f"Manual solver override: {args.solver.upper()}")
                else:
                    cached_ranking, sel_data = load_selector_data(args, problem_spec, problem_id)
                    if cached_ranking:
                        solver_ranking = cached_ranking
                        print(f"✓ Reusing existing Selector output: {' → '.join(s.upper() for s in solver_ranking)}")
                    else:
                        print("\n── Running Selector ──")
                        sel_query = problem_spec.get("puzzle_selector", problem_spec["puzzle"])
                        sel_agent = SelectorAgent(config)

                        f = io.StringIO()
                        with redirect_stdout(f):
                            sel_result = await sel_agent.run(user_query=sel_query)
                        selector_raw_output = f.getvalue()
                        print(selector_raw_output)

                        ranking = extract_ranking_from_result(sel_result)
                        if ranking:
                            solver_ranking = ranking
                        else:
                            extracted = extract_solution_json(sel_result)
                            if extracted:
                                try:
                                    parsed = json.loads(extracted)
                                    if isinstance(parsed, dict) and "solver_ranking" in parsed:
                                        solver_ranking = [s.lower().strip() for s in parsed["solver_ranking"]]
                                except Exception:
                                    pass
                            if not solver_ranking:
                                solver_ranking = ["z3", "clingo", "vampire"]
                                print("Selector failed to produce ranking, using default fallback")

                        print(f"Solver ranking: {' → '.join(s.upper() for s in solver_ranking)}")

                # ── Stage 3b: MCP with fallback (skip already-run solvers) ──
                user_query_mcp = problem_spec["puzzle"]
                for solver in solver_ranking:
                    # Check if this solver already ran via test_mcp
                    cached_mcp = load_mcp_data(args, problem_spec, problem_id, solver)
                    if cached_mcp:
                        cached_status = cached_mcp.get("status", "")
                        cached_validation = cached_mcp.get("validation", "")
                        if cached_status == "success" and cached_validation != "Error":
                            solvers_tried.append(solver)
                            final_result = cached_mcp.get("final_answer") or str(cached_mcp.get("model_answer", ""))
                            if isinstance(final_result, dict):
                                final_result = json.dumps(final_result)
                            used_solver = solver
                            status = "success_system2"
                            print(f"✓ Reusing existing MCP result for {solver.upper()} (status={cached_status}, validation={cached_validation})")
                            break
                        else:
                            solvers_tried.append(solver)
                            print(f"✗ Existing MCP result for {solver.upper()} was a failure (status={cached_status}) — skipping to next solver")
                            continue

                    print(f"\n── Trying {solver.upper()} ──")
                    solvers_tried.append(solver)
                    try:
                        mcp_result, mcp_raw, mcp_config = await run_mcp_with_solver(
                            args, problem_spec, solver, output, user_query_mcp
                        )
                        mcp_raw_output += f"\n\n=== MCP ({solver.upper()}) ===\n" + mcp_raw
                        final_result = mcp_result
                        used_solver = solver
                        config = mcp_config
                        status = "success_system2"
                        print(f"✓ {solver.upper()} succeeded!")
                        break
                    except Exception as e:
                        mcp_raw_output += f"\n\n=== MCP ({solver.upper()}) - FAILED ===\n{str(e)}\n"
                        print(f"✗ {solver.upper()} failed: {e}")
                        continue

                if final_result is None:
                    # All solvers failed — fall back to System 1 answer
                    final_result = s1_answer if s1_answer else "All solvers failed."
                    status = "fallback_system1"
                    print("\n✗ All solvers failed — falling back to System 1 answer")

        except Exception as e:
            status = "error"
            error = str(e)
            import traceback
            traceback.print_exc()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if not problem_spec:
            print(f"Failed to load or run problem {problem_id}: {error}")
            continue

        all_raw_output = system1_raw_output + switcher_raw_output + selector_raw_output + mcp_raw_output

        # ── Build markdown report ──────────────────────────────────
        md_content = f"# Benchmark Report (NESYGMA): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
        md_content += f"**Provider:** {args.provider}\n**Model:** {config.model_name if config else 'Unknown'}\n"
        md_content += f"**Confidence:** {confidence}%\n"
        md_content += f"**Escalated:** {escalated}\n"
        if escalated:
            md_content += f"**Solver Ranking:** {' → '.join(s.upper() for s in solver_ranking)}\n"
            md_content += f"**Used Solver:** {used_solver.upper() if used_solver else 'None'}\n"
            md_content += f"**Solvers Tried:** {', '.join(s.upper() for s in solvers_tried)}\n"
        if config:
            md_content += f"**Config:** max_output_tokens: {config.max_output_tokens}, temperature: {config.temperature}, top_p: {config.top_p}, seed: {config.seed}, reasoning_enabled: {config.reasoning_enabled}, reasoning_effort: {config.reasoning_effort}\n"
        md_content += f"**Status:** {status}\n"
        md_content += f"**Duration:** {duration:.2f}s\n\n"

        md_content += "## System 1\n\n"
        md_content += format_log(system1_raw_output)
        if s1_answer:
            md_content += "\n### System 1 Answer\n\n```json\n" + str(s1_answer) + "\n```\n\n"

        if switcher_raw_output:
            md_content += "## Switcher\n\n"
            md_content += format_log(switcher_raw_output)
            md_content += f"\n**Confidence:** {confidence}%\n\n"

        if escalated:
            if selector_raw_output:
                md_content += "## Selector\n\n"
                md_content += format_log(selector_raw_output)

            md_content += "## MCP Execution\n\n"
            md_content += format_log(mcp_raw_output)

        if final_result:
            md_content += "\n## Final Answer\n\n```json\n" + str(final_result) + "\n```\n"

        if output:
            output.save_md(md_content)
            if used_solver:
                output.capture_solver_files(used_solver)

        # ── Token counting ─────────────────────────────────────────
        total_input_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Input tokens:\s+([\d,]+)", all_raw_output))
        total_output_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Output tokens:\s+([\d,]+)", all_raw_output))

        # ── Validation ─────────────────────────────────────────────
        extracted_ans = extract_solution_json(final_result)
        final_answer_obj = None
        if extracted_ans:
            try: final_answer_obj = json.loads(extracted_ans)
            except: pass

        validation_status, validation_message, model_answer = check_validation(
            problem_spec, final_result, final_answer_obj, extracted_ans
        )

        summary = {
            "benchmark": problem_spec["benchmark"], "problem_id": problem_id,
            "provider": args.provider, "model": config.model_name if config else "Unknown",
            "mode": "nesygma",
            "confidence": confidence, "escalated": escalated,
            "solver_ranking": solver_ranking if escalated else [],
            "used_solver": used_solver, "solvers_tried": solvers_tried,
            "status": status, "error": error,
            "validation": validation_status, "validation_message": validation_message,
            "true_answer": problem_spec.get("true_label") or problem_spec.get("true_answer"),
            "model_answer": model_answer, "duration_s": duration, "timestamp": start_time.isoformat(),
            "total_input_tokens": total_input_tokens, "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens, "final_answer": final_answer_obj,
            "thinking_trace": thinking_trace, "system1_result": str(s1_answer)
        }
        if output:
            output.save_jsonl(summary)
            print(f"\nReport saved to: {output.md_file}")

        await asyncio.sleep(0.15)

if __name__ == "__main__":
    asyncio.run(main())
