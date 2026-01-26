import html
import importlib.util
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()


def _render_page(
    *,
    name: str = "",
    response_text: str = "",
    error_text: str = "",
) -> str:
    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Azure Chat Client</title>
    <style>
      :root {{
        color-scheme: light dark;
      }}
      body {{
        font-family: "Segoe UI", system-ui, sans-serif;
        margin: 0;
        padding: 32px;
        background: #f5f7fb;
        color: #1f2937;
      }}
      .container {{
        max-width: 900px;
        margin: 0 auto;
        background: #ffffff;
        border-radius: 16px;
        padding: 24px 28px;
        box-shadow: 0 18px 40px rgba(31, 41, 55, 0.12);
      }}
      h1 {{
        margin-top: 0;
      }}
      .grid {{
        display: grid;
        gap: 16px;
      }}
      label {{
        font-weight: 600;
      }}
      input, textarea {{
        width: 100%;
        padding: 10px 12px;
        border-radius: 8px;
        border: 1px solid #d1d5db;
        font-size: 1rem;
      }}
      textarea {{
        min-height: 120px;
        resize: vertical;
      }}
      button {{
        background: #2563eb;
        color: #ffffff;
        border: none;
        padding: 12px 18px;
        border-radius: 999px;
        font-weight: 600;
        cursor: pointer;
        width: fit-content;
      }}
      .response {{
        background: #f3f4f6;
        border-radius: 12px;
        padding: 16px;
        white-space: pre-wrap;
      }}
      .error {{
        color: #b91c1c;
        background: #fee2e2;
        padding: 12px;
        border-radius: 8px;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Azure Chat Client</h1>
      <p>Kommuniziere mit der KI über das Eingabefeld.</p>
      <form method="post" action="/submit" class="grid">
        <div class="grid">
          <label for="name">Name</label>
          <input id="name" name="name" type="text" value="{html.escape(name)}" required />
        </div>
        <div class="grid">
          <label for="email">E-Mail</label>
          <input id="email" name="email" type="email" required />
        </div>
        <div class="grid">
          <label for="message">Nachricht</label>
          <textarea id="message" name="message" required></textarea>
        </div>
        <button type="submit">Absenden</button>
      </form>
      <h2>Antwort</h2>
      {f"<div class='error'>{html.escape(error_text)}</div>" if error_text else ""}
      <div class="response">{html.escape(response_text) if response_text else "Noch keine Antwort."}</div>
    </div>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def form():
    return _render_page()


def _load_azure_communication():
    module_path = Path(__file__).with_name("azure-communication.py")
    spec = importlib.util.spec_from_file_location("azure_communication", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load azure-communication module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@app.post("/submit", response_class=HTMLResponse)
def submit(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(""),
):
    azure_module = _load_azure_communication()
    try:
        response_text = azure_module.get_chat_response(message)
        return _render_page(name=name, response_text=response_text)
    except ValueError as exc:
        return _render_page(name=name, error_text=str(exc))
