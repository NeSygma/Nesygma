"""
Workspace file management for solver outputs.
"""
import streamlit as st
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

SOLVER_EXTENSIONS = {
    "clingo": [".lp"],
    "z3": [".py"],
    "vampire": [".p", ".tptp"],
}

SOLVER_LANG = {
    "clingo": "prolog",
    "z3": "python",
    "vampire": "text",
}

WORKSPACE_MAP = {
    "clingo": ROOT_DIR / "clingo_workspace",
    "z3": ROOT_DIR / "z3_workspace",
    "vampire": ROOT_DIR / "vampire_workspace",
}


def get_workspace_files(solver: str) -> list:
    workspace_dir = WORKSPACE_MAP.get(solver)
    if not workspace_dir or not workspace_dir.exists():
        return []
    extensions = SOLVER_EXTENSIONS.get(solver, [])
    return sorted(
        f for f in workspace_dir.iterdir()
        if f.is_file() and f.suffix in extensions and not f.name.startswith("__")
    )


def render_workspace_files(solver: str):
    files = get_workspace_files(solver)
    if not files:
        st.info(f"No workspace files found for {solver.upper()}.")
        return
    lang = SOLVER_LANG.get(solver, "text")
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            with st.expander(f" **{f.name}**", expanded=False):
                st.code(content, language=lang)
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")


def clear_all_workspaces():
    """Clear all solver workspace files."""
    for solver, workspace_dir in WORKSPACE_MAP.items():
        if workspace_dir.exists():
            for f in workspace_dir.iterdir():
                if f.is_file() and not f.name.startswith("__"):
                    try:
                        f.unlink()
                    except Exception:
                        pass