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
    load_problem_spec, create_agent_config, setup_argparser, BenchmarkOutput, format_log, extract_solution_json, check_validation
)
from system1.system1_core import System1Agent

async def main():
    if sys.platform == "win32":
        import io
        sys.stdout.reconfigure(encoding='utf-8')

    parser = setup_argparser(description="NeSygma System 1 Benchmark Script")
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
        system1_raw_output = ""
        status = "error"
        problem_spec = None
        config = None
        output = None
        
        try:
            problem_spec = load_problem_spec(args.benchmark, problem_id)
            solver_str = args.solver if args.solver else problem_spec.get("type", "clingo")
            output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="system1")
            
            if not args.problem and output.jsonl_file.exists():
                print(f"Problem {problem_id} already has a result.jsonl. Skipping.")
                continue

            config = create_agent_config(args.provider, solver_str, args.model, workspace_path=output.workspace_dir, or_provider=getattr(args, 'or_provider', None), benchmark=problem_spec["benchmark"], key_index=args.key_index)
            agent = System1Agent(config)
            user_query = problem_spec["puzzle_system1"]
            
            f = io.StringIO()
            with redirect_stdout(f):
                result, was_truncated = await agent.run(user_query=user_query)
            system1_raw_output = f.getvalue()
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
        
        thinking_lines = []
        in_thinking = False
        for line in system1_raw_output.splitlines():
            if "<THINKING>" in line or "<think>" in line: in_thinking = True
            elif "</THINKING>" in line or "</think>" in line: in_thinking = False
            elif in_thinking: thinking_lines.append(line)
        thinking_trace = "\n".join(thinking_lines).strip()
        
        md_content = f"# Benchmark Report (SYSTEM1): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
        md_content += f"**Provider:** {args.provider}\n**Model:** {config.model_name if config else 'Unknown'}\n"
        if config:
            md_content += f"**Config:** max_output_tokens: {config.max_output_tokens}, temperature: {config.temperature}, top_p: {config.top_p}, seed: {config.seed}, reasoning_enabled: {config.reasoning_enabled}, reasoning_effort: {config.reasoning_effort}\n"
        md_content += f"**Duration:** {duration:.2f}s\n\n"
        print(system1_raw_output)
        md_content += format_log(system1_raw_output)
        if result: md_content += "\n## System 1 Final Answer\n\n```json\n" + str(result) + "\n```\n"

        if output:
            output.save_md(md_content)
        
        total_input_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Input tokens:\s+([\d,]+)", system1_raw_output))
        total_output_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Output tokens:\s+([\d,]+)", system1_raw_output))

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
            "provider": args.provider, "model": config.model_name if config else "Unknown", "mode": "system1",
            "status": status, "error": error, "validation": validation_status, "validation_message": validation_message,
            "true_answer": problem_spec.get("true_label") or problem_spec.get("true_answer"),
            "model_answer": model_answer, "duration_s": duration, "timestamp": start_time.isoformat(),
            "total_input_tokens": total_input_tokens, "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens, "final_answer": final_answer_obj,
            "thinking_trace": thinking_trace, "system1_result": str(result)
        }
        if output:
            output.save_jsonl(summary)
            print(f"\nReport saved to: {output.md_file}")
        
        await asyncio.sleep(0.15)

if __name__ == "__main__":
    asyncio.run(main())
