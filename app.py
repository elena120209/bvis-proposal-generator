import base64, subprocess, tempfile, os, uuid
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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
    hall: Optional[str]=None; timeline: Optional[List[str]]=None
    apikey: Optional[str]=None

API_KEY = os.environ.get("GEN_API_KEY","")  # optional shared secret

def to_pdf(pptx_bytes: bytes) -> bytes:
    d = tempfile.mkdtemp()
    pptx = os.path.join(d, "in.pptx"); open(pptx,"wb").write(pptx_bytes)
    # Per-call LibreOffice profile in a writable temp dir. This avoids the
    # "profile locked" / non-writable-HOME failures that otherwise hit on
    # sandboxed hosts (e.g. Hugging Face Spaces) and lets concurrent calls run.
    profile = os.path.join(d, "loprofile")
    env = dict(os.environ, HOME=d)
    subprocess.run(
        ["soffice", f"-env:UserInstallation=file://{profile}",
         "--headless", "--convert-to", "pdf", "--outdir", d, pptx],
        check=True, timeout=120, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = os.path.join(d,"in.pdf")
    return open(pdf,"rb").read()

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
