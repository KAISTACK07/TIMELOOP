"""
Converts README.md to a styled HTML file, then opens it in the browser for PDF printing.
"""
import markdown
import os

README_PATH = os.path.join(os.path.dirname(__file__), '..', 'README.md')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'TimeLoop_Documentation.html')

with open(README_PATH, 'r', encoding='utf-8') as f:
    md_content = f.read()

html_body = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br'],
)

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TimeLoop — Project Documentation</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --bg: #ffffff;
    --text: #1a1a2e;
    --text-secondary: #4a4a6a;
    --accent: #e63946;
    --accent-light: #fdf0f0;
    --border: #e8e8f0;
    --code-bg: #f4f4f8;
    --heading-color: #0f0f1a;
    --link: #e63946;
    --table-header-bg: #1a1a2e;
    --table-header-text: #ffffff;
    --table-stripe: #f8f8fc;
    --blockquote-bg: #fdf6e3;
    --blockquote-border: #e6a817;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: var(--text);
    background: var(--bg);
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 50px;
  }}

  /* ── Cover / Title ── */
  h1 {{
    font-size: 28pt;
    font-weight: 700;
    color: var(--accent);
    margin-top: 10px;
    margin-bottom: 8px;
    padding-bottom: 16px;
    border-bottom: 3px solid var(--accent);
    letter-spacing: -0.5px;
  }}

  h2 {{
    font-size: 16pt;
    font-weight: 700;
    color: var(--heading-color);
    margin-top: 36px;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border);
    page-break-after: avoid;
  }}

  h3 {{
    font-size: 13pt;
    font-weight: 600;
    color: var(--heading-color);
    margin-top: 24px;
    margin-bottom: 10px;
    page-break-after: avoid;
  }}

  h4 {{
    font-size: 11.5pt;
    font-weight: 600;
    color: var(--text-secondary);
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}

  p {{
    margin-bottom: 12px;
    text-align: justify;
  }}

  /* ── Links ── */
  a {{
    color: var(--link);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s;
  }}
  a:hover {{
    border-bottom-color: var(--link);
  }}

  /* ── Lists ── */
  ul, ol {{
    margin-bottom: 14px;
    padding-left: 24px;
  }}
  li {{
    margin-bottom: 5px;
  }}
  li > ul, li > ol {{
    margin-top: 4px;
    margin-bottom: 4px;
  }}

  /* ── Code ── */
  code {{
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9.5pt;
    background: var(--code-bg);
    padding: 2px 6px;
    border-radius: 4px;
    color: #c7254e;
  }}

  pre {{
    background: #1a1a2e;
    color: #e0e0f0;
    padding: 18px 22px;
    border-radius: 8px;
    overflow-x: auto;
    margin-bottom: 18px;
    font-size: 9pt;
    line-height: 1.6;
    page-break-inside: avoid;
  }}
  pre code {{
    background: transparent;
    color: inherit;
    padding: 0;
    border-radius: 0;
  }}

  /* ── Tables ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    font-size: 10pt;
    page-break-inside: avoid;
  }}
  thead th {{
    background: var(--table-header-bg);
    color: var(--table-header-text);
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    font-size: 9.5pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  thead th:first-child {{
    border-radius: 6px 0 0 0;
  }}
  thead th:last-child {{
    border-radius: 0 6px 0 0;
  }}
  tbody td {{
    padding: 9px 14px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }}
  tbody tr:nth-child(even) {{
    background: var(--table-stripe);
  }}
  tbody tr:last-child td:first-child {{
    border-radius: 0 0 0 6px;
  }}
  tbody tr:last-child td:last-child {{
    border-radius: 0 0 6px 0;
  }}

  /* ── Blockquotes ── */
  blockquote {{
    border-left: 4px solid var(--blockquote-border);
    background: var(--blockquote-bg);
    padding: 14px 20px;
    margin: 16px 0;
    border-radius: 0 8px 8px 0;
    font-style: italic;
    color: var(--text-secondary);
    page-break-inside: avoid;
  }}
  blockquote p {{
    margin-bottom: 0;
  }}
  blockquote strong {{
    color: var(--text);
  }}

  /* ── Horizontal Rules ── */
  hr {{
    border: none;
    border-top: 2px solid var(--border);
    margin: 32px 0;
  }}

  /* ── Emoji Bullets ── */
  li strong {{
    color: var(--heading-color);
  }}

  /* ── Print Styles ── */
  @media print {{
    body {{
      padding: 20px 30px;
      font-size: 10pt;
      max-width: 100%;
    }}
    h1 {{
      font-size: 24pt;
    }}
    h2 {{
      font-size: 14pt;
      break-after: avoid;
    }}
    h3 {{
      font-size: 12pt;
      break-after: avoid;
    }}
    pre {{
      font-size: 8pt;
      break-inside: avoid;
    }}
    table {{
      break-inside: avoid;
    }}
    blockquote {{
      break-inside: avoid;
    }}
    a {{
      color: var(--link);
    }}
    .no-print {{
      display: none !important;
    }}
  }}

  /* ── Print Button ── */
  .print-bar {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #1a1a2e, #2d2d44);
    padding: 14px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}
  .print-bar span {{
    color: #ffffff;
    font-weight: 600;
    font-size: 13pt;
    letter-spacing: 0.5px;
  }}
  .print-btn {{
    background: var(--accent);
    color: #fff;
    border: none;
    padding: 10px 28px;
    font-size: 11pt;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.5px;
    transition: all 0.2s;
  }}
  .print-btn:hover {{
    background: #c62e3a;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(230,57,70,0.4);
  }}
  .spacer {{
    height: 60px;
  }}

  /* ── Footer ── */
  body > p:last-child {{
    text-align: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 2px solid var(--border);
    color: var(--text-secondary);
    font-size: 10pt;
  }}
</style>
</head>
<body>
  <div class="print-bar no-print">
    <span>📄 TimeLoop Documentation</span>
    <button class="print-btn" onclick="window.print()">⬇ Save as PDF</button>
  </div>
  <div class="spacer no-print"></div>
  {html_body}
</body>
</html>
"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"HTML generated: {os.path.abspath(OUTPUT_PATH)}")
