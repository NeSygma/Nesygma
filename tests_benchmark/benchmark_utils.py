import sys
from pathlib import Path

CUR_DIR = Path(__file__).resolve().parent
if str(CUR_DIR) not in sys.path:
    sys.path.insert(0, str(CUR_DIR))

ROOT_DIR = CUR_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configuration and CLI
from benchmark_config import (
    create_agent_config,
    setup_argparser,
)

# Problem loaders and prompts
from benchmark_loaders import (
    FOLIO_ANSWER_INPUT_PROMPT,
    LSAT_ANSWER_INPUT_PROMPT,
    load_problem_spec,
    load_aspbench,
    load_folio,
    load_agieval_lsat,
)

# Validation and extraction
from benchmark_validators import (
    check_validation,
    extract_solution_json,
    validate_aspbench,
)

# Outputs and logging
from benchmark_output import (
    BenchmarkOutput,
    format_log,
)
