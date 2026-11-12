# PRD Genie UI

A small web page for the PRD Genie Langflow workflow. It lets a PM add several files (.txt, .md, .docx, .pdf) or paste text, pick a stage (Analyze, PRD, Stories), run it, review the result, and send it to the next stage.

The page talks to a tiny local server (`app.py`). The server reads the files, puts the mode tag first, calls Langflow and returns the text. The Langflow API key stays on the server and never reaches the browser.

## 1. Prepare a copy of the flow for the API

The UI reads the files itself and sends plain text, so the flow does not need the file nodes.

1. In Langflow, duplicate `prd-genie` and name the copy `prd-genie-api`.
2. In the copy, delete **Read File**, **Parser** and **Input Combiner**.
3. Connect **Chat Input** to the **Text Input** of `Mode: Analyze` (where Input Combiner used to go).
4. Nothing else changes: no prompts, no models.
5. Check it in the Playground: send `ANALYZE:` followed by a line of notes. The Analyze output should appear.

## 2. Find the flow id

Open the flow. The address bar shows `.../flow/<flow-id>`. Copy that id. If your Langflow asks for an API key, create one in Settings and copy it.

## 3. Configure

Copy `.env.example` to `.env`.

- To check the page without Langflow, keep `STUB=1`. It returns sample output and calls no model.
- To use the real flow, set `STUB=0`, `LANGFLOW_URL` (the address Langflow runs on), `LANGFLOW_FLOW_ID`, and `LANGFLOW_API_KEY` if needed.

Never commit `.env`. It is listed in `.gitignore`.

## 4. Run

- Windows: double-click `start.bat`, or run it in a terminal.
- Mac or Linux: `./start.sh`

Open http://127.0.0.1:8000.

## 5. Use

1. Pick **Analyze**. Paste notes or add files, then run.
2. Review the extraction and the gap questions. Fix anything wrong.
3. **Send extraction to PRD** moves the extraction into the PRD stage. To answer a gap question, add a `PM CLARIFICATIONS` section at the end of the text.
4. Run **PRD**, review, then **Send PRD to Stories**, and run **Stories**.

Tags in the output show where each item came from: `[FROM PRD]`, `[FROM PM]`, `[DERIVED]` and `[DRAFT]`.

## Limits

- Each run is independent. The PM carries the approved output from one stage to the next, which is the sign-off step.
- Scanned PDFs have no text layer and need OCR first.
- Input is capped at 200,000 characters (`MAX_CHARS`).
- The Human Input pause and the questions step are not part of this UI.
