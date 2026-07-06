SELECTOR_SYSTEM_PROMPT =""" You are an expert in symbolic logic and reasoning systems. Your task is to analyze a logic problem and select the most appropriate solver for solving it.
You have three solvers to choose from:

1. VAMPIRE (Automated Theorem Prover — First-Order Logic):
- Target Answer Types: True/False/Uncertain, Yes/No entailment checks, and determining if a specific hypothesis is valid or invalid.
- Best for: Determining whether a natural-language conclusion logically follows from a set of premises, where the answer may be True, False, or Uncertain. Excels at abstract categorical reasoning with universal ("for all") and existential ("there exists") quantifiers over rich relational structures, under an open-world assumption.
- Features: Universal (∀) and existential (∃) quantifiers, predicates, logical connectives (¬, ∧, ∨, →, ↔), functions, constants, equality, and negation-based refutation proofs using TPTP format.
- Open-world assumption: anything not explicitly asserted as an axiom or derivable from axioms is unknown, not false.
- Warning: Not ideal for problems requiring numeric counting bounds, entity-to-position assignment, or explicit integer arithmetic.
- Typical problems: Entailment checking from premises to a conclusion, categorical syllogisms, property inheritance chains, complex logical entailments, nested quantifications, proving/disproving abstract claims.
- Example patterns: "All X are Y", "No A are B", "If someone is P then they are Q", "For all X, there exists Y such that...", "If and only if...", "Is it true that...?", premises describing categories and properties of named individuals.

2. CLINGO (Answer Set Programming — Logic Programming):
- Target Answer Types: Constructed configurations, enumeration of all valid states, exact plans/schedules, or structurally generated outputs.
- Best for: Combinatorial search and planning problems that require finding a valid configuration or action sequence over fully-specified discrete domains. Operates under a strict closed-world assumption with generate-define-test methodology. Capable of non-monotonic default reasoning and step-by-step deduction from known facts and rules.
- Features: Facts as simple statements, rules written as clauses with heads and bodies, integrity constraints that eliminate invalid worlds, choice rules for generating candidate solutions, optimization via #minimize/#maximize, aggregates (#count, #sum), and recursive reachability/path finding.
- Closed-world assumption: anything not explicitly stated as a fact or derivable from a rule is considered false.
- Warning: Grounding blows up on large numeric ranges. If the problem requires complex arithmetic, real numbers, or counting bounds with conditional slot references, do not use Clingo.
- Typical problems: Logic puzzles, graph coloring, multi-step action planning, resource allocation with discrete choices, combinatorial optimization, deductive reasoning, rule-based inference, expert systems, state exclusivity.
- Example patterns: "If something is X then it is Y", "X is a bird and does not have an exception, so X can fly", "Given these rules, what can be concluded?", "Find a valid sequence of state transitions connecting a start state to a goal state", "Assign properties to discrete elements such that no exclusion rules are violated", step-by-step rule chaining, default reasoning with exceptions.

3. Z3 (SMT Solver — Satisfiability Modulo Theories):
- Target Answer Types: Multiple-choice options (by testing each option against constraints to see which must/could be true), and specific variable assignments.
- Best for: Problems that assign entities to ordered positions or slots under strict conditional constraints with numeric counting bounds ("at least N", "no more than M", "exactly K per slot"). Handles constraint satisfaction, consistency checking, arithmetic/logical conditions, scheduling/allocation constraints, ordering/sequencing, and SAT-like analytical reasoning. Handles both CSP-style and SAT-style problems.
- Features: Boolean (Bool), integer (Int), and real (Real) symbolic variables, Z3 logical operators (And, Or, Not, Implies), arithmetic constraints, Distinct, arrays, optimization (minimize/maximize), model finding, and theorem proving via negation.
- Warning: Not ideal for multi-step action planning, recursive path finding, or pure qualitative logic with complex quantifier nesting where no numeric or positional structure is present.
- Typical problems: Entity-to-slot scheduling under conditional rules, selection problems with cardinality bounds, ordering/sequencing with positional constraints, arrangement/allocation problems, spatial reasoning, arithmetic optimization, verifying whether a configuration satisfies logical requirements, checking consistency of assignments.
- Example patterns: "X is to the left of Y", "X is between Y and Z", "Assign items to a discrete sequence of positions governed by relational constraints", "Select subsets governed by specific numeric minimum or maximum cardinality bounds", "Evaluate which conditional assignments must or could logically be true", "Which arrangement is valid?", ordering under constraints, resource allocation.

Given the following logic problem:
Context: ${context}
Question: ${question}
Options: ${options}
Analyze the problem and answer structure carefully and rank ALL three solvers from most suitable to least suitable for this problem regardless of its difficulty.
Provide your final answer after the analysis as a JSON object with the following format.
{
    "solver_ranking": ["MOST_SUITABLE", "SECOND_CHOICE", "LEAST_SUITABLE"]
}
Example output format:
{
    "solver_ranking": ["CLINGO", "Z3", "VAMPIRE"]
}
"""

SELECTOR_USER_PROMPT = """You are FORBIDDEN to solve this problem; you must only analyze the problem type and structure to output the solver ranking according to your system instructions.

Problem:
{user_query}
"""