import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import curriculum, generator
from .docx_builder import build_docx

app = FastAPI(title="منصة المذكرات — التعليم المتوسط", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class GenerateRequest(BaseModel):
    level: int = Field(ge=1, le=4)
    subject: str
    sequence: str = Field(min_length=1, max_length=200)
    lesson: str = Field(min_length=1, max_length=200)
    domain: str | None = None
    duration: str | None = None
    memo_number: str | None = None
    week: str | None = None
    teacher: str | None = None
    school: str | None = None
    class_name: str | None = None
    school_year: str | None = None
    notes: str | None = Field(default=None, max_length=1000)
    text_title: str | None = Field(default=None, max_length=200)


class Phase(BaseModel):
    name: str = ""
    time: str = ""
    activities: list[str] = []
    evaluation: str = ""


class Memo(BaseModel):
    lang: str = "ar"
    level: int | None = None
    level_name: str = ""
    level_short: str = ""
    subject: str = ""
    subject_name: str = ""
    sequence: str = ""
    domain: str = ""
    lesson: str = ""
    duration: str = ""
    memo_number: str = ""
    week: str = ""
    teacher: str = ""
    school: str = ""
    class_name: str = ""
    school_year: str = ""
    target_competency: str = ""
    objectives: list[str] = []
    means: list[str] = []
    phases: list[Phase] = []
    homework: str = ""


class ExportRequest(BaseModel):
    memos: list[Memo] = Field(min_length=1, max_length=60)
    filename: str | None = None


@app.get("/api/health")
def health():
    return {"ok": True, "ai": bool(generator._api_key()), "model": generator.LLM_MODEL}


@app.get("/api/llm-check")
async def llm_check():
    return await generator.check_llm()


@app.get("/api/curriculum")
def get_curriculum():
    return curriculum.summary()


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    try:
        return await generator.generate(req.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/export")
def export(req: ExportRequest):
    memos = [m.model_dump() for m in req.memos]
    data = build_docx(memos)
    base = req.filename or (f"مذكرة - {memos[0]['lesson']}" if len(memos) == 1 else f"مذكرات - {memos[0]['sequence']}")
    base = re.sub(r'[\\/:*?"<>|]+', " ", base).strip()[:80] or f"memo-{date.today()}"
    fname = f"{base}.docx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=memo.docx; filename*=UTF-8''{quote(fname)}"},
    )


# Serve the built React app (frontend/dist copied to backend/static) when present.
STATIC = Path(__file__).resolve().parent.parent / "static"
if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = STATIC / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(STATIC / "index.html")
