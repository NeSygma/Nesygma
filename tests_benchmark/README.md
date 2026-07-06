# NeSygma Benchmark Modular Test Suite - Execution Guide

This directory contains scripts to evaluate NeSygma's performance across different reasoning phases and benchmark datasets.

## Configuration & Modifying LLMs
If you need to add or modify an LLM provider, or change core generation parameters, you will need to edit three files:
1. `tests_benchmark/benchmark_config.py` - Sets default model names per provider, generation parameters (`max_output_tokens`, `temperature`, `top_p`), reasoning settings, and API key environment variable loading logic for the benchmarking suite.
2. `agent/config.py` - Defines the `LLMProvider` Enum and `PROVIDER_CONFIG` mapping (which maps each provider to its base API URL and expected API key environment variables).
3. `agent/llm_client.py` - Contains `LLMManager`, which handles the actual instantiation of LangChain models (`ChatDeepSeek`, `ChatGoogleGenerativeAI`, etc.) based on the provider.

---

## Benchmark Phases

### 1. System 1 (Pure Language Model Reasoning)
Runs only the LLM reasoning phase without symbolic solvers or error refinement.

*   **FOLIO:**
    ```bash
    python tests_benchmark/test_system1.py --benchmark FOLIO --problem 86 --provider google
    ```
*   **ASPBench:**
    ```bash
    python tests_benchmark/test_system1.py --benchmark ASPBench --problem 13 --provider xiaomi
    ```
*   **AGIEval LSAT:**
    ```bash
    python tests_benchmark/test_system1.py --benchmark agieval_lsat --problem 11 --provider openrouter
    ```

---

### 2. Selector (Solver Recommendation)
Evaluates the logical structure of a puzzle and ranks solvers (Z3, Clingo, Vampire) based on structural fit using language model.

*   **FOLIO:**
    ```bash
    python tests_benchmark/test_selector.py --benchmark FOLIO --problem 111 --provider google
    ```
*   **ASPBench:**
    ```bash
    python tests_benchmark/test_selector.py --benchmark ASPBench --problem 1 --provider openrouter
    ```
*   **AGIEval LSAT:**
    ```bash
    python tests_benchmark/test_selector.py --benchmark agieval_lsat --problem 225 --provider openrouter
    ```

---

### 3. Switcher (Metacognition)
Uses the thinking trace and answer from System 1 to act like LLM as a Judge to give confidence score.
*Note: Run the corresponding System 1 test first.*

*   **FOLIO:**
    ```bash
    python tests_benchmark/test_switcher.py --benchmark FOLIO --problem 111 --provider google
    ```
*   **ASPBench:**
    ```bash
    python tests_benchmark/test_switcher.py --benchmark ASPBench --problem 47 --provider mistral
    ```
*   **AGIEval LSAT:**
    ```bash
    python tests_benchmark/test_switcher.py --benchmark agieval_lsat --problem 55 --provider openrouter
    ```

---

### 4. MCP (Symbolic Reasoning)
Language models translate the problem into symbolic code, execute solvers, and iteratively refining errors.

**Automatic Fallback:** When no `--solver` is specified, MCP reads the full solver ranking from Selector and tries solvers in order. If the first solver fails (translator error, runtime error), it automatically falls back to the second solver, then the third. When `--solver` is specified, it uses only that solver with no fallback.

*Note: Omit `--solver` to use the full ranked fallback chain from Selector's results.*

*   **FOLIO (Auto-Select with Fallback):**
    ```bash
    python tests_benchmark/test_mcp.py --benchmark FOLIO --problem 145 --provider google
    ```
*   **ASPBench (Explicit Solver, No Fallback):**
    ```bash
    python tests_benchmark/test_mcp.py --benchmark ASPBench --problem 4 --provider google --solver clingo
    ```
*   **AGIEval LSAT (Explicit Solver, No Fallback):**
    ```bash
    python tests_benchmark/test_mcp.py --benchmark agieval_lsat --problem 230 --provider google --solver z3
    ```
*   **Batch Run (Auto-Select with Fallback):**
    ```bash
    python tests_benchmark/test_mcp.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```

> **Note on Failures:** If a solver fails (e.g., translator error), `test_mcp.py` will save the partial output to `output_mcp/{provider}/{benchmark}/{problem_id}/{solver}/index.md` and `result.jsonl` with `status: error`. This ensures that on the next run, it skips that specific solver and moves to the next one in the fallback chain.

---

### 5. System 2 (Selector → MCP with Solver Fallback)
Runs the full System 2 pipeline: Selector ranks solvers, then MCP tries them in order with automatic fallback on failure (e.g., translator errors). Reuses prior Selector and MCP results when available.

*   **Single Problem:**
    ```bash
    python tests_benchmark/test_system2.py --benchmark FOLIO --problem 86 --provider google
    ```
*   **Batch Run (reuses existing selector/mcp outputs):**
    ```bash
    python tests_benchmark/test_system2.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```
*   **With Solver Override (skips Selector entirely):**
    ```bash
    python tests_benchmark/test_system2.py --benchmark ASPBench --problem 4 --provider google --solver z3
    ```

**Stage-level skip logic:**
1. **Selector** — If `output_selector/` already has results for this problem+provider, the ranking is reused without re-running the Selector.
2. **MCP per solver** — If `output_mcp/{solver}/` already has results, successful runs are reused and failed runs are skipped to the next solver.
3. **Full problem** — If `output_system2/` already has `result.jsonl`, the entire problem is skipped (range mode only).

---

### 6. NeSygma (Full Pipeline: System 1 → Switcher → System 2 Fallback)
The complete NeSygma pipeline: System 1 runs first, then the Switcher evaluates confidence. If confidence ≥ 75%, the System 1 answer is kept. If confidence < 75%, it escalates to System 2 (Selector → MCP with solver fallback). If escalated and all solvers fail, it defaults back to the System 1 answer. Reuses prior stage results when available.

*   **Single Problem:**
    ```bash
    python tests_benchmark/test_nesygma.py --benchmark FOLIO --problem 86 --provider google
    ```
*   **Batch Run (reuses all existing stage outputs):**
    ```bash
    python tests_benchmark/test_nesygma.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```
*   **With Solver Override (skips Selector when escalating):**
    ```bash
    python tests_benchmark/test_nesygma.py --benchmark agieval_lsat --start 1 --end 230 --provider google --solver z3
    ```

**Stage-level skip logic:**
1. **System 1** — If `output_system1/` already has successful results, the answer and thinking trace are reused.
2. **Switcher** — If `output_switcher/` already has results with a confidence score, it is reused.
3. **Selector** — If escalating and `output_selector/` has results, the ranking is reused.
4. **MCP per solver** — If `output_mcp/{solver}/` has results, successful runs are reused and failed runs are skipped.
5. **Full problem** — If `output_nesygma/` already has `result.jsonl`, the entire problem is skipped (range mode only).

---

## Recommended Workflow: Run Components Individually

Running each component separately (System 1, Switcher, Selector, MCP) is **more efficient and less costly** than running `test_system2.py` or `test_nesygma.py` directly:

1. **Run all System 1 first:**
    ```bash
    python tests_benchmark/test_system1.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```
2. **Run all Switcher** (requires System 1 outputs):
    ```bash
    python tests_benchmark/test_switcher.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```
3. **Run all Selector:**
    ```bash
    python tests_benchmark/test_selector.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```
4. **Run all MCP** (reads Selector ranking, tries solvers with fallback):
    ```bash
    python tests_benchmark/test_mcp.py --benchmark FOLIO --start 1 --end 200 --provider google
    ```

> **Note:** If you have already run all 4 components above, you do **not** need to run `test_system2.py` or `test_nesygma.py`. The individual output directories (`output_system1/`, `output_switcher/`, `output_selector/`, `output_mcp/`) contain all the data needed. You can compute System 2 and NeSygma results manually using counting scripts by reading the individual JSONL files.
>
> If some MCP solvers failed and you want to retry, manually check which solvers failed in `output_mcp/` and re-run those specific problems. The fallback mechanism in `test_mcp.py` will automatically skip previously failed solvers and try the next one in the ranking.

---

## Sequential Range Runs & Completion Skipping

Instead of running a single `--problem`, you can run a range of problems sequentially using `--start` and `--end` flags.

*   **Example (run FOLIO problems 1 to 200 using nvidia2):**
    ```bash
    python tests_benchmark/test_system1.py --benchmark FOLIO --start 1 --end 200 --provider nvidia2
    ```

### Key Loop Features:
1.  **Completion Skipping:** In range mode, the runner checks if `result.jsonl` already exists for a problem. If found, it skips the run (saving API credits). If you specify a single `--problem`, it will force-overwrite it.
2.  **Stage Skipping (System 2 & NeSygma):** These pipeline scripts additionally check for outputs from earlier phases (`output_system1/`, `output_switcher/`, `output_selector/`, `output_mcp/`) and reuse them instead of re-running. This means you can run `test_system1.py`, `test_selector.py`, etc. independently first, and `test_system2.py` / `test_nesygma.py` will pick up those results automatically.
3.  **Rate Limiting:** A `0.15-second` delay is added after completing each problem to prevent rate limit limits.

---

## CLI Parameters Reference

| Parameter | Options / Type | Description |
| :--- | :--- | :--- |
| `--benchmark` | `ASPBench`, `FOLIO`, `agieval_lsat` | **Required.** Dataset benchmark to execute. |
| `--problem` | `string` | Single problem ID or index (e.g. `86`). |
| `--start` | `int` | Sequential run start index (inclusive). |
| `--end` | `int` | Sequential run end index (inclusive). |
| `--provider` | `google`, `nvidia`, `nvidia2`, `openrouter`, `mistral`, `xiaomi` | LLM provider to query. Select provider. |
| `--solver` | `clingo`, `vampire`, `z3` | Override solver choice (disables fallback in MCP). |
| `--model` | `string` | Override the default model name. |
| `--or-provider`| `string` | Pin OpenRouter upstream provider routing. |
| `--key-index` | `int` (1-11) | Select Google API key index to override `GOOGLE_API_KEY`. |

