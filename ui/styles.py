"""
Custom CSS styles for the NeSygma interactive UI.
"""

CUSTOM_CSS = """
<style>
    .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        overflow-x: hidden;
    }
    .stCode > div {
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-x: hidden !important;
        max-width: 100% !important;
    }
    .stCode > div > code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-x: hidden !important;
    }
    .thinking-box {
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #89b4fa;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 400px;
        overflow-y: auto;
    }
    .tool-box {
        background: #1e1e2e;
        color: #a6e3a1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f9e2af;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .token-box {
        background: #313244;
        color: #cdd6f4;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
    .final-answer {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        font-size: 1.1rem;
        word-break: break-word;
        white-space: pre-wrap;
    }
</style>
"""