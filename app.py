"""
NeSygma Interactive UI — Streamlit Application (v5 - Clean)

3 Modes:
  1. System 1  — Pure LLM reasoning (no symbolic tools)
  2. System 2  — Selector ranks solvers → MCP tries them in order with fallback
  3. NeSygma   — System1 + Switcher → if confidence < 75%, escalate to Selector + MCP
"""
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from ui.config import (
    build_config, PROVIDER_MODELS, ALL_PROVIDERS, ALL_SOLVERS, ALL_EFFORTS,
    OPENROUTER_MODELS, OPENROUTER_MODEL_LABELS,
)
from ui.capture import (
    run_with_live_output, parse_output, render_parsed_sections, extract_thinking_trace,
)
from ui.workspace import render_workspace_files, clear_all_workspaces
from ui.pipeline import (
    run_system1, run_selector, run_switcher, run_mcp,
    extract_confidence, extract_solver_ranking,
)
from ui.styles import CUSTOM_CSS
from tests_benchmark.benchmark_utils import (
    load_problem_spec, check_validation, extract_solution_json,
)


# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeSygma Interactive",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Session state (must be before sidebar so _busy is defined) ──────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

_busy = st.session_state.is_processing


# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Configuration")
    mode = st.radio("Pipeline Mode", ["System 1", "System 2", "NeSygma"], disabled=_busy)
    st.divider()
    provider = st.selectbox("LLM Provider", ALL_PROVIDERS, index=ALL_PROVIDERS.index("google"), disabled=_busy)

    # ── Model selection: dropdown for OpenRouter, text input for others ──
    model_extra_body = None
    openrouter_provider_cfg = None
    _or_entry = None

    if provider == "openrouter":
        or_label = st.selectbox("Model", OPENROUTER_MODEL_LABELS, index=0, disabled=_busy)
        _or_entry = OPENROUTER_MODELS[OPENROUTER_MODEL_LABELS.index(or_label)]
        model_name = _or_entry["model"]
        openrouter_provider_cfg = _or_entry.get("openrouter_provider")
    else:
        model_name = st.text_input("Model Name", value=PROVIDER_MODELS.get(provider, ""), disabled=_busy)

    st.divider()
    solver_override = None
    if mode in ("System 2", "NeSygma"):
        so = st.selectbox("Solver Override", ["Auto (from Selector)"] + ALL_SOLVERS, disabled=_busy)
        solver_override = None if so == "Auto (from Selector)" else so
    st.divider()

    # ── Reasoning (available for all providers) ──
    with st.expander("Reasoning"):
        _default_re = _or_entry.get("default_reasoning", True) if (provider == "openrouter" and _or_entry) else True
        reasoning_enabled = st.toggle("Enable Reasoning", value=_default_re, disabled=_busy)
        reasoning_effort = st.selectbox("Effort", ALL_EFFORTS, index=ALL_EFFORTS.index("high"), disabled=_busy)


    with st.expander("Advanced"):
        temperature = st.slider("Temperature", 0.0, 2.0, 0.0, 0.05, disabled=_busy)
        top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05, disabled=_busy)
        seed = st.number_input("Seed", value=42, min_value=0, disabled=_busy)
        max_iterations = st.slider("Max MCP Iterations", 1, 10, 4, disabled=_busy)
        max_output_tokens = st.number_input("Max Output Tokens", value=32768, min_value=256, max_value=131072, step=256, disabled=_busy)
        
    st.divider()
    with st.expander("Benchmarking"):
        enable_benchmark = st.toggle("Enable Benchmark", value=False, disabled=_busy)
        benchmark_name = st.selectbox("Dataset", ["ASPBench", "FOLIO", "agieval_lsat"], disabled=not enable_benchmark or _busy)
        benchmark_problem = st.number_input("Problem Number", min_value=1, step=1, disabled=not enable_benchmark or _busy)
        if st.button("Run Benchmark", use_container_width=True, type="secondary", disabled=not enable_benchmark or _busy):
            try:
                spec = load_problem_spec(benchmark_name, str(benchmark_problem))
                query = spec["puzzle_system1"]
                st.session_state.messages.append({"role": "user", "content": query, "benchmark_spec": spec})
                st.session_state.is_processing = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load benchmark problem: {e}")

    st.divider()
    if st.button("New Chat", use_container_width=True, type="primary", disabled=_busy):
        st.session_state.messages = []
        clear_all_workspaces()
        st.rerun()
    st.divider()
    st.caption("NeSygma")


# ── Helper ──────────────────────────────────────────────────────────
def make_config(solver="z3"):
    return build_config(
        provider, model_name, solver, reasoning_enabled, reasoning_effort,
        temperature, top_p, seed, max_iterations, max_output_tokens,
        model_extra_body=model_extra_body,
        openrouter_provider=openrouter_provider_cfg,
    )


# ── Render chat history ─────────────────────────────────────────────
st.title("NeSygma")

# Skip last user message if currently processing (it will be rendered below)
_msgs_to_render = st.session_state.messages
if st.session_state.is_processing and _msgs_to_render and _msgs_to_render[-1]["role"] == "user":
    _msgs_to_render = _msgs_to_render[:-1]

for msg in _msgs_to_render:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            if msg.get("benchmark_spec"):
                st.info(f"Running Benchmark: **{msg['benchmark_spec']['benchmark']} (Problem {msg['benchmark_spec']['problem_id']})**")
            st.markdown(msg["content"])
        else:
            for step in msg.get("steps", []):
                st.markdown(f"#### {step['name']}")
                if step.get("sections"):
                    render_parsed_sections(step["sections"])
                if step.get("extra"):
                    ex = step["extra"]
                    if "ranking" in ex:
                        st.success(f"Solver ranking: **{' → '.join(s.upper() for s in ex['ranking'])}**")
                    if "confidence" in ex:
                        st.metric("Switcher Confidence", f"{ex['confidence']}%")
                    if "workspace_solver" in ex:
                        with st.expander(f"Workspace Files ({ex['workspace_solver'].upper()})"):
                            render_workspace_files(ex["workspace_solver"])
            st.markdown(f'<div class="final-answer">{msg["content"]}</div>', unsafe_allow_html=True)
            if msg.get("validation_status"):
                if msg["validation_status"] == "Correct":
                    st.success(f"**Validation: Correct**")
                elif msg["validation_status"] == "Incorrect":
                    st.error(f"**Validation: Incorrect**\n\n{msg.get('validation_msg', '')}")
                else:
                    st.warning(f"**Validation: {msg['validation_status']}**\n\n{msg.get('validation_msg', '')}")


# ── Chat input ──────────────────────────────────────────────────────
if query := st.chat_input("Enter your logic problem...", disabled=_busy):
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.is_processing = True
    st.rerun()


# ── Process query if flagged ────────────────────────────────────────
if not (st.session_state.is_processing and st.session_state.messages):
    st.stop()

last_msg = st.session_state.messages[-1]
if last_msg["role"] != "user":
    st.stop()

query = last_msg["content"]
benchmark_spec = last_msg.get("benchmark_spec")

with st.chat_message("user"):
    if benchmark_spec:
        st.info(f"Running Benchmark: **{benchmark_spec['benchmark']} (Problem {benchmark_spec['problem_id']})**")
    st.markdown(query)


# ── Solver loop helper ──────────────────────────────────────────────
def _run_solver_loop(solver_ranking: list, query: str, steps: list, benchmark_spec: dict = None) -> str:
    """Try solvers in order with fallback. Returns final answer."""
    for solver in solver_ranking:
        with st.status(f"Trying {solver.upper()}...", expanded=True) as status:
            try:
                cfg = make_config(solver)
                translation_query = None
                
                if benchmark_spec:
                    cfg.benchmark = benchmark_spec["benchmark"]
                    if benchmark_spec.get("puzzle_translation"):
                        translation_query = str(benchmark_spec["puzzle_translation"])
                
                mcp_result, mcp_raw, mcp_live = run_with_live_output(run_mcp, cfg, query, translation_query)
                mcp_sections = parse_output(mcp_raw)
                mcp_live.empty()
                render_parsed_sections(mcp_sections)
                if not mcp_result:
                    raise RuntimeError("MCP returned no result — treating as failure")
                if mcp_result.startswith("Translator failed"):
                    raise RuntimeError(mcp_result)
                with st.expander(f"Workspace Files ({solver.upper()})"):
                    render_workspace_files(solver)
                steps.append({"name": f"MCP ({solver.upper()})", "sections": mcp_sections, "extra": {"workspace_solver": solver}})
                status.update(label=f"{solver.upper()} succeeded!", state="complete")
                return mcp_result
            except Exception:
                with st.expander(f"Workspace Files ({solver.upper()})"):
                    render_workspace_files(solver)
                status.update(label=f"{solver.upper()} failed", state="error")
                steps.append({"name": f"MCP ({solver.upper()}) - FAILED", "sections": [], "extra": {"workspace_solver": solver}})
    return "All solvers failed."


# ── Run pipeline ────────────────────────────────────────────────────
with st.chat_message("assistant"):
    start_time = datetime.now()
    steps = []
    final_answer = ""

    try:
        # ─── System 1 ───────────────────────────────────────
        if mode == "System 1":
            with st.status("Running System 1...", expanded=True) as status:
                cfg = make_config()
                if benchmark_spec: cfg.benchmark = benchmark_spec["benchmark"]
                result, raw, live_box = run_with_live_output(run_system1, cfg, query)
                s1_answer, was_truncated = result
                sections = parse_output(raw)
                live_box.empty()
                render_parsed_sections(sections)
                if was_truncated:
                    st.warning("System 1 hit max output tokens - response truncated")
                status.update(label="System 1 complete!", state="complete")
            final_answer = s1_answer
            steps.append({"name": "System 1", "sections": sections})

        # ─── System 2 ───────────────────────────────────────
        elif mode == "System 2":
            solver_ranking = None
            if solver_override:
                solver_ranking = [solver_override]
                st.info(f"Manual solver: **{solver_override.upper()}**")
            else:
                with st.status("Running Selector...", expanded=True) as status:
                    cfg = make_config()
                    if benchmark_spec: cfg.benchmark = benchmark_spec["benchmark"]
                    if benchmark_spec and benchmark_spec.get("puzzle_selector"):
                        sel_query = benchmark_spec["puzzle_selector"]
                    else:
                        sel_query = query
                    try:
                        sel_result, sel_raw, sel_live = run_with_live_output(run_selector, cfg, sel_query)
                        sel_sections = parse_output(sel_raw)
                        sel_live.empty()
                        render_parsed_sections(sel_sections)
                        solver_ranking = extract_solver_ranking(sel_result) or ["z3", "clingo", "vampire"]
                    except Exception as e:
                        sel_sections = []
                        solver_ranking = ["z3", "clingo", "vampire"]
                        st.warning(f"Selector failed ({e}), falling back to default solver order")
                    status.update(label=f"Selector: {' -> '.join(s.upper() for s in solver_ranking)}", state="complete")
                steps.append({"name": "Selector", "sections": sel_sections, "extra": {"ranking": solver_ranking}})

            final_answer = _run_solver_loop(solver_ranking, query, steps, benchmark_spec)

        # ─── NeSygma ────────────────────────────────────────
        elif mode == "NeSygma":
            # Stage 1: System 1
            with st.status("Running System 1...", expanded=True) as status:
                cfg = make_config()
                if benchmark_spec: cfg.benchmark = benchmark_spec["benchmark"]
                s1_result, s1_raw, s1_live = run_with_live_output(run_system1, cfg, query)
                s1_answer, was_truncated = s1_result
                s1_sections = parse_output(s1_raw)
                s1_live.empty()
                render_parsed_sections(s1_sections)
                thinking_trace = extract_thinking_trace(s1_raw)
                if was_truncated:
                    st.warning("System 1 hit max output tokens - skipping Switcher, escalating directly")
                status.update(label="System 1 complete!", state="complete")
            steps.append({"name": "System 1", "sections": s1_sections})

            # Stage 2: Switcher (skip if System 1 truncated)
            if was_truncated:
                confidence = 0
                steps.append({"name": "Switcher - SKIPPED (truncated)", "sections": [], "extra": {"confidence": 0}})
            else:
                with st.status("Running Switcher...", expanded=True) as status:
                    cfg = make_config()
                    if benchmark_spec: cfg.benchmark = benchmark_spec["benchmark"]
                    sw_result, sw_raw, sw_live = run_with_live_output(run_switcher, cfg, query, s1_answer, thinking_trace)
                    sw_answer, sw_truncated = sw_result
                    sw_sections = parse_output(sw_raw)
                    sw_live.empty()
                    render_parsed_sections(sw_sections)
                    if sw_truncated:
                        confidence = 0
                        st.warning("Switcher hit max output tokens - confidence set to 0%")
                    else:
                        confidence = extract_confidence(sw_answer) or 0
                    status.update(label=f"Switcher: {confidence}% confidence", state="complete")
                steps.append({"name": "Switcher", "sections": sw_sections, "extra": {"confidence": confidence}})

            if confidence >= 75:
                final_answer = s1_answer
            else:
                st.warning(f"Confidence {confidence}% < 75% - Escalating to Symbolic Grounding")

                # Stage 3: Selector + MCP
                solver_ranking = None
                if solver_override:
                    solver_ranking = [solver_override]
                else:
                    with st.status("Running Selector...", expanded=True) as status:
                        cfg = make_config()
                        if benchmark_spec: cfg.benchmark = benchmark_spec["benchmark"]
                        if benchmark_spec and benchmark_spec.get("puzzle_selector"):
                            sel_query = benchmark_spec["puzzle_selector"]
                        else:
                            sel_query = query
                        try:
                            sel_result, sel_raw, sel_live = run_with_live_output(run_selector, cfg, sel_query)
                            sel_sections = parse_output(sel_raw)
                            sel_live.empty()
                            render_parsed_sections(sel_sections)
                            solver_ranking = extract_solver_ranking(sel_result) or ["z3", "clingo", "vampire"]
                        except Exception as e:
                            sel_sections = []
                            solver_ranking = ["z3", "clingo", "vampire"]
                            st.warning(f"Selector failed ({e}), falling back to default solver order")
                        status.update(label=f"Selector: {' -> '.join(s.upper() for s in solver_ranking)}", state="complete")
                    steps.append({"name": "Selector", "sections": sel_sections, "extra": {"ranking": solver_ranking}})

                mcp_answer = _run_solver_loop(solver_ranking, query, steps, benchmark_spec)
                final_answer = mcp_answer if mcp_answer != "All solvers failed." else s1_answer

    except Exception as e:
        final_answer = f"Error: {e}"

    duration = (datetime.now() - start_time).total_seconds()
    st.markdown(f'<div class="final-answer">{final_answer}</div>', unsafe_allow_html=True)
    
    validation_status = None
    validation_msg = None
    if benchmark_spec:
        import json

        extracted_ans = extract_solution_json(final_answer)
        final_answer_obj = None
        if extracted_ans:
            try: final_answer_obj = json.loads(extracted_ans)
            except Exception: pass
            
        val_status, val_msg, _ = check_validation(benchmark_spec, final_answer, final_answer_obj, extracted_ans)
        validation_status = val_status
        validation_msg = val_msg
        
        if val_status == "Correct":
            st.success("Validation: Correct")
        elif val_status == "Incorrect":
            st.error(f"Validation: Incorrect\n\n{val_msg}")
        else:
            st.warning(f"Validation: {val_status}\n\n{val_msg}")

    st.caption(f"Completed in {duration:.1f}s")

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_answer,
        "steps": steps,
        "validation_status": validation_status,
        "validation_msg": validation_msg
    })

st.session_state.is_processing = False
st.rerun()