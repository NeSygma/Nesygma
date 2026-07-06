import asyncio
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
    load_problem_spec, create_agent_config, setup_argparser, BenchmarkOutput, format_log
)
from ui.prompts import EVALUATOR_USER_PROMPT, _THINKING_SECTION_TEMPLATE
from switcher.switcher_core import SwitcherAgent

async def main():
    if sys.platform == "win32":
        import io
        sys.stdout.reconfigure(encoding='utf-8')

    parser = setup_argparser(description="NeSygma Switcher Benchmark Script")
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
        switcher_result = None
        switcher_raw_output = ""
        status = "error"
        problem_spec = None
        config = None
        output = None
        system1_answer = "No System 1 answer"
        
        try:
            problem_spec = load_problem_spec(args.benchmark, problem_id)
            solver_str = args.solver if args.solver else problem_spec.get("type", "clingo")
            output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="switcher")
            
            if not args.problem and output.jsonl_file.exists():
                print(f"Problem {problem_id} already has a result.jsonl. Skipping.")
                continue

            config = create_agent_config(args.provider, solver_str, args.model, workspace_path=output.workspace_dir, or_provider=getattr(args, 'or_provider', None), benchmark=problem_spec["benchmark"], key_index=args.key_index)
            
            system1_output = BenchmarkOutput(args.provider, problem_spec["benchmark"], problem_id, problem_spec["id"], mode="system1")
            system1_data = system1_output.load_jsonl()
            
            if not system1_data:
                print(f"Warning: System 1 output not found at {system1_output.jsonl_file}. Skipping problem {problem_id}. Run test_system1.py first.")
                continue

            thinking_content = system1_data.get("thinking_trace", "")
            thinking_section = _THINKING_SECTION_TEMPLATE.format(thinking=thinking_content) if thinking_content else ""
            system1_answer = system1_data.get("system1_result", "No System 1 answer")
            
            puzzle_text = problem_spec["puzzle_selector"]
            evaluator_query = EVALUATOR_USER_PROMPT.format(
                puzzle_text=puzzle_text,
                thinking_section=thinking_section,
                system1_answer=system1_answer
            )
            
            agent = SwitcherAgent(config)
            
            f = io.StringIO()
            with redirect_stdout(f):
                switcher_result, was_truncated = await agent.run(user_query=evaluator_query)
            switcher_raw_output = f.getvalue()
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

        md_content = f"# Benchmark Report (SWITCHER): {problem_spec['benchmark']} - {problem_spec['id']}\n\n"
        md_content += f"**Provider:** {args.provider}\n**Model:** {config.model_name if config else 'Unknown'}\n"
        if config:
            md_content += f"**Config:** max_output_tokens: {config.max_output_tokens}, temperature: {config.temperature}, top_p: {config.top_p}, seed: {config.seed}, reasoning_enabled: {config.reasoning_enabled}, reasoning_effort: {config.reasoning_effort}\n"
        md_content += f"**Duration:** {duration:.2f}s\n\n"
        
        md_content += "## System 1 Execution Context\n\n"
        md_content += "```json\n" + str(system1_answer) + "\n```\n\n"
        
        print(switcher_raw_output)
        md_content += "## Switcher Execution\n\n"
        md_content += format_log(switcher_raw_output)
        if switcher_result: md_content += "\n### Switcher Final Answer\n\n```\n" + str(switcher_result) + "\n```\n"

        if output:
            output.save_md(md_content)
        
        total_input_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Input tokens:\s+([\d,]+)", switcher_raw_output))
        total_output_tokens = sum(int(m.replace(",", "")) for m in re.findall(r"Output tokens:\s+([\d,]+)", switcher_raw_output))

        extracted_confidence = None
        if switcher_result:
            match = re.search(r"Confidence:\s*(\d+)%", switcher_result, re.IGNORECASE)
            if match: extracted_confidence = int(match.group(1))

        summary = {
            "benchmark": problem_spec["benchmark"], "problem_id": problem_id,
            "provider": args.provider, "model": config.model_name if config else "Unknown", "mode": "switcher",
            "status": status, "error": error, "validation": "Skipped", "validation_message": "",
            "true_answer": problem_spec.get("true_label") or problem_spec.get("true_answer"),
            "model_answer": f"Confidence: {extracted_confidence}%" if extracted_confidence is not None else None,
            "duration_s": duration, "timestamp": start_time.isoformat(),
            "total_input_tokens": total_input_tokens, "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens, "final_answer": None,
            "switcher_confidence": extracted_confidence
        }
        if output:
            output.save_jsonl(summary)
            print(f"\nReport saved to: {output.md_file}")
        
        await asyncio.sleep(0.15)

if __name__ == "__main__":
    asyncio.run(main())
