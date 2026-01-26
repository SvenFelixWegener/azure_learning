from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

FORM_HTML = """<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Azure Lern-Formular</title>
  </head>
  <body>
    <h1>Willkommen</h1>
    <p>Bitte gib deine Daten ein:</p>
    <form method="post" action="/submit">
      <label for="name">Name</label>
      <input id="name" name="name" type="text" required />
      <br />
      <label for="email">E-Mail</label>
      <input id="email" name="email" type="email" required />
      <br />
      <label for="message">Nachricht</label>
      <textarea id="message" name="message" rows="4" cols="40"></textarea>
      <br />
      <button type="submit">Absenden</button>
    </form>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def form():
    return FORM_HTML


@app.post("/submit", response_class=HTMLResponse)
def submit():
    return "<p>Danke! Dein Formular wurde gesendet.</p><a href='/'>Zurück</a>"