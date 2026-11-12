"""PRD Genie UI: a small backend for the Langflow workflow.

It serves the page, reads the uploaded files (txt, md, docx, pdf), puts the
mode tag first, calls the Langflow run API and returns the text. The API key
stays here on the server and never reaches the browser.
"""
import asyncio
import io
import os
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

BASE = Path(__file__).parent


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env(BASE / ".env")

LANGFLOW_URL = os.getenv("LANGFLOW_URL", "http://127.0.0.1:7860").rstrip("/")
FLOW_ID = os.getenv("LANGFLOW_FLOW_ID", "").strip()
API_KEY = os.getenv("LANGFLOW_API_KEY", "").strip()
STUB = os.getenv("STUB", "0").strip() == "1"
MAX_CHARS = int(os.getenv("MAX_CHARS", "200000"))
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "300"))

TAGS = {"analyze": "ANALYZE:", "prd": "PRD:", "stories": "STORIES:"}
TEXT_EXT = {".txt", ".md", ".csv", ".json", ".log"}

app = FastAPI(title="PRD Genie UI")


# ---------- reading files ----------

def read_docx(data: bytes) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(io.BytesIO(data))
    parts = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = Paragraph(child, doc).text.strip()
            if text:
                parts.append(text)
        elif tag == "tbl":
            for row in Table(child, doc).rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
    return "\n".join(parts)


def read_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()


def extract_text(name: str, data: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext in TEXT_EXT:
        return data.decode("utf-8-sig", errors="replace")
    if ext == ".docx":
        return read_docx(data)
    if ext == ".pdf":
        return read_pdf(data)
    raise ValueError(f"Unsupported file type {ext or '(none)'}. Use .txt, .md, .docx or .pdf.")


# ---------- reading the Langflow response ----------

def dig(obj, *keys):
    for key in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def pick_text(data) -> str:
    """Collect the text of every output node that produced something.

    Branches that did not run come back empty, so normally one text is found.
    """
    seen, texts = set(), []
    for run in (data or {}).get("outputs", []) or []:
        for item in run.get("outputs", []) or []:
            candidates = (
                dig(item, "results", "message", "text"),
                dig(item, "outputs", "message", "message"),
                dig(item, "artifacts", "message"),
            )
            for cand in candidates:
                if isinstance(cand, str) and cand.strip() and cand.strip() not in seen:
                    seen.add(cand.strip())
                    texts.append(cand.strip())
                    break
    return "\n\n---\n\n".join(texts)


# ---------- stub (no model call) ----------

STUB_NOTE = "> STUB MODE: sample output, no model was called.\n\n"

STUB_OUTPUT = {
    "analyze": STUB_NOTE + """## Extraction
{"sufficiency":"SUFFICIENT","sufficiency_reason":"The input contains clear and testable requirements.","source_type":"transcript","stated_requirements":[{"id":"REQ-001","type":"functional","text":"The user should be able to filter reports by date range, category, and status.","verbatim_quote":"The user should be able to filter reports by date range, category, and status.","speaker":"UNKNOWN","priority_signal":"UNKNOWN"},{"id":"REQ-002","type":"non_functional","text":"Results must load in under 2 seconds.","verbatim_quote":"Results must load in under 2 seconds.","speaker":"UNKNOWN","priority_signal":"UNKNOWN"}],"acceptance_criteria":[],"stakeholders":[{"name":"Sarah","role":"PM","viewpoint":"UNKNOWN"}],"deadlines":[{"item":"Project Deadline","date":"Q3"}],"dependencies":[],"assumptions_stated":[],"ambiguous_items":[],"contradictions":[],"risks":[]}

## Gaps and questions
{"gaps":[],"summary":"There are no gaps identified in the extraction. All stated requirements are clear and sufficient."}""",
    "prd": STUB_NOTE + """# Product Requirements Document
## 1. Product Overview
- Product Name: Not specified in source
- Document Version: 1.0
- Author: AI-generated draft for PM review (PM owner: Sarah)
- Date: 2026-10-26
- Status: Draft
## 2. Goals and Objectives
- Business Goal: Not specified in source
- User Goal: Not specified in source
- Success Metrics: Not specified in source
## 3. User Personas
Name / Role: User, Key Need: Not specified in source, Current Workaround: Not specified in source
## 4. Feature Requirements
### 4.1 Functional Requirements
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-001 | The user should be able to filter reports by date range, category, and status. | Unprioritized | REQ-001 |
### 4.2 Non-Functional Requirements
| ID | Requirement | Category | Target |
|----|-------------|----------|--------|
| NFR-001 | Results must load in under 2 seconds. | Performance | under 2 seconds (REQ-002) |
## 5. Acceptance Criteria
None stated in source
## 6. Out of Scope
Not specified in source
## 7. Dependencies
None stated in source
## 8. Assumptions
Not specified in source
## 9. Open Questions
None stated in source.
## 10. Timeline
| Milestone | Target Date |
|-----------|-------------|
| Design Complete | Not specified in source |
| Development Start | Not specified in source |
| QA / Testing | Not specified in source |
| Launch | Not specified in source |
Other deadlines (as stated): Project Deadline Q3""",
    "stories": STUB_NOTE + """## Epic E1: Report Filtering
### Feature F1.1: Filter reports
#### Story S1.1.1: Filter by date range
**Review status:** DRAFT, pending PM review
**Origin:** PRD requirement FR-001

**Story Description:**
As a User, I want to filter reports by date range, so that [DRAFT] I can view reports for a specific period.

**Priority (suggested):** Should Have | No priority signal in source; suggested only.

**Business Rules:**
- [DRAFT] Input: Users can type a date or pick it from a calendar.
- [DRAFT] Validation: The From date cannot be later than the To date.

**Acceptance Criteria:**
- AC-1 [DERIVED] Given: reports are available to filter
  When: the user selects a date range
  Then: the system displays reports within the selected range.

**NFRs:** NFR-001: Results must load in under 2 seconds.

**Source:** FR-001

**INVEST flags:** V: benefit not stated in source

## Blocked / Needs clarification
None stated in source""",
}


# ---------- calling Langflow ----------

async def call_langflow(message: str) -> str:
    if not FLOW_ID:
        raise HTTPException(500, "LANGFLOW_FLOW_ID is not set. Add it to .env (see the README).")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["x-api-key"] = API_KEY
    payload = {"input_value": message, "input_type": "chat", "output_type": "chat"}
    url = f"{LANGFLOW_URL}/api/v1/run/{FLOW_ID}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, params={"stream": "false"}, headers=headers, json=payload)
    except httpx.ConnectError:
        raise HTTPException(502, f"Cannot reach Langflow at {LANGFLOW_URL}. Start Langflow, then check LANGFLOW_URL in .env.")
    except httpx.TimeoutException:
        raise HTTPException(504, "Langflow took too long to answer. Try a shorter input, or raise REQUEST_TIMEOUT in .env.")

    body = resp.text or ""
    if resp.status_code in (401, 403):
        raise HTTPException(502, "Langflow rejected the API key. Check LANGFLOW_API_KEY in .env.")
    if resp.status_code == 404:
        raise HTTPException(502, "Langflow has no flow with that id. Check LANGFLOW_FLOW_ID in .env.")
    if resp.status_code >= 400:
        hint = ""
        low = body.lower()
        if "insufficient_quota" in low or "exceeded your current quota" in low:
            hint = " OpenAI reports that the account has no credit left."
        raise HTTPException(502, f"Langflow returned {resp.status_code}.{hint} Details: {body[:400]}")

    text = pick_text(resp.json())
    if not text:
        raise HTTPException(
            502,
            "Langflow ran but returned no text. Check that the flow starts from Chat Input and that its output nodes ran.",
        )
    return text


# ---------- routes ----------

@app.get("/")
async def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/status")
async def status():
    info = {"stub": STUB, "langflow_url": LANGFLOW_URL, "flow_configured": bool(FLOW_ID), "reachable": None}
    if not STUB:
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                resp = await client.get(f"{LANGFLOW_URL}/health")
                info["reachable"] = resp.status_code < 500
        except Exception:
            info["reachable"] = False
    return info


@app.post("/api/run")
async def run(
    mode: str = Form(...),
    text: str = Form(""),
    files: list[UploadFile] = File(default=[]),
):
    if mode not in TAGS:
        raise HTTPException(400, "Unknown stage. Choose Analyze, PRD or Stories.")

    typed = text.strip()
    blocks, report = [], []
    for upload in files:
        name = upload.filename or "file"
        data = await upload.read()
        try:
            content = extract_text(name, data).strip()
        except Exception as exc:  # unreadable or unsupported file
            report.append({"name": name, "ok": False, "note": str(exc)})
            continue
        if not content:
            report.append({"name": name, "ok": False, "note": "No readable text found. A scanned PDF needs OCR first."})
            continue
        blocks.append((name, content))
        report.append({"name": name, "ok": True, "chars": len(content)})

    sources = len(blocks) + (1 if typed else 0)
    if sources == 0:
        detail = "Nothing to send. Paste text or add at least one readable file."
        failed = [r for r in report if not r["ok"]]
        if failed:
            detail += " " + " ".join(f"{r['name']}: {r['note']}" for r in failed)
        raise HTTPException(400, detail)

    parts = [typed] if typed else []
    for name, content in blocks:
        parts.append(f"--- File: {name} ---\n{content}" if sources > 1 else content)
    body = "\n\n".join(parts)
    if len(body) > MAX_CHARS:
        raise HTTPException(413, f"The input is {len(body):,} characters, over the limit of {MAX_CHARS:,}. Split it or raise MAX_CHARS in .env.")

    message = f"{TAGS[mode]}\n\n{body}"
    started = time.time()
    if STUB:
        await asyncio.sleep(1.0)
        output = STUB_OUTPUT[mode]
    else:
        output = await call_langflow(message)

    return {
        "output": output,
        "seconds": round(time.time() - started, 1),
        "chars_sent": len(message),
        "files": report,
        "preview": message[:3000],
        "stub": STUB,
    }
