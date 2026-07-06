FOLIO_TRANSLATION_INPUT_PROMPT = """Translate this problem from natural languages to solver languages:

Consider the following logical premises:
{premises}

Conclusion to evaluate:
{conclusion}

Question: Based STRICTLY on the premises, is the conclusion True, False, or Uncertain?
"""

FOLIO_ANSWER_INPUT_PROMPT = """Consider the following logical premises:
{premises}

Conclusion to evaluate:
{conclusion}

Question: Based STRICTLY on the premises, is the conclusion True, False, or Uncertain?
Return your final answer in JSON format like this: {{"Conclusion": "True or False or Uncertain in here"}}
"""


