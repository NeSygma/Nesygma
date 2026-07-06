"""
Streaming capture, output parsing, and rendering for the NeSygma interactive UI.
"""
import asyncio
import io
import json
import re
import sys
import threading
import time

import streamlit as st


# ── Streaming Capture ───────────────────────────────────────────────

class StreamingCapture(io.StringIO):
    """Thread-safe capture that stores stdout for later parsing."""
    def __init__(self):
        super().__init__()
        self._buffer = ""
        self._lock = threading.Lock()
        self._original_stdout = sys.stdout

    def write(self, s):
        self._original_stdout.write(s)
        self._original_stdout.flush()
        with self._lock:
            self._buffer += s
        return len(s)

    def flush(self):
        self._original_stdout.flush()

    def getvalue(self):
        with self._lock:
            return self._buffer


def run_with_live_output(async_func, *args):
    """Run async function in background thread with live Streamlit updates.
    
    Returns (result, raw_output, live_container).
    """
    capture = StreamingCapture()
    result_holder = [None]
    error_holder = [None]
    done = threading.Event()

    live_box = st.empty()

    def target():
        old_stdout = sys.stdout
        sys.stdout = capture
        try:
            result_holder[0] = asyncio.run(async_func(*args))
        except Exception as e:
            error_holder[0] = e
        finally:
            sys.stdout = old_stdout
            done.set()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()

    while not done.is_set():
        raw = capture.getvalue()
        if raw:
            live_box.code(raw, language=None)
        time.sleep(0.3)

    raw = capture.getvalue()
    if raw:
        live_box.code(raw, language=None)

    if error_holder[0] is not None:
        raise error_holder[0]
    return result_holder[0], raw, live_box


# ── Structured Output Parsing ───────────────────────────────────────

class ParsedSection:
    """A single parsed output section."""
    def __init__(self, section_type: str, content: str, label: str = ""):
        self.type = section_type
        self.content = content
        self.label = label


def parse_output(raw: str) -> list:
    """Parse raw agent output into structured sections."""
    sections = []
    lines = raw.splitlines(keepends=True)
    buffer = []
    current_type = "text"
    in_thinking = False
    in_result = False
    current_tool_name = ""

    def flush():
        nonlocal buffer
        text = "".join(buffer).strip()
        if text:
            sections.append(ParsedSection(current_type, text, label=current_tool_name))
        buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if "<THINKING>" in line or "<think>" in line:
            flush()
            in_thinking = True
            current_type = "thinking"
            buffer = []
            i += 1
            continue

        if "</THINKING>" in line or "</think>" in line:
            flush()
            in_thinking = False
            current_type = "text"
            i += 1
            continue

        tool_match = re.match(r'\[MCP TOOL\]\s*(.*)', line.strip())
        if tool_match:
            flush()
            current_tool_name = tool_match.group(1).strip()
            current_type = "tool_call"
            buffer = [f"Tool: {current_tool_name}\n"]
            i += 1
            args_lines = []
            while i < len(lines):
                aline = lines[i]
                if aline.strip().startswith("Args:"):
                    args_lines.append(aline.strip()[5:].strip())
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith("[") and not lines[i].strip().startswith("---"):
                        args_lines.append(lines[i])
                        i += 1
                    break
                elif aline.strip().startswith("[") or aline.strip().startswith("---"):
                    break
                else:
                    args_lines.append(aline)
                    i += 1
            args_text = "".join(args_lines).strip()
            if args_text:
                try:
                    parsed = json.loads(args_text)
                    if isinstance(parsed, dict) and "code" in parsed:
                        buffer.append(f"File: {parsed.get('filename', 'N/A')}\n")
                        buffer.append(f"```python\n{parsed['code']}\n```")
                    else:
                        buffer.append(f"```json\n{json.dumps(parsed, indent=2)}\n```")
                except (json.JSONDecodeError, TypeError):
                    buffer.append(f"```\n{args_text}\n```")
            flush()
            continue

        if line.strip() == "[RESULT]":
            flush()
            current_type = "tool_result"
            in_result = True
            buffer = []
            i += 1
            continue

        if in_result and (
            line.strip().startswith("--- Iteration")
            or line.strip().startswith("[MCP TOOL]")
            or line.strip().startswith("[TOKEN USAGE")
            or line.strip().startswith("TOKEN USAGE")
            or line.strip().startswith("COMPLETE")
        ):
            flush()
            in_result = False
            current_type = "text"
            # Fall through to be parsed as header/text below

        iter_match = re.match(r'---\s*Iteration\s+(\d+)\s*---', line.strip())
        if iter_match:
            flush()
            sections.append(ParsedSection("header", f"Iteration {iter_match.group(1)}"))
            i += 1
            continue

        token_match = re.match(r'(?:\[TOKEN USAGE.*\]|TOKEN USAGE SUMMARY)', line.strip())
        if token_match:
            flush()
            token_lines = [line.strip()]
            i += 1
            while i < len(lines) and (
                "tokens:" in lines[i].lower()
                or lines[i].strip() == ""
                or re.match(r'^[=\-]{3,}$', lines[i].strip())
            ):
                if lines[i].strip() and not re.match(r'^[=\-]{3,}$', lines[i].strip()):
                    token_lines.append(lines[i].strip())
                i += 1
            sections.append(ParsedSection("token_usage", "\n".join(token_lines)))
            continue

        if line.strip().startswith("===") or (line.strip().startswith("MCP ") and "AGENT" in line) or line.strip() == "COMPLETE":
            flush()
            sections.append(ParsedSection("header", line.strip().strip("= ")))
            i += 1
            continue

        if line.strip().startswith("Query:"):
            flush()
            sections.append(ParsedSection("text", line.strip()))
            i += 1
            continue

        buffer.append(line)
        i += 1

    flush()
    return sections


def render_parsed_sections(sections: list):
    """Render parsed output sections with styled Streamlit containers."""
    for sec in sections:
        if sec.type == "header":
            st.markdown(f"#### {sec.content}")
        elif sec.type == "thinking":
            with st.expander("**Thinking / Reasoning**", expanded=False):
                st.markdown(f'<div class="thinking-box">{sec.content}</div>', unsafe_allow_html=True)
        elif sec.type == "tool_call":
            with st.expander(f"**Tool Call: {sec.label}**", expanded=False):
                st.markdown(f'<div class="tool-box">{sec.content}</div>', unsafe_allow_html=True)
        elif sec.type == "tool_result":
            content = sec.content
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                pass
            with st.expander("**Tool Result**", expanded=False):
                st.code(content, language=None)
        elif sec.type == "token_usage":
            st.markdown(f'<div class="token-box">{sec.content}</div>', unsafe_allow_html=True)
        elif sec.type == "text":
            text = sec.content.strip()
            if text:
                st.markdown(text)


# ── Thinking Trace Extraction ───────────────────────────────────────

def extract_thinking_trace(raw: str) -> str:
    """Extract thinking trace from raw output."""
    lines = []
    in_t = False
    for line in raw.splitlines():
        if "<THINKING>" in line or "<think>" in line:
            in_t = True
        elif "</THINKING>" in line or "</think>" in line:
            in_t = False
        elif in_t:
            lines.append(line)
    return "\n".join(lines).strip()