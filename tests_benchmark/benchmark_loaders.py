import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

FOLIO_ANSWER_INPUT_PROMPT = """Consider the following logical premises:
{premises}

Conclusion to evaluate:
{conclusion}

Question: Based STRICTLY on the premises, is the conclusion True, False, or Uncertain?
Return your final answer in JSON format like this: {{"Conclusion": "True or False or Uncertain in here"}}
"""

LSAT_ANSWER_INPUT_PROMPT = """{query_problem}

Return your final answer in JSON format like this: {{"answer": "A or B or C or D or E"}}.
"""

def load_problem_spec(benchmark: str, problem: str):
    if benchmark == "ASPBench":
        return load_aspbench(problem)
    elif benchmark == "FOLIO":
        return load_folio(problem)
    elif benchmark == "agieval_lsat":
        return load_agieval_lsat(problem)
    raise ValueError(f"Unknown benchmark: {benchmark}")

def load_aspbench(problem_id: str):
    try:
        pid = int(problem_id)
        if 1 <= pid <= 64:
            difficulty = "easy"
            search_pid = pid
        elif pid >= 65:
            difficulty = "hard"
            search_pid = pid - 64
        else:
            raise ValueError(f"ASPBench problem ID {pid} must be at least 1")
    except ValueError:
        raise ValueError(f"ASPBench problem ID must be an integer, got '{problem_id}'")

    aspbench_root = ROOT_DIR / "Benchmark" / "ASPBench"
    path = aspbench_root / "datasets" / difficulty
    
    problem_file = None
    pattern = f"{search_pid:02d}_*_{difficulty}.md"
    matches = list(path.glob(pattern))
    if not matches:
        pattern = f"{search_pid}_*_{difficulty}.md"
        matches = list(path.glob(pattern))
        
    if matches:
        problem_file = matches[0]
    
    if not problem_file:
        raise ValueError(f"Could not find ASPBench problem with ID {pid} in {path}")

    problem_name = problem_file.stem
    ground_truth_py = path / f"{problem_name}_ground_truth.py"
    
    puzzle_text = problem_file.read_text(encoding="utf-8")
    
    prefix = "Translate this problem from natural languages to solver languages:\n\n"
    if "## Output Format" in puzzle_text:
        header_idx = puzzle_text.find("## Output Format")
        json_match = re.search(r"```json.*?```", puzzle_text[header_idx:], re.DOTALL)
        if json_match:
            # Cut from header start to the end of the JSON block
            after_json_idx = header_idx + json_match.end()
            stripped_puzzle = puzzle_text[:header_idx].strip() + "\n\n" + puzzle_text[after_json_idx:].strip()
        else:
            # Fallback: if no JSON block found, do not cut anything
            stripped_puzzle = puzzle_text.strip()
            
        puzzle_translation = prefix + stripped_puzzle.strip()
        puzzle_selector = stripped_puzzle.strip()
    else:
        stripped_puzzle = puzzle_text.strip()
        puzzle_translation = prefix + stripped_puzzle
        puzzle_selector = stripped_puzzle
    
    puzzle_mcp = puzzle_text
    puzzle_system1 = puzzle_text + "\n\nReturn your final answer in JSON format."

    return {
        "benchmark": "ASPBench",
        "problem_id": problem_id,
        "id": problem_name,
        "puzzle": puzzle_mcp,
        "puzzle_translation": puzzle_translation,
        "puzzle_system1": puzzle_system1,
        "puzzle_selector": puzzle_selector,
        "validator": ground_truth_py,
        "type": "clingo"
    }

def load_folio(problem_id: str):
    benchmark_path = ROOT_DIR / "Benchmark" / "FOLIO" / "datasets" / "folio_v2_validation.jsonl"
    try:
        pid = int(problem_id)
        with open(benchmark_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if i == pid:
                    item = json.loads(line)
                    premises = item["premises"]
                    conclusion = item["conclusion"]
                    true_label = item["label"]
                    story_id = item["story_id"]
                    
                    import sys
                    provider = None
                    if "--provider" in sys.argv:
                        try:
                            provider = sys.argv[sys.argv.index("--provider") + 1]
                        except IndexError:
                            pass
                    
                    if provider in ("xiaomi", "xiaomi2") and pid in range(145, 150):
                        premises = premises.replace("Taiwanese", "Korean").replace("taiwanese", "korean")
                        premises = premises.replace("Vladimir", "Dreamy").replace("vladimir", "dreamy")
                        conclusion = conclusion.replace("Taiwanese", "Korean").replace("taiwanese", "korean")
                        conclusion = conclusion.replace("Vladimir", "Dreamy").replace("vladimir", "dreamy")
                    
                    puzzle_system1 = FOLIO_ANSWER_INPUT_PROMPT.format(premises=premises, conclusion=conclusion)
                    puzzle_mcp = puzzle_system1
                    
                    puzzle_translation = f"""Translate this problem from natural languages to solver languages:

Consider the following logical premises:
{premises}

Conclusion to evaluate:
{conclusion}

Question: Based STRICTLY on the premises, is the conclusion True, False, or Uncertain?
"""
                    puzzle_selector = f"Premises:\n{premises}\n\nConclusion:\n{conclusion}\n\nIs the conclusion True, False, or Uncertain?"
                    
                    return {
                        "benchmark": "FOLIO",
                        "problem_id": problem_id,
                        "id": f"story_{story_id}_ex_{pid}",
                        "puzzle": puzzle_mcp,
                        "puzzle_translation": puzzle_translation.strip(),
                        "puzzle_system1": puzzle_system1,
                        "puzzle_selector": puzzle_selector,
                        "true_label": true_label,
                        "type": "vampire"
                    }
        raise ValueError(f"FOLIO example_id {pid} not found in {benchmark_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load FOLIO: {e}")

def load_agieval_lsat(index: str):
    benchmark_path = ROOT_DIR / "Benchmark" / "AR_LSAT" / "datasets" / "agieval_lsat_ar.jsonl"
    try:
        pid = int(index)
        with open(benchmark_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if i == pid:
                    item = json.loads(line)
                    query = item["query"]
                    gold_idx = item["gold"][0]
                    true_answer = chr(ord('A') + gold_idx)
                    
                    puzzle_system1 = LSAT_ANSWER_INPUT_PROMPT.format(query_problem=query)
                    puzzle_mcp = query.strip()
                    
                    puzzle_selector = query.strip()
                    
                    return {
                        "benchmark": "agieval_lsat",
                        "problem_id": index,
                        "id": f"lsat_{pid}",
                        "puzzle": puzzle_mcp,
                        "puzzle_translation": f"Translate this problem from natural languages to solver languages:\n\n{query.strip()}",
                        "puzzle_system1": puzzle_system1,
                        "puzzle_selector": puzzle_selector,
                        "true_answer": true_answer,
                        "type": "z3"
                    }
        raise ValueError(f"Agieval LSAT index {index} out of range")
    except Exception as e:
        raise RuntimeError(f"Failed to load agieval lsat: {e}")
