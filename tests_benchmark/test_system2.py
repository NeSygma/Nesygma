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
from selector.selector_core import SelectorAgent
from agent.mcp_core import MCPAgent


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


def parse_solver_ranking(model_answer) -> list:
    """Parse solver ranking from selector output. Returns list of solver strings."""
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

    parser = setup_argparser(description="NeSygma System 2 Benchmark Script (Selector → MCP with Fallback)")
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
        solver_ranking = ["z3", "clingo", "vampire"]  # default fallback
        used_solver = None
        all_raw_output = ""
        selector_raw_output = ""
        mcp_raw_output = ""
        solvers_tried = []

        try:
            problem_spec = load_problem_spec(args.benchmark, problem_id)
            output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="system2")

            if not args.problem and output.jsonl_file.exists():
                print(f"Problem {problem_id} already has a result.jsonl. Skipping.")
                continue

            # ── Stage 1: Selector (reuse existing or run fresh) ────────
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
                    solver_str_for_config = problem_spec.get("type", "clingo")
                    config = create_agent_config(
                        args.provider, solver_str_for_config, args.model,
                        workspace_path=output.workspace_dir,
                        or_provider=getattr(args, 'or_provider', None),
                        benchmark=problem_spec["benchmark"],
                        key_index=args.key_index
                    )
                    agent = SelectorAgent(config)
                    sel_query = problem_spec.get("puzzle_selector", problem_spec["puzzle"])

                    f = io.StringIO()
                    with redirect_stdout(f):
                        sel_result = await agent.run(user_query=sel_query)
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

                    print(f"Solver ranking: {' → '.join(s.upper() for s in solver_ranking)}")

            # ── Stage 2: MCP with fallback (skip already-run solvers) ──
            user_query = problem_spec["puzzle"]
            for solver in solver_ranking:
                # Check if this solver already ran successfully via test_mcp
                cached_mcp = load_mcp_data(args, problem_spec, problem_id, solver)
                if cached_mcp:
                    cached_status = cached_mcp.get("status", "")
                    cached_validation = cached_mcp.get("validation", "")
                    if cached_status == "success" and cached_validation != "Error":
                        # Reuse this solver's result
                        solvers_tried.append(solver)
                        final_result = cached_mcp.get("final_answer") or str(cached_mcp.get("model_answer", ""))
                        if isinstance(final_result, dict):
                            final_result = json.dumps(final_result)
                        used_solver = solver
                        status = "success"
                        print(f"✓ Reusing existing MCP result for {solver.upper()} (status={cached_status}, validation={cached_validation})")
                        break
                    else:
                        # Solver ran but failed — skip to next
                        solvers_tried.append(solver)
                        print(f"✗ Existing MCP result for {solver.upper()} was a failure (status={cached_status}) — skipping to next solver")
                        continue

                print(f"\n── Trying {solver.upper()} ──")
                solvers_tried.append(solver)
                try:
                    mcp_result, mcp_raw, mcp_config = await run_mcp_with_solver(
                        args, problem_spec, solver, output, user_query
                    )
                    mcp_raw_output += f"\n\n=== MCP ({solver.upper()}) ===\n" + mcp_raw
                    final_result = mcp_result
                    used_solver = solver
                    config = mcp_config
                    status = "success"
                    print(f"✓ {solver.upper()} succeeded!")
                    break
                except Exception as e:
                    mcp_raw_output += f"\n\n=== MCP ({solver.upper()}) - FAILED ===\n{str(e)}\n"
                    print(f"✗ {solver.upper()} failed: {e}")
                    continue

            if final_result is None:
                final_result = "All solvers failed."
                status = "all_solvers_failed"
                print("\n✗ All solvers failed.")

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

        all_raw_output = selector_raw_output + mcp_raw_output

        # ── Build markdown report ──────────────────────────────────
        md_content = f"# Benchmark Report (SYSTEM2): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
        md_content += f"**Provider:** {args.provider}\n**Model:** {config.model_name if config else 'Unknown'}\n"
        md_content += f"**Solver Ranking:** {' → '.join(s.upper() for s in solver_ranking)}\n"
        md_content += f"**Used Solver:** {used_solver.upper() if used_solver else 'None'}\n"
        md_content += f"**Solvers Tried:** {', '.join(s.upper() for s in solvers_tried)}\n"
        if config:
            md_content += f"**Config:** max_output_tokens: {config.max_output_tokens}, temperature: {config.temperature}, top_p: {config.top_p}, seed: {config.seed}, reasoning_enabled: {config.reasoning_enabled}, reasoning_effort: {config.reasoning_effort}\n"
        md_content += f"**Duration:** {duration:.2f}s\n\n"

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
            "mode": "system2",
            "solver_ranking": solver_ranking, "used_solver": used_solver,
            "solvers_tried": solvers_tried,
            "status": status, "error": error,
            "validation": validation_status, "validation_message": validation_message,
            "true_answer": problem_spec.get("true_label") or problem_spec.get("true_answer"),
            "model_answer": model_answer, "duration_s": duration, "timestamp": start_time.isoformat(),
            "total_input_tokens": total_input_tokens, "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens, "final_answer": final_answer_obj
        }
        if output:
            output.save_jsonl(summary)
            print(f"\nReport saved to: {output.md_file}")

        await asyncio.sleep(0.15)

if __name__ == "__main__":
    asyncio.run(main())
