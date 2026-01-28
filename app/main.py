import html
import logging
import sys

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

import ai_communication

LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,  # wichtig: überschreibt evtl. bestehende configs (uvicorn etc.)
)

app = FastAPI()

def _render_page(
        *,
        name: str = "",
        message: str = "",
        response_text: str = "",
        error_text: str = "",
) -> str:
    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Azure KI Chat</title>
    <style>
      :root {{
        color-scheme: light dark;
        --bg: #0b1020;
        --panel: #111827;
        --card: #0f172a;
        --border: #1f2937;
        --text: #e5e7eb;
        --muted: #94a3b8;
        --accent: #6366f1;
        --accent-strong: #4f46e5;
        --assistant: #1f2a44;
        --user: #1d4ed8;
        --shadow: 0 18px 40px rgba(15, 23, 42, 0.45);
      }}
      body {{
        font-family: "Segoe UI", system-ui, sans-serif;
        margin: 0;
        padding: 32px;
        background: radial-gradient(circle at top, #1e293b 0%, #0b1020 55%);
        color: var(--text);
      }}
      .container {{
        max-width: 980px;
        margin: 0 auto;
        background: var(--panel);
        border-radius: 20px;
        padding: 28px;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: 1.75rem;
      }}
      .subtitle {{
        margin: 0 0 24px;
        color: var(--muted);
      }}
      .chat-shell {{
        display: grid;
        gap: 20px;
      }}
      .chat-window {{
        background: var(--card);
        border-radius: 16px;
        border: 1px solid var(--border);
        padding: 20px;
        min-height: 260px;
        display: grid;
        gap: 16px;
      }}
      .bubble {{
        max-width: 80%;
        padding: 12px 16px;
        border-radius: 18px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.35);
      }}
      .bubble.user {{
        margin-left: auto;
        background: linear-gradient(135deg, var(--accent-strong), var(--user));
      }}
      .bubble.assistant {{
        background: var(--assistant);
        border: 1px solid rgba(148, 163, 184, 0.25);
      }}
      .composer {{
        display: grid;
        gap: 12px;
      }}
      label {{
        font-weight: 600;
      }}
      .input-row {{
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      }}
      input, textarea {{
        width: 100%;
        padding: 12px 14px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: #0b1224;
        color: var(--text);
        font-size: 1rem;
      }}
      textarea {{
        min-height: 110px;
        resize: vertical;
      }}
      button {{
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: #ffffff;
        border: none;
        padding: 12px 20px;
        border-radius: 999px;
        font-weight: 600;
        cursor: pointer;
        width: fit-content;
      }}
      .response-meta {{
        color: var(--muted);
        font-size: 0.9rem;
      }}
      .error {{
        color: #fecaca;
        background: rgba(185, 28, 28, 0.2);
        padding: 12px 14px;
        border-radius: 10px;
        border: 1px solid rgba(248, 113, 113, 0.3);
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>KI Chatfenster</h1>
      <p class="subtitle">Aktuelles LLM-Design mit separatem Antwortbereich.</p>
      <div class="chat-shell">
        <div class="chat-window">
          <div class="bubble user">
            {html.escape(message) if message else "Noch keine Nachricht gesendet."}
          </div>
          <div class="bubble assistant">
            {html.escape(response_text) if response_text else "Noch keine Antwort."}
          </div>
        </div>
        {f"<div class='error'>{html.escape(error_text)}</div>" if error_text else ""}
        <form method="post" action="/submit" class="composer">
          <div class="input-row">
            <div>
              <label for="name">Name</label>
              <input id="name" name="name" type="text" value="{html.escape(name)}" required />
            </div>
            <div>
              <label for="email">E-Mail (optional)</label>
              <input id="email" name="email" type="email" value="" />
            </div>
          </div>
          <div>
            <label for="message">Nachricht</label>
            <textarea id="message" name="message" required>{html.escape(message)}</textarea>
          </div>
          <button type="submit">Senden</button>
          <span class="response-meta">Antworten werden im Chatfenster angezeigt.</span>
        </form>
      </div>
    </div>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def form():
    return _render_page()


@app.post("/submit", response_class=HTMLResponse)
def submit(
        name: str = Form(...),
        email: str = Form(""),  # optional
        message: str = Form(""),
):
    try:
        response_text = ai_communication.get_response(message)
        return _render_page(name=name, message=message, response_text=response_text)
    except Exception as exc:
        # In production you might want to log exc (without leaking secrets) and show a generic message.
        return _render_page(name=name, message=message, error_text=str(exc))
