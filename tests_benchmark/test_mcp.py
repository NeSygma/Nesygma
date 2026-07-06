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
    """Parse the full solver ranking from selector model_answer. Returns list of solver strings."""
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
        # Generic string parsing fallback
        cleaned = model_answer.replace('"', '').replace('[', '').replace(']', '')
        parts = [s.strip().lower() for s in cleaned.split(',') if s.strip()]
        if parts:
            return parts
    return None


async def run_single_solver(args, problem_spec, problem_id, solver_str, user_query):
    """Run MCP with a single solver. Returns (success, result, raw_output, config, output, error_msg)."""
    output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="mcp", solver=solver_str)
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

    error_msg = None
    result = None
    try:
        with redirect_stdout(tee):
            result = await agent.run(
                user_query=user_query,
                translation_query=translation_query
            )
    except Exception as e:
        error_msg = str(e)

    raw_output = log_buffer.getvalue()

    if not error_msg:
        if not result:
            error_msg = "MCP returned no result — treating as failure"
        elif result.startswith("Translator failed"):
            error_msg = result
            result = None

    success = error_msg is None
    return success, result, raw_output, config, output, error_msg


async def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    parser = setup_argparser(description="NeSygma MCP Benchmark Script")
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
        result = None
        all_raw_output = ""
        status = "error"
        problem_spec = None
        config = None
        output = None
        used_solver = None
        solvers_tried = []
        solver_override = bool(args.solver)

        try:
            problem_spec = load_problem_spec(args.benchmark, problem_id)
            user_query = problem_spec["puzzle"]

            # ── Determine solver list ───────────────────────────────
            if args.solver:
                # User override: single solver, no fallback
                solver_list = [args.solver.lower()]
                print(f"Solver override: {args.solver.upper()} (no fallback)")
            else:
                # Read full ranking from Selector output
                selector_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="selector")
                selector_data = selector_output.load_jsonl()
                if not selector_data or not selector_data.get("model_answer"):
                    print(f"Warning: Selector output not found at {selector_output.jsonl_file}. Skipping problem {problem_id}.")
                    print("Run test_selector.py first to rank solvers, or specify --solver explicitly (e.g., --solver vampire).")
                    continue

                ranking = parse_solver_ranking(selector_data["model_answer"])
                if ranking:
                    solver_list = ranking
                else:
                    solver_list = [problem_spec.get("type", "clingo")]

                print(f"Solver ranking from Selector: {' -> '.join(s.upper() for s in solver_list)}")

            # ── Try solvers in order (fallback only when no --solver) ──
            for solver_str in solver_list:
                # Check if this solver already ran
                existing_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="mcp", solver=solver_str)
                if not args.problem and existing_output.jsonl_file.exists():
                    existing_data = existing_output.load_jsonl()
                    if existing_data:
                        cached_status = existing_data.get("status", "")
                        cached_validation = existing_data.get("validation", "")
                        if cached_status == "success" and cached_validation != "Error":
                            solvers_tried.append(solver_str)
                            result = existing_data.get("final_answer") or str(existing_data.get("model_answer", ""))
                            if isinstance(result, dict):
                                result = json.dumps(result)
                            used_solver = solver_str
                            output = existing_output
                            status = "success"
                            print(f"Reusing existing MCP result for {solver_str.upper()} (status={cached_status}, validation={cached_validation})")
                            break
                        elif not solver_override:
                            # Failed before — skip to next solver in fallback mode
                            solvers_tried.append(solver_str)
                            print(f"Existing MCP result for {solver_str.upper()} was a failure (status={cached_status}) — skipping to next solver")
                            continue
                        # If solver_override, fall through and re-run the single solver

                print(f"\n── Trying {solver_str.upper()} ──")
                solvers_tried.append(solver_str)
                
                success, mcp_result, mcp_raw, mcp_config, mcp_output, err_msg = await run_single_solver(
                    args, problem_spec, problem_id, solver_str, user_query
                )
                
                all_raw_output += mcp_raw
                
                if success:
                    result = mcp_result
                    used_solver = solver_str
                    config = mcp_config
                    output = mcp_output
                    status = "success"
                    print(f"{solver_str.upper()} succeeded!")
                    break
                else:
                    all_raw_output += f"\n\n=== MCP ({solver_str.upper()}) - FAILED ===\n{err_msg}\n"
                    print(f"{solver_str.upper()} failed: {err_msg}")
                    
                    # ── Save the failure for this solver immediately so we can skip it next time ──
                    fail_md = f"# Benchmark Report (MCP): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
                    fail_md += f"**Provider:** {args.provider}\n**Model:** {mcp_config.model_name if mcp_config else 'Unknown'}\n**Solver:** {solver_str}\n"
                    fail_md += f"**Status:** FAILED\n**Error:** {err_msg}\n\n"
                    fail_md += format_log(mcp_raw)
                    mcp_output.save_md(fail_md)
                    
                    mcp_output.save_jsonl({
                        "benchmark": problem_spec["benchmark"], "problem_id": problem_id,
                        "provider": args.provider, "model": mcp_config.model_name if mcp_config else "Unknown",
                        "solver": solver_str, "mode": "mcp", "status": "error", "error": err_msg,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if solver_override:
                        # No fallback when user specifies --solver
                        error = err_msg
                        output = mcp_output  # so the final save block uses it
                        config = mcp_config
                        break
                    continue

            if result is None and status != "success":
                status = "all_solvers_failed" if not solver_override else "error"
                if not error:
                    error = "All solvers failed."
                print(f"\nAll solvers failed for problem {problem_id}.")

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

        # Use the last solver tried for reporting if no success
        report_solver = used_solver or (solvers_tried[-1] if solvers_tried else "unknown")

        # ── Build markdown report ──────────────────────────────────
        md_content = f"# Benchmark Report (MCP): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
        md_content += f"**Provider:** {args.provider}\n**Model:** {config.model_name if config else 'Unknown'}\n**Solver:** {report_solver}\n"
        if len(solvers_tried) > 1:
            md_content += f"**Solvers Tried:** {', '.join(s.upper() for s in solvers_tried)}\n"
        if config:
            md_content += f"**Config:** max_output_tokens: {config.max_output_tokens}, temperature: {config.temperature}, top_p: {config.top_p}, seed: {config.seed}, reasoning_enabled: {config.reasoning_enabled}, reasoning_effort: {config.reasoning_effort}\n"
        md_content += f"**Duration:** {duration:.2f}s\n\n"

        md_content += format_log(all_raw_output)
        if result:
            md_content += "\n## Final Answer\n\n```json\n" + str(result) + "\n```\n"

        if output and status == "success":
            output.save_md(md_content)
            if used_solver:
                output.capture_solver_files(used_solver)

        # ── Token counting ─────────────────────────────────────────
        total_input_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Input tokens:\s+([\d,]+)", all_raw_output))
        total_output_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Output tokens:\s+([\d,]+)", all_raw_output))

        # ── Validation ─────────────────────────────────────────────
        extracted_ans = extract_solution_json(result)
        final_answer_obj = None
        if extracted_ans:
            try: final_answer_obj = json.loads(extracted_ans)
            except: pass

        validation_status, validation_message, model_answer = check_validation(
            problem_spec, result, final_answer_obj, extracted_ans
        )

        summary = {
            "benchmark": problem_spec["benchmark"], "problem_id": problem_id,
            "provider": args.provider, "model": config.model_name if config else "Unknown",
            "solver": report_solver, "mode": "mcp",
            "solvers_tried": solvers_tried,
            "status": status, "error": error,
            "validation": validation_status, "validation_message": validation_message,
            "true_answer": problem_spec.get("true_label") or problem_spec.get("true_answer"),
            "model_answer": model_answer, "duration_s": duration, "timestamp": start_time.isoformat(),
            "total_input_tokens": total_input_tokens, "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens, "final_answer": final_answer_obj
        }
        
        # Only do the final save if we succeeded or if there's an explicit override failure
        # (Otherwise, individual failures were already saved in the loop)
        if output and (status == "success" or solver_override):
            output.save_jsonl(summary)
            print(f"\nReport saved to: {output.md_file}")

        await asyncio.sleep(0.15)

if __name__ == "__main__":
    asyncio.run(main())

