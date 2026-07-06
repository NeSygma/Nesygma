import json
import re
import sys
import subprocess
from pathlib import Path

def check_validation(problem_spec: dict, result_str: str | None, final_answer_obj: dict | None, extracted_ans: str | None) -> tuple[str, str, any]:
    """Validate solver output against ground truth.
    
    Fully segregated by (benchmark, solver) combination:
      - ASPBench (any solver)
      - FOLIO + clingo
      - FOLIO + z3
      - FOLIO + vampire
      - FOLIO + fallback (LLM text)
      - agieval_lsat + clingo
      - agieval_lsat + z3
      - agieval_lsat + fallback (LLM text)
    """
    validation_status = "Skipped"
    validation_message = ""
    model_answer = None

    if not result_str:
        return "Skipped", "No result to validate", None

    ans_str = extracted_ans if extracted_ans else str(result_str)
    benchmark = problem_spec.get("benchmark", "")
    solver = str(problem_spec.get("solver", "")).lower().strip()

    # ═════════════════════════════════════════════════
    #  ASPBench (any solver)
    # ═════════════════════════════════════════════════
    if benchmark == "ASPBench":
        val_result = validate_aspbench(problem_spec["validator"], ans_str)
        validation_status = "Correct" if val_result.get("valid") else "Incorrect"
        validation_message = val_result.get("message", "")
        model_answer = final_answer_obj if final_answer_obj else ans_str

    # ═════════════════════════════════════════════════
    #  FOLIO
    # ═════════════════════════════════════════════════
    elif benchmark == "FOLIO":
        model_label = ""

        # --- Try structured LLM JSON first (any solver) ---
        if isinstance(final_answer_obj, dict):
            model_label = str(final_answer_obj.get("Conclusion", final_answer_obj.get("conclusion", final_answer_obj.get("label", "")))).strip().capitalize()

        # --- Try raw solver payload ---
        if not model_label:
            val_data = None
            if isinstance(final_answer_obj, dict) and ("positive" in final_answer_obj or "negative" in final_answer_obj or "stdout" in final_answer_obj or "models" in final_answer_obj):
                val_data = final_answer_obj
            elif isinstance(result_str, dict):
                val_data = result_str
            else:
                try:
                    val_data = json.loads(str(result_str))
                except:
                    pass

            if isinstance(val_data, dict):
                # ─── FOLIO + vampire ───
                if "positive" in val_data or "negative" in val_data:
                    pos_szs = str(val_data.get("positive", {}).get("szs_status", "")).lower().replace("_", "")
                    neg_szs = str(val_data.get("negative", {}).get("szs_status", "")).lower().replace("_", "")
                    decisive = {"theorem", "unsatisfiable"}
                    if pos_szs in decisive and neg_szs not in decisive:
                        model_label = "True"
                    elif neg_szs in decisive and pos_szs not in decisive:
                        model_label = "False"
                    elif pos_szs in decisive and neg_szs in decisive:
                        model_label = "Inconsistent"  # Inconsistent premises
                    else:
                        valid_statuses = {"theorem", "unsatisfiable", "satisfiable", "countersatisfiable"}
                        if pos_szs in valid_statuses and neg_szs in valid_statuses:
                            model_label = "Uncertain"

                # ─── FOLIO + z3 ───
                elif "stdout" in val_data:
                    text = str(val_data.get("stdout", ""))
                    text_lower = text.lower()
                    if "status: sat" in text_lower or "status: proved" in text_lower:
                        # Parse the explicit CONCLUSION: line instead of bare substring matching
                        conclusion_line = re.search(r'CONCLUSION:\s*(True|False|Uncertain|Inconsistent)', text, re.IGNORECASE)
                        if conclusion_line:
                            model_label = conclusion_line.group(1).capitalize()
                        else:
                            # Legacy fallback for scripts without CONCLUSION: line
                            if "true" in text_lower: model_label = "True"
                            elif "false" in text_lower: model_label = "False"
                            else: model_label = "Uncertain"

                # ─── FOLIO + clingo ───
                elif "models" in val_data and isinstance(val_data.get("models"), list):
                    clingo_models = val_data["models"]
                    if clingo_models:
                        possible_verdicts = {"True", "False", "Uncertain", "Inconsistent"}
                        for model_symbols in clingo_models:
                            model_verdicts = set()
                            for sym in model_symbols:
                                verdict_match = re.search(r'(?:verdict|answer)[_\(](true|false|uncertain|inconsistent)', str(sym), re.IGNORECASE)
                                if verdict_match:
                                    model_verdicts.add(verdict_match.group(1).capitalize())
                            possible_verdicts = possible_verdicts.intersection(model_verdicts)
                        
                        if "Inconsistent" in possible_verdicts:
                            model_label = "Inconsistent"
                        elif len(possible_verdicts) == 1:
                            model_label = possible_verdicts.pop()

        # --- FOLIO fallback: extract from raw text ---
        if not model_label:
            conclusion_match = re.search(r'(?:Conclusion|Answer)[^\w]*\s*(True|False|Uncertain|Inconsistent)', str(result_str), re.IGNORECASE)
            if conclusion_match: 
                model_label = conclusion_match.group(1).capitalize()
            else:
                verdict_match = re.search(r'(?:verdict|answer)[_\(](true|false|uncertain|inconsistent)', str(result_str), re.IGNORECASE)
                if verdict_match:
                    model_label = verdict_match.group(1).capitalize()
                else:
                    raw_match = re.search(r'\b(True|False|Uncertain|Inconsistent)\b', str(result_str), re.IGNORECASE)
                    if raw_match:
                        model_label = raw_match.group(1).capitalize()

        # --- FOLIO: compare against ground truth ---
        true_label = str(problem_spec["true_label"]).strip().capitalize()
        model_answer = model_label if model_label else (final_answer_obj if final_answer_obj else result_str)
        if model_label == true_label: validation_status = "Correct"
        elif model_label in ["True", "False", "Uncertain"]:
            validation_status = "Incorrect"; validation_message = f"Expected {true_label}, got {model_label}"
        else: validation_status = "Incorrect"; validation_message = f"Could not extract label from: {model_label}"

    # ═════════════════════════════════════════════════
    #  agieval_lsat
    # ═════════════════════════════════════════════════
    elif benchmark == "agieval_lsat":
        model_ans = ""

        # --- Try structured LLM JSON first (any solver) ---
        if isinstance(final_answer_obj, dict):
            model_ans = str(final_answer_obj.get("answer", final_answer_obj.get("Answer", ""))).strip().upper()
        
        # --- Try raw solver payload ---
        if not model_ans:
            val_data = None
            if isinstance(final_answer_obj, dict) and ("stdout" in final_answer_obj or "models" in final_answer_obj):
                val_data = final_answer_obj
            elif isinstance(result_str, dict):
                val_data = result_str
            else:
                try:
                    val_data = json.loads(str(result_str))
                except:
                    pass

            if isinstance(val_data, dict):
                # ─── agieval_lsat + z3 ───
                if "stdout" in val_data:
                    stdout = str(val_data["stdout"]).strip()
                    # Fast path: output is exactly a single letter
                    if re.fullmatch(r'[A-E]', stdout, re.IGNORECASE):
                        model_ans = stdout.upper()
                    else:
                        # 1. Primary check: Look for explicit "answer: X" or "option: X" labels
                        ans_matches = re.findall(r'answer[\s]*[:=]?[\s]*([A-E])\b', stdout, re.IGNORECASE)
                        if not ans_matches:
                            ans_matches = re.findall(r'option[\s]*[:=]?[\s]*([A-E])\b', stdout, re.IGNORECASE)

                        if ans_matches:
                            unique_options = list(set([m.upper() for m in ans_matches]))
                            if len(unique_options) == 1:
                                model_ans = unique_options[0]

                        if not model_ans:
                            # 2. Fallback: Parse the text for valid options while filtering out negative claims
                            clean_stdout = re.sub(r'option\s+[A-E]\s+(?:is\s+)?(?:invalid|not satisfiable|unsatisfiable)', '', stdout, flags=re.IGNORECASE)
                            
                            valid_opt_matches = re.findall(r'valid options?[^\[A-E]*([A-E])\b', clean_stdout, re.IGNORECASE)
                            if valid_opt_matches:
                                unique_options = list(set([m.upper() for m in valid_opt_matches]))
                                if len(unique_options) == 1: model_ans = unique_options[0]
                            
                            if not model_ans:
                                # Find standalone letters in the cleaned output
                                options = re.findall(r'(?:^|[\r\n]|\\r|\\n)\s*([A-E])\s*(?:$|[\r\n]|\\r|\\n)', clean_stdout, re.IGNORECASE)
                                if not options:
                                    options = re.findall(r'\b([A-E])\b', clean_stdout, re.IGNORECASE)
                                if options:
                                    model_ans = options[-1].upper()

                # ─── agieval_lsat + clingo ───
                elif "models" in val_data and isinstance(val_data["models"], list):
                    clingo_models = val_data["models"]
                    if clingo_models:
                        possible_options = {"A", "B", "C", "D", "E"}
                        for model_symbols in clingo_models:
                            model_options = set()
                            for sym in model_symbols:
                                # Universal: any atom ending in _x or (x) where x in {a-e}
                                match = re.search(r'[_\(]([a-e])[\)]?$', str(sym), re.IGNORECASE)
                                if match:
                                    model_options.add(match.group(1).upper())
                            possible_options = possible_options.intersection(model_options)
                        if len(possible_options) == 1:
                            model_ans = possible_options.pop()

        # --- agieval_lsat fallback: extract from raw text ---
        if not model_ans:
            if re.fullmatch(r'[A-E]', str(result_str).strip(), re.IGNORECASE):
                model_ans = str(result_str).strip().upper()
            else:
                ans_match = re.search(r'(?:Answer|Conclusion|Option)[\s]*[:=]?[\s]*([A-E])\b', str(result_str), re.IGNORECASE)
                if ans_match: 
                    model_ans = ans_match.group(1).upper()
                else:
                    clean_str = re.sub(r'option\s+[A-E]\s+(?:is\s+)?invalid', '', str(result_str), flags=re.IGNORECASE)
                    letters = re.findall(r'\b([A-E])\b', clean_str)
                    if letters: model_ans = letters[-1].upper()
                
        if model_ans.startswith("(") and model_ans.endswith(")"): model_ans = model_ans[1:-1]

        # --- agieval_lsat: compare against ground truth ---
        true_ans = str(problem_spec["true_answer"]).strip().upper()
        model_answer = model_ans if model_ans else (final_answer_obj if final_answer_obj else result_str)
        if model_ans == true_ans: validation_status = "Correct"
        elif model_ans in ["A", "B", "C", "D", "E"]:
            validation_status = "Incorrect"; validation_message = f"Expected {true_ans}, got {model_ans}"
        else: validation_status = "Incorrect"; validation_message = f"Could not extract answer from: {model_ans}"

    return validation_status, validation_message, model_answer

def extract_solution_json(output_text: str) -> str | None:
    if not output_text:
        return None
    
    final_ans_match = re.search(r"(?:##|\*\*)\s*Final Answer\s*(?::|##|\*\*)\s*(.*)", output_text, re.DOTALL | re.IGNORECASE)
    if final_ans_match:
        final_text = final_ans_match.group(1).strip()
        label_match = re.search(r"(?:Conclusion|Answer)?[\s\*]*:\s*(\w+)", final_text, re.IGNORECASE)
        if not label_match:
             label_match = re.search(r"\b(True|False|Uncertain)\b", final_text, re.IGNORECASE)
        
        if label_match:
            lbl = label_match.group(1).capitalize()
            if lbl in ["True", "False", "Uncertain"]:
                return json.dumps({"label": lbl})

        inner_json = re.search(r"```json\s*(.*?)\s*```", final_text, re.DOTALL)
        if inner_json:
            return inner_json.group(1).strip()
        return final_text

    json_blocks = re.findall(r"```json\s*(.*?)\s*```", output_text, re.DOTALL)
    if json_blocks:
        candidate = json_blocks[-1].strip()
        try:
            json.loads(candidate)
            return candidate
        except:
            pass

    conclusion_match = re.search(r"\*\*Conclusion\*\*:\s*(\w+)", output_text, re.IGNORECASE)
    if not conclusion_match:
        conclusion_match = re.search(r"Conclusion:\s*(\w+)", output_text, re.IGNORECASE)
    
    if conclusion_match:
        ans = conclusion_match.group(1).capitalize()
        if ans in ["True", "False", "Uncertain"]:
            return json.dumps({"label": ans})

    decoder = json.JSONDecoder()
    candidates = []
    for idx, ch in enumerate(output_text):
        if ch != "{":
            continue
        try:
            obj, consumed = decoder.raw_decode(output_text[idx:])
            if isinstance(obj, dict):
                candidates.append((obj, idx, idx + consumed))
        except json.JSONDecodeError:
            continue
    if not candidates:
        return None
    for obj, start, end in reversed(candidates):
        if "num_colors" in obj and "coloring" in obj:
            return output_text[start:end]
        if "killer" in obj and "killer_name" in obj:
            return output_text[start:end]
        if "label" in obj:
            return output_text[start:end]
        if "Conclusion" in obj or "conclusion" in obj:
            return output_text[start:end]
        if "answer" in obj:
            return output_text[start:end]
        if "solver_ranking" in obj:
            return output_text[start:end]
    _, start, end = max(candidates, key=lambda item: (item[2] - item[1]))
    return output_text[start:end]

def validate_aspbench(ground_truth_file: Path, solution_json: str) -> dict:
    try:
        proc = subprocess.run(
            [sys.executable, str(ground_truth_file)],
            input=solution_json,
            capture_output=True,
            text=True,
            timeout=60,
        )
        stdout = (proc.stdout or "").strip()
        if not stdout:
            stderr = (proc.stderr or "").strip()
            return {"valid": False, "message": f"Validator returned no output. stderr: {stderr}"}
        return json.loads(stdout)
    except Exception as exc:
        return {"valid": False, "message": f"Validator execution error: {exc}"}
