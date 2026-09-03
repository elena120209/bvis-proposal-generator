import base64, subprocess, tempfile, os, uuid
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import filler

app = FastAPI(title="BVIS Proposal Generator")

class Proposal(BaseModel):
    event: Optional[str]=None; committee: Optional[str]=None; leads: Optional[str]=None
    month: Optional[str]=None; year: Optional[str]=None
    date: Optional[str]=None; location: Optional[str]=None
    activities: Optional[List[str]]=None; why: Optional[List[str]]=None
    allowed: Optional[List[str]]=None; notallowed: Optional[List[str]]=None
    act1_name: Optional[str]=None; act2_name: Optional[str]=None
    act1_participate: Optional[List[str]]=None; act1_prizes: Optional[List[str]]=None
    act2_participate: Optional[List[str]]=None; act2_prizes: Optional[List[str]]=None
    hall: Optional[str]=None; timeline: Optional[List[str]]=None
    apikey: Optional[str]=None

API_KEY = os.environ.get("GEN_API_KEY","")  # optional shared secret

def to_pdf(pptx_bytes: bytes) -> bytes:
    d = tempfile.mkdtemp()
    pptx = os.path.join(d, "in.pptx"); open(pptx,"wb").write(pptx_bytes)
    # Per-call LibreOffice profile in a writable temp dir. This avoids the
    # "profile locked" / non-writable-HOME failures that otherwise hit on
    # sandboxed hosts and lets concurrent calls run.
    profile = os.path.join(d, "loprofile")
    env = dict(os.environ, HOME=d)
    subprocess.run(
        ["soffice", f"-env:UserInstallation=file://{profile}",
         "--headless", "--convert-to", "pdf", "--outdir", d, pptx],
        check=True, timeout=120, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = os.path.join(d,"in.pdf")
    return open(pdf,"rb").read()

def _split(s):
    """Turn a pipe- or newline-delimited string into a clean list."""
    if not s: return []
    s = s.replace("\r","")
    parts = s.split("|") if "|" in s else s.split("\n")
    return [x.strip() for x in parts if x.strip()]

def _build(event="", committee="", month="", year="", date="", location="",
           activities="", why="", timeline="",
           act1_name="", act2_name="",
           act1_participate="", act1_prizes="",
           act2_participate="", act2_prizes=""):
    data = {
        "event": event or None, "committee": committee or None,
        "month": month or None, "year": year or None,
        "date": date or None, "location": location or None,
        "act1_name": act1_name or None, "act2_name": act2_name or None,
        "activities": _split(activities), "why": _split(why), "timeline": _split(timeline),
        "act1_participate": _split(act1_participate), "act1_prizes": _split(act1_prizes),
        "act2_participate": _split(act2_participate), "act2_prizes": _split(act2_prizes),
    }
    return {k: v for k, v in data.items() if v}

@app.get("/")
def health(): return {"ok": True, "service":"bvis-proposal-generator"}

@app.post("/generate")
def generate(p: Proposal):
    if API_KEY and p.apikey != API_KEY:
        return JSONResponse({"error":"unauthorized"}, status_code=401)
    data = {k:v for k,v in p.dict().items() if v is not None and k!="apikey"}
    pptx = filler.fill(data)
    pdf = to_pdf(pptx)
    return {
        "pptx_base64": base64.b64encode(pptx).decode(),
        "pdf_base64": base64.b64encode(pdf).decode(),
        "filename": (data.get("event","proposal").replace(" ","_"))
    }

# --- Browser-friendly GET routes: open a URL, get a file download. -----------
# These let a Power Apps button do Launch("<url>/pdf?event=...&committee=...")
# with NO premium connector. Lists are passed pipe-delimited, e.g.
#   activities=Pumpkin%20%26%20Pins|Snatch%20the%20Donut
def _file_response(fmt, event, committee, month, year, date, location,
                   activities, why, timeline, act1_name, act2_name,
                   act1_participate, act1_prizes, act2_participate, act2_prizes):
    data = _build(event, committee, month, year, date, location,
                  activities, why, timeline, act1_name, act2_name,
                  act1_participate, act1_prizes, act2_participate, act2_prizes)
    pptx = filler.fill(data)
    fname = (event or "proposal").replace(" ", "_")
    if fmt == "pptx":
        return Response(
            pptx,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{fname}.pptx"'})
    pdf = to_pdf(pptx)
    return Response(
        pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}.pdf"'})

@app.get("/pdf")
def pdf_get(event: str="", committee: str="", month: str="", year: str="",
            date: str="", location: str="", activities: str="", why: str="",
            timeline: str="", act1_name: str="", act2_name: str="",
            act1_participate: str="", act1_prizes: str="",
            act2_participate: str="", act2_prizes: str=""):
    return _file_response("pdf", event, committee, month, year, date, location,
                          activities, why, timeline, act1_name, act2_name,
                          act1_participate, act1_prizes, act2_participate, act2_prizes)

@app.get("/pptx")
def pptx_get(event: str="", committee: str="", month: str="", year: str="",
             date: str="", location: str="", activities: str="", why: str="",
             timeline: str="", act1_name: str="", act2_name: str="",
             act1_participate: str="", act1_prizes: str="",
             act2_participate: str="", act2_prizes: str=""):
    return _file_response("pptx", event, committee, month, year, date, location,
                          activities, why, timeline, act1_name, act2_name,
                          act1_participate, act1_prizes, act2_participate, act2_prizes)
