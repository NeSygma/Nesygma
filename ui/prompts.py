"""
Shared prompt templates used by the interactive UI and pipeline.
Moved from tests_benchmark/benchmark_utils.py to eliminate dependency.
"""

EVALUATOR_USER_PROMPT = """PROBLEM:
{puzzle_text}

{thinking_section}SYSTEM 1 ANSWER (For Evaluation):
{system1_answer}

ANTI-ANCHORING REMINDER: Do NOT let the System 1 Answer above bias your independent reasoning in Stage 2. You MUST complete your own derivation from the premises alone before comparing against the System 1 Answer. Treat the System 1 Answer as a hypothesis to be verified, not as a guide.

Follow your system instructions to complete all 5 Metacognitive stages evaluating the provided SYSTEM 1 ANSWER.
Apply the three cognitive de-biasing checks (anchoring, confirmation, and overconfidence) at each relevant stage as instructed.
After completing all stages, output your confidence score in EXACTLY this format on a new line:
Confidence: <number between 0 and 100>%"""

_THINKING_SECTION_TEMPLATE = """SYSTEM 1 INTERNAL REASONING (Thinking Trace — for your reference):
{thinking}

Note: The above is System 1's verbatim internal thinking chain before it produced its final answer. Use it as additional evidence when auditing S1's reasoning quality, but do NOT let it anchor your own independent Stage 2 derivation.

"""