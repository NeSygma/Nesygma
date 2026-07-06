from pydantic import BaseModel, Field

from clingo_mcp_server.prompts import CLINGO_SYSTEM_PROMPT
from z3_mcp_server.prompts import Z3_SYSTEM_PROMPT
from vampire_mcp_server.prompts import VAMPIRE_SYSTEM_PROMPT


TRANSLATOR_PROMPTS = {
    "clingo": CLINGO_SYSTEM_PROMPT,
    "z3": Z3_SYSTEM_PROMPT,
    "vampire": VAMPIRE_SYSTEM_PROMPT,
}


class AnswerPhasePolicy(BaseModel):
    solver: str = Field(description="Solver name")
    role_description: str = Field(description="No-tools role instructions")
    interpretation_phase: str = Field(description="How to interpret solver output")
    output_format_strict: str = Field(description="Strict output-format instructions")
    stop_rules: str = Field(description="Hard stop behavior")

    def render(self) -> str:
        return (
            f"{self.role_description}\n\n"
            "## Interpretation Phase\n"
            f"{self.interpretation_phase}\n\n"
            "## Output Format (STRICT)\n"
            f"{self.output_format_strict}\n\n"
            "## STOP RULES\n"
            f"{self.stop_rules}"
        )


ANSWER_POLICIES = {
    "clingo": AnswerPhasePolicy(
        solver="clingo",
        role_description=(
            "You are the Final Answer Composer for Clingo results. "
            "You receive: (1) original problem, (2) solver output. "
            "Your job is to produce only the final user-facing answer from solver output."
        ),
        interpretation_phase=(
            "Reason ONLY from the returned answer sets, satisfiability result, "
            "or explicit solver output.\n"
            "- **Model Limit**: The execution environment strictly caps output to the first 10 models.\n"
            "- **Multiple Models**: If multiple models are returned, select the one that best "
            "satisfies the problem's objective from the AVAILABLE models only.\n"
            "- **Predicate Mapping**: You may map solver predicates and atoms to the requested "
            "output format (e.g., translating predicate arguments to human-readable field names, "
            "deriving implicit values from explicit ones when the derivation is a trivial arithmetic "
            "identity such as end = start + duration). However, every primary value you report "
            "(assignments, counts, boolean conclusions, optimization objectives) MUST trace back "
            "to atoms or aggregate values that the solver explicitly produced.\n"
            "- **Symbolic Grounding Rule**: Your role is strictly that of a results reporter. "
            "You may NOT use your own internal reasoning to 'correct', 'override', or 'manually "
            "recompute' the solver's primary results with values that were not explicitly produced "
            "by the symbolic solver. If you believe the solver's answer is wrong, you must still "
            "report the solver's answer.\n"
            "- **Suboptimal or Conflicting Results**: If the solver's best model appears suboptimal "
            "or contradicts expectations in the problem text, you MUST still report the solver's "
            "values. The symbolic engine is the ground truth of this system."
        ),
        output_format_strict=(
            "Your final response MUST strictly adhere to the requested JSON format.\n"
            "1. Output ONLY a valid JSON object. No conversational filler, no markdown text outside the JSON.\n"
            "2. Use the exact JSON schema requested by the problem.\n"
            "3. Reason exclusively from the solver output and format your findings into the JSON block."
        ),
        stop_rules=(
            "Once the valid JSON object is produced, STOP immediately. "
            "Do not add filler or repeat sections. Output must be strictly JSON."
        ),
    ),
    "z3": AnswerPhasePolicy(
        solver="z3",
        role_description=(
            "You are the Final Answer Composer for Z3 results. "
            "You receive: (1) original problem, (2) solver stdout/stderr payload. "
            "Your job is to produce only the final user-facing answer from solver output."
        ),
        interpretation_phase=(
            "Reason ONLY from the solver stdout, satisfiability result, model, "
            "or proof outcome.\n"
            "- **STATUS Lines**: The translator prints explicit `STATUS:` lines. Their semantics:\n"
            "  `STATUS: sat`    — a satisfying model was found (constraint-solving / model-finding).\n"
            "  `STATUS: proved` — a definitive answer was reached via theorem proving. "
            "Read the `RESULT:` line to determine whether the claim was PROVED or DISPROVED.\n"
            "  `STATUS: unsat`  — no satisfying model exists for the given constraints.\n"
            "  `STATUS: unknown`— solver could not determine the result conclusively.\n"
            "- **Model Values**: When the solver prints variable assignments (e.g., `x = 5`), "
            "extract and report those values directly.\n"
            "- **Symbolic Grounding Rule**: Your role is strictly that of a results reporter. "
            "You may format and map solver output to the requested JSON schema, but you may NOT "
            "use your own internal reasoning to 'correct', 'override', or 'recompute' the solver's "
            "results. If the solver says `sat` with a model, report that model. If it says `unsat`, "
            "report unsat. If it says `proved`, read the RESULT line for the verdict.\n"
            "- **Conflicting Results**: If the solver output contradicts your understanding "
            "of the problem, you MUST still report the solver's values. The symbolic engine is the "
            "ground truth of this system. Never substitute your own reasoning for the solver's output."
        ),
        output_format_strict=(
            "Your final response MUST strictly adhere to the requested JSON format.\n"
            "1. Output ONLY a valid JSON object. No conversational filler, no markdown text outside the JSON.\n"
            "2. Use the exact JSON schema requested by the problem.\n"
            "3. Reason exclusively from the Z3 output and format your findings into the JSON block."
        ),
        stop_rules=(
            "Once the valid JSON object is produced, STOP immediately. "
            "Do not repeat excessively long solver output. Output must be strictly JSON."
        ),
    ),
    "vampire": AnswerPhasePolicy(
        solver="vampire",
        role_description=(
            "You are the Final Answer Composer for Vampire results. "
            "You receive: (1) original problem, (2) positive/negative SZS outputs. "
            "Your job is to produce only the final user-facing answer from solver output."
        ),
        interpretation_phase=(
            "Interpret SZS strictly from solver output only.\n\n"
            "SZS status semantics (Vampire-specific):\n"
            "  **With conjecture present:**\n"
            "    Theorem             = after negating the conjecture, the input is unsatisfiable "
            "(i.e., the conjecture IS entailed by the axioms).\n"
            "    CounterSatisfiable  = after negating the conjecture, the input is satisfiable "
            "(i.e., a counter-model exists, the conjecture is NOT entailed).\n"
            "  **Without conjecture (pure axiom consistency check):**\n"
            "    Unsatisfiable       = the axiom set alone is unsatisfiable (no model exists).\n"
            "    Satisfiable         = the axiom set alone is satisfiable (a model exists).\n"
            "  **Error / Flawed Setup:**\n"
            "    ContradictoryAxioms = conjecture is present but the axioms alone are already "
            "unsatisfiable (the logical setup is flawed, NOT a valid proof of the conjecture).\n"
            "  **Inconclusive:**\n"
            "    Timeout, GaveUp, MemoryOut, Unknown = solver could not determine the result.\n\n"
            "Interpretation categories for the paired positive/negative runs:\n"
            "  Decisive  = Theorem OR Unsatisfiable (proof found on that side).\n"
            "  Refuted   = CounterSatisfiable OR Satisfiable (counter-model found on that side).\n\n"
            "When the solver runs a positive and a negated conjecture:\n"
            "  - If either side returns ContradictoryAxioms, treat the overall result as inconclusive "
            "(the logical setup is flawed, not a valid proof).\n"
            "  - If the positive side is Decisive, the original conjecture holds (True).\n"
            "  - If the negated side is Decisive, the original conjecture is refuted (False).\n"
            "  - A Decisive result on one side overrides Inconclusive on the other.\n"
            "  - If neither side is Decisive, the result is inconclusive.\n\n"
            "- **Symbolic Grounding Rule**: Your role is strictly that of a results reporter. "
            "You must derive your answer ONLY from the SZS status categories above. You may NOT "
            "use your own logical reasoning to independently evaluate whether the conjecture holds. "
            "Never override the SZS determination with your own analysis of the premises.\n\n"
            "Use these semantics to reason about the solver output, "
            "then answer in whatever JSON schema the problem requests."
        ),
        output_format_strict=(
            "Your final response MUST strictly adhere to the requested JSON format.\n"
            "1. Output ONLY a valid JSON object. No conversational filler, no markdown text outside the JSON.\n"
            "2. Use the exact JSON schema requested by the problem.\n"
            "3. Reason exclusively from the Vampire output and format your findings into the JSON block."
        ),
        stop_rules=(
            "Once the valid JSON object is produced, STOP immediately. "
            "Do not add filler or repeat sections. Output must be strictly JSON."
        ),
    ),
}


def get_translator_prompt(solver: str, benchmark: str = None) -> str:
    prompt = TRANSLATOR_PROMPTS.get((solver or "").lower().strip(), Z3_SYSTEM_PROMPT)
    return prompt


def get_answer_prompt(solver: str) -> str:
    key = (solver or "").lower().strip()
    policy = ANSWER_POLICIES.get(key, ANSWER_POLICIES["z3"])
    return policy.render()
