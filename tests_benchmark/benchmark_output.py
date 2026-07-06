import json
import re
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

class BenchmarkOutput:
    def __init__(self, provider: str, benchmark: str, problem_num: str, problem_id: str, mode: str, solver: str = None):
        if benchmark == "ASPBench":
            folder_name = problem_id
        else:
            folder_name = f"{problem_num}_{problem_id}"
  
        if provider == "openrouter7":
            provider_folder = "nvidia"
        else:
            provider_folder = provider
            
        base_folder = f"output_{mode}"
        self.base_dir = ROOT_DIR / base_folder / provider_folder / benchmark / folder_name
        if solver:
            self.base_dir = self.base_dir / solver
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.md_file = self.base_dir / "index.md"
        self.jsonl_file = self.base_dir / "result.jsonl"
        self.log_content = []
        # Unique workspace per run to avoid race conditions in parallel execution
        self.workspace_dir = self.base_dir / "workspace"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        self.log_content.append(message)
        print(message, end="", flush=True)

    def save_md(self, content: str):
        self.md_file.write_text(content, encoding="utf-8")

    def save_jsonl(self, data: dict):
        with open(self.jsonl_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def load_jsonl(self) -> dict | None:
        if not self.jsonl_file.exists():
            return None
        with open(self.jsonl_file, "r", encoding="utf-8") as f:
            line = f.readline()
            if line:
                return json.loads(line)
        return None

    def capture_solver_files(self, solver: str):
        # Use run-specific workspace if it exists, otherwise fallback to global (legacy)
        workspace_dir = getattr(self, 'workspace_dir', None)
        if not workspace_dir or not workspace_dir.exists():
            workspace_map = {
                "clingo": "clingo_workspace",
                "vampire": "vampire_workspace",
                "z3": "z3_workspace"
            }
            workspace_dir = ROOT_DIR / workspace_map.get(solver, "workspace")
        
        if not workspace_dir.exists():
            return
        
        extensions = {
            "clingo": [".lp"],
            "vampire": [".p", ".tptp"],
            "z3": [".py"]
        }
        allowed_exts = extensions.get(solver, [])
        
        for f in workspace_dir.iterdir():
            if f.is_file() and f.suffix in allowed_exts:
                if f.name.startswith("__"): continue
                shutil.copy2(f, self.base_dir / f.name)

    def clear_workspace(self, solver: str):
        workspace_dir = getattr(self, 'workspace_dir', None)
        if not workspace_dir or not workspace_dir.exists():
            workspace_map = {
                "clingo": "clingo_workspace",
                "vampire": "vampire_workspace",
                "z3": "z3_workspace"
            }
            workspace_dir = ROOT_DIR / workspace_map.get(solver, "workspace")
            
        if workspace_dir.exists():
            for f in workspace_dir.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                    except:
                        pass

def format_log(raw_output: str) -> str:
    md_content = ""
    def render_thinking_block(thinking_lines: list[str]) -> str:
        chunks: list[list[str]] = []
        current: list[str] = []
        for raw_line in thinking_lines:
            stripped = raw_line.strip()
            if not stripped:
                if current:
                    chunks.append(current)
                    current = []
                continue
            current.append(stripped)
        if current:
            chunks.append(current)
        if not chunks:
            return ""
        section = "### Thinking\n\n"
        for chunk in chunks:
            title_match = re.fullmatch(r"\*\*(.+?)\*\*", chunk[0])
            if title_match:
                title = title_match.group(1).strip()
                details = " ".join(chunk[1:]).strip()
                if details:
                    section += f"- **{title}**: {details}\n"
                else:
                    section += f"- **{title}**\n"
            else:
                section += f"- {' '.join(chunk)}\n"
        section += "\n"
        return section

    lines = raw_output.splitlines()
    in_thinking = False
    thinking_lines: list[str] = []

    for line in lines:
        if line.startswith("--- Iteration"):
            md_content += f"## {line.strip('- ')}\n\n"
        elif line.startswith("Query:"):
            md_content += f"### Query\n{line[6:].strip()}\n\n"
        elif "[TOKEN USAGE" in line:
            md_content += f"### {line.strip('[] ')}\n\n"
        elif "[MCP TOOL]" in line:
            md_content += f"### Tool Call: {line[10:].strip()}\n\n"
        elif "[RESULT]" in line:
            md_content += "#### Result\n\n"
        elif "<THINKING>" in line or "<think>" in line:
            in_thinking = True
            thinking_lines = []
        elif "</THINKING>" in line or "</think>" in line:
            md_content += render_thinking_block(thinking_lines)
            in_thinking = False
            thinking_lines = []
        elif line.strip() == "AGENT CONFIGURATION":
             md_content += "## Agent Configuration\n\n"
        elif "="*10 in line or "#"*10 in line:
             continue
        else:
            if in_thinking:
                thinking_lines.append(line)
                continue
            if line.startswith(">"):
                md_content += f"> {line[1:].strip()}\n"
            else:
                md_content += line + "\n"

    if in_thinking and thinking_lines:
        md_content += render_thinking_block(thinking_lines)
    return md_content
