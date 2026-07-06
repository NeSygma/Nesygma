LSAT_TRANSLATION_INPUT_PROMPT = """Translate this problem from natural languages to solver languages:

{query_problem}
"""

LSAT_ANSWER_INPUT_PROMPT = """{query_problem}

Return your final answer in JSON format like this: {{"answer": "A or B or C or D or E"}}.
"""

