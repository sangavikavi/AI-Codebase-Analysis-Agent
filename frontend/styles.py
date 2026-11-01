"""Modern, rich styling tokens and CSS for Streamlit dashboard."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Glassmorphism Header & Cards */
.metric-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px -4px rgba(37, 99, 235, 0.25);
    border-color: rgba(59, 130, 246, 0.4);
}

.metric-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
}

.metric-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.02em;
}

/* Status Chips */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-completed {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-analyzing, .badge-preprocessing {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-paused {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.badge-failed {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Event Feed Item */
.feed-item {
    border-left: 3px solid #3b82f6;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
}

.feed-item.milestone {
    border-left-color: #10b981;
}

.feed-item.warning {
    border-left-color: #f59e0b;
}

.feed-item.error {
    border-left-color: #ef4444;
}

/* Citation Card */
.citation-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 0.85rem;
    margin-top: 0.5rem;
}
</style>
"""


def render_mermaid(diagram_code: str, height: int = 450) -> str:
    """Render Mermaid diagram inside an interactive iframe with zoom/pan and auto theme."""
    escaped_code = diagram_code.replace("`", "\\`")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'dark',
                securityLevel: 'loose',
                fontFamily: 'Inter, sans-serif'
            }});
        </script>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                background-color: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: auto;
            }}
            .mermaid {{
                width: 100%;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{diagram_code}
        </div>
    </body>
    </html>
    """
    return html_content
