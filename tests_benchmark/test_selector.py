import asyncio
import json
import re
from datetime import datetime
from contextlib import redirect_stdout

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from benchmark_utils import (
    load_problem_spec, create_agent_config, setup_argparser, BenchmarkOutput, format_log, extract_solution_json
)
from selector.selector_core import SelectorAgent

async def main():
    if sys.platform == "win32":
        import io
        sys.stdout.reconfigure(encoding='utf-8')

    parser = setup_argparser(description="NeSygma Selector Benchmark Script")
    args = parser.parse_args()
    if not args.problem and (args.start is None or args.end is None):
        parser.error("Either --problem or both --start and --end must be specified.")
    
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
    
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
        selector_raw_output = ""
        status = "error"
        problem_spec = None
        config = None
        output = None
        
        try:
            problem_spec = load_problem_spec(args.benchmark, problem_id)
            solver_str = args.solver if args.solver else problem_spec.get("type", "clingo")
            output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="selector")
            
            if not args.problem and output.jsonl_file.exists():
                print(f"Problem {problem_id} already has a result.jsonl. Skipping.")
                continue

            config = create_agent_config(args.provider, solver_str, args.model, workspace_path=output.workspace_dir, or_provider=getattr(args, 'or_provider', None), benchmark=problem_spec["benchmark"], key_index=args.key_index)
            agent = SelectorAgent(config)
            user_query = problem_spec["puzzle_selector"]
            
            f = io.StringIO()
            with redirect_stdout(f):
                result = await agent.run(user_query=user_query)
            selector_raw_output = f.getvalue()
            status = "success"
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

        md_content = f"# Benchmark Report (SELECTOR): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
        md_content += f"**Provider:** {args.provider}\n**Model:** {config.model_name if config else 'Unknown'}\n"
        if config:
            md_content += f"**Config:** max_output_tokens: {config.max_output_tokens}, temperature: {config.temperature}, top_p: {config.top_p}, seed: {config.seed}, reasoning_enabled: {config.reasoning_enabled}, reasoning_effort: {config.reasoning_effort}\n"
        md_content += f"**Duration:** {duration:.2f}s\n\n"
        print(selector_raw_output)
        md_content += format_log(selector_raw_output)
        if result: md_content += "\n## Selector Final Answer\n\n```json\n" + str(result) + "\n```\n"

        if output:
            output.save_md(md_content)
        
        total_input_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Input tokens:\s+([\d,]+)", selector_raw_output))
        total_output_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Output tokens:\s+([\d,]+)", selector_raw_output))

        extracted_ans = extract_solution_json(result)
        final_answer_obj = None
        if extracted_ans:
            try: final_answer_obj = json.loads(extracted_ans)
            except: pass

        model_answer = None
        validation_status = "Skipped"
        
        if isinstance(final_answer_obj, dict):
            model_answer = final_answer_obj.get("solver_ranking")
        else:
            model_answer = final_answer_obj if final_answer_obj else (extracted_ans if extracted_ans else result)

        summary = {
            "benchmark": problem_spec["benchmark"], "problem_id": problem_id,
            "provider": args.provider, "model": config.model_name if config else "Unknown", "mode": "selector",
            "status": status, "error": error, "validation": validation_status, "validation_message": "",
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
