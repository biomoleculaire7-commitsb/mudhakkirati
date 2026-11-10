"""Lesson-plan (مذكرة) generation: LLM (OpenAI-compatible, Groq by default) with an offline template fallback."""
import asyncio
import json
import logging
import os
import re

import httpx

from . import curriculum

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "8000"))
log = logging.getLogger("mudhakkira.llm")
logging.basicConfig(level=logging.INFO)


def _api_key() -> str | None:
    return os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")


LANG_NAMES = {"ar": "العربية الفصحى", "fr": "le français", "en": "English"}

SYSTEM_PROMPT = """أنت مفتش ومكوّن خبير في التعليم المتوسط الجزائري، تُعِدّ مذكرات (بطاقات تربوية) وفق مناهج الجيل الثاني
لوزارة التربية الوطنية الجزائرية، بالمقاربة بالكفاءات والوضعية المشكلة، كما يُعِدّها أستاذ متمرّس.
قواعد صارمة:
- احترم البرنامج الرسمي ومستوى التلاميذ، ولا تتجاوز محتوى المستوى المحدد.
- كل مرحلة تحتوي على نشاطات ملموسة: أسئلة الأستاذ وإجابات التلاميذ المتوقعة (ج: ...)، أمثلة وتمارين بقيم عددية حقيقية عند الحاجة.
- الوضعية الانطلاقية مستمدة من محيط التلميذ الجزائري.
- التقويم في كل مرحلة: تشخيصي في البداية، تكويني (مرحلي) أثناء البناء، ختامي في إعادة الاستثمار.
- مجموع أزمنة المراحل يساوي مدة الحصة.
- أجب بكائن JSON صالح فقط، دون أي نص خارجه."""

JSON_SHAPE = """{
  "target_competency": "الكفاءة الختامية أو الكفاءة المستهدفة",
  "objectives": ["مؤشر/هدف تعلمي 1", "..."],
  "means": ["الكتاب المدرسي ص ..", "السبورة", "..."],
  "phases": [
    {
      "name": "اسم المرحلة",
      "time": "10 د",
      "activities": ["فقرة 1 من سير النشاط", "سؤال: ... ج: ...", "..."],
      "evaluation": "نوع التقويم: ما يقوم به المتعلم"
    }
  ],
  "homework": "واجب منزلي أو نشاط مقترح (اختياري)"
}"""


def find_official(subject: dict, level_id: int, sequence: str, lesson: str):
    """Return (official dict | None, lesson hint | None, guidelines | None) from the curriculum."""
    seqs = subject.get("levels", {}).get(str(level_id), [])
    seq = next((x for x in seqs if x.get("title") == sequence), None)
    hint = None
    if seq:
        for l in seq.get("lessons", []):
            if isinstance(l, dict) and l.get("title") == lesson:
                hint = l.get("hint")
    return (seq or {}).get("official"), hint, subject.get("guidelines", {}).get(str(level_id))


def official_block(off: dict, hint: str | None, guide: str | None) -> str:
    lines = [f"\n— مرجع رسمي ({off['source']}) — التزم به حرفياً عند صياغة الأهداف والموارد والتقويم:"]
    lines.append("المستويات المستهدفة من الكفاءات الختامية:")
    lines += [f"  • {k}: {v}" for k, v in off["levels"].items()]
    lines.append("هيكلة الموارد المعرفية المستهدفة:")
    lines += [f"  • {k}: {v}" for k, v in off["resources"].items()]
    lines.append(f"الوضعية الانطلاقية: {off['situation']}")
    lines.append("المهمات: " + "؛ ".join(off["tasks"]))
    lines.append("معايير ومؤشرات التقويم: " + "؛ ".join(off["criteria"]))
    if guide:
        lines.append(f"توجيهات منهجية: {guide}")
    if hint:
        lines.append(f"خصوصية هذه الحصة: {hint}")
    return "\n".join(lines)


def build_prompt(req: dict, subject: dict, level: dict) -> str:
    lang = subject["lang"]
    phases = " ← ".join(subject["phases"])
    out_lang = LANG_NAMES[lang]
    parts = [
        f"المستوى: {level['name']}",
        f"المادة: {subject['name']}",
        f"المقطع التعلمي: {req['sequence']}",
        f"الميدان: {req.get('domain') or 'حدده المناسب من: ' + '، '.join(subject['domains'])}",
        f"المحتوى المعرفي (الدرس): {req['lesson']}",
        f"مدة الحصة: {req.get('duration') or subject['hours']}",
        f"المراحل المطلوبة بالترتيب: {phases}",
    ]
    if req.get("text_title"):
        parts.append(f"السند / عنوان النص من الكتاب المدرسي: {req['text_title']}")
    if req.get("notes"):
        parts.append(f"توجيهات الأستاذ: {req['notes']}")
    off, hint, guide = find_official(subject, level["id"], req["sequence"], req["lesson"])
    if off:
        parts.append(official_block(off, hint, guide))
        parts.append("هذه الحصة تتناول المحتوى المعرفي المذكور أعلاه فقط من بين موارد المقطع؛ لا تتجاوزه إلى موارد أخرى، واستعمل صياغة المخطط الرسمي في الأهداف والتقويم.")
    elif hint:
        parts.append(f"خصوصية هذه الحصة: {hint}")
    return (
        "\n".join(parts)
        + f"\n\nاكتب كامل محتوى المذكرة بـ {out_lang}"
        + (" (المادة تُدرَّس بهذه اللغة)." if lang != "ar" else ".")
        + "\nاجعل سير الحصة مفصلاً وقابلاً للتطبيق في القسم مباشرة (8 إلى 15 فقرة في مرحلة بناء التعلمات)."
        + f"\nأعد JSON بهذا الشكل بالضبط:\n{JSON_SHAPE}"
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model output")
    return json.loads(m.group(0), strict=False)  # tolerate raw newlines inside Arabic strings


class LLMError(Exception):
    pass


def _explain(status: int, text: str) -> str:
    """Short Arabic explanation of an API error, kept with the raw detail for debugging."""
    detail = text[:300]
    if status == 401:
        return f"مفتاح API غير صالح أو ملغى (401). أنشئ مفتاحاً جديداً. التفاصيل: {detail}"
    if status == 429:
        return f"تجاوزت حد الطلبات المسموح به مؤقتاً (429). انتظر دقيقة ثم أعد المحاولة. التفاصيل: {detail}"
    if status == 413:
        return f"الطلب أطول من الحد المسموح به لهذا النموذج (413). التفاصيل: {detail}"
    return f"خطأ من خدمة الذكاء الاصطناعي ({status}). التفاصيل: {detail}"


async def _post(client: httpx.AsyncClient, body: dict) -> httpx.Response:
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    for attempt in range(3):
        r = await client.post(f"{LLM_BASE_URL}/chat/completions", headers=headers, json=body)
        if r.status_code != 429 or attempt == 2:
            return r
        # rate limited: wait as told by the API (bounded), then retry
        try:
            wait = float(r.headers.get("retry-after", "8"))
        except ValueError:
            wait = 8.0
        await asyncio.sleep(min(max(wait, 2.0), 20.0))
    return r


async def _call_llm(prompt: str) -> dict:
    base = {
        "model": LLM_MODEL,
        "temperature": 0.5,
        "max_tokens": LLM_MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=120) as client:
        # 1st try: strict JSON mode. If the provider rejects the output (e.g. long Arabic text cut off ->
        # json_validate_failed), retry once in plain mode and parse the JSON ourselves.
        r = await _post(client, {**base, "response_format": {"type": "json_object"}})
        if r.status_code == 400 and ("json" in r.text.lower() or "validate" in r.text.lower()):
            log.warning("JSON mode rejected, retrying without response_format: %s", r.text[:300])
            r = await _post(client, base)
        if r.status_code >= 400:
            log.error("LLM HTTP %s: %s", r.status_code, r.text[:500])
            raise LLMError(_explain(r.status_code, r.text))
        choice = r.json()["choices"][0]
        content = choice["message"]["content"] or ""
        try:
            return _extract_json(content)
        except (ValueError, json.JSONDecodeError) as exc:
            log.error("Unparseable LLM output (finish_reason=%s): %s", choice.get("finish_reason"), content[:500])
            if choice.get("finish_reason") == "length":
                raise LLMError("انقطع رد النموذج لطوله قبل اكتمال المذكرة. أعد المحاولة أو اختصر التوجيهات.") from exc
            raise LLMError("ردّ النموذج بصيغة غير صالحة. أعد المحاولة.") from exc


async def check_llm() -> dict:
    """Tiny real request to the provider, to diagnose deployment problems from the browser."""
    if not _api_key():
        return {"ok": False, "error": "لا يوجد مفتاح GROQ_API_KEY في متغيرات البيئة."}
    body = {"model": LLM_MODEL, "max_tokens": 5, "messages": [{"role": "user", "content": "قل: نعم"}]}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await _post(client, body)
        if r.status_code >= 400:
            return {"ok": False, "status": r.status_code, "error": _explain(r.status_code, r.text)}
        return {"ok": True, "model": LLM_MODEL, "reply": r.json()["choices"][0]["message"]["content"]}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:300]}"}


def _fallback(req: dict, subject: dict) -> dict:
    """Structured skeleton when no API key is configured — the teacher completes it in the editor."""
    lesson, lang = req["lesson"], subject["lang"]
    if lang == "fr":
        return {
            "target_competency": f"L'apprenant est capable de mobiliser ses acquis relatifs à « {lesson} » dans une situation de communication.",
            "objectives": [f"Identifier les caractéristiques de : {lesson}", "Réinvestir les acquis à l'écrit et à l'oral"],
            "means": ["Manuel scolaire", "Tableau", "Supports visuels"],
            "phases": [
                {"name": p, "time": t, "activities": [a], "evaluation": e}
                for p, t, a, e in zip(subject["phases"], ["10 min", "35 min", "15 min"],
                                      ["Présentation de la situation-problème et émission d'hypothèses.",
                                       f"Observation du support, questions de compréhension et découverte de la notion : {lesson}.",
                                       "Exercice d'application individuel puis correction collective."],
                                      ["Diagnostique", "Formative", "Sommative"])
            ],
            "homework": "Exercice du manuel.",
        }
    if lang == "en":
        return {
            "target_competency": f"The learner can interact, interpret and produce messages related to: {lesson}.",
            "objectives": [f"By the end of the lesson, learners will be able to use: {lesson}"],
            "means": ["Textbook", "Board", "Flashcards"],
            "phases": [
                {"name": p, "time": t, "activities": [a], "evaluation": e}
                for p, t, a, e in zip(subject["phases"], ["10 min", "35 min", "15 min"],
                                      ["Warm-up: questions and pictures to elicit prior knowledge.",
                                       f"Presentation and practice of: {lesson}.",
                                       "Production task in pairs, then feedback."],
                                      ["Diagnostic", "Formative", "Summative"])
            ],
            "homework": "Textbook exercise.",
        }
    off, hint, _ = find_official(subject, int(req["level"]), req["sequence"], lesson)
    n = len(subject["phases"])
    times = {3: ["10 د", "35 د", "15 د"], 4: ["10 د", "25 د", "10 د", "15 د"]}.get(n, ["10 د"] * n)
    acts = {
        0: f"عرض الوضعية المشكلة الانطلاقية المرتبطة بالمقطع «{req['sequence']}» ومناقشتها وطرح الفرضيات.",
        1: f"نشاطات بناء التعلمات حول «{lesson}»: ملاحظة السند، أسئلة موجهة، استنتاجات جزئية.",
    }
    evals = ["تشخيصي: يستحضر مكتسباته القبلية", "تكويني: يشارك ويجيب ويصحح أخطاءه", "تكويني: يصوغ الاستنتاج", "ختامي: يوظف ما تعلمه في وضعية جديدة"]
    phases = []
    for i, p in enumerate(subject["phases"]):
        last = i == n - 1
        phases.append({
            "name": p, "time": times[i],
            "activities": [acts.get(i, "تمرين تطبيقي فردي ثم تصحيح جماعي." if last else f"حوصلة المعارف المتعلقة بـ «{lesson}» وتدوينها على الكراريس.")],
            "evaluation": evals[-1] if last else evals[min(i, 2)],
        })
    if off:
        dom = req.get("domain") or ""
        key = next((k for k in off["levels"] if k.split()[-1] in dom or k in dom), None)
        if "إنتاج" in dom:
            key = "الإنتاج الكتابي"
        target = off["levels"].get(key) if key else (off["levels"].get("الكفاءة الختامية") or " ".join(off["levels"].values()))
        if hint:
            phases[0]["activities"].append(hint)
        return {
            "target_competency": target,
            "objectives": off["tasks"][:3] if not off["levels"].get("الكفاءة الختامية") else [f"يتعرف على {lesson} ويوظفه", "يحل مشكلات بسيطة ومركبة متعلقة بموارد المقطع"],
            "means": ["الكتاب المدرسي", "دليل الأستاذ", "السبورة"],
            "phases": phases,
            "homework": "تمرين من الكتاب المدرسي.",
        }
    return {
        "target_competency": f"يتحكم المتعلم في الموارد المتعلقة بـ «{lesson}» ويوظفها في حل وضعيات مشكلة.",
        "objectives": [f"يتعرف على {lesson}", f"يوظف {lesson} في وضعيات متنوعة"],
        "means": ["الكتاب المدرسي", "دليل الأستاذ", "السبورة"],
        "phases": phases,
        "homework": "تمرين من الكتاب المدرسي.",
    }


async def generate(req: dict) -> dict:
    subject = curriculum.get_subject(req["subject"])
    level = curriculum.get_level(int(req["level"]))
    if not subject or not level:
        raise ValueError("مادة أو مستوى غير معروف")

    source = "template"
    content = None
    if _api_key():
        try:
            content = await _call_llm(build_prompt(req, subject, level))
            source = "ai"
        except LLMError as exc:
            content = None
            req["_error"] = str(exc)
        except Exception as exc:  # network errors etc. → fall back, but tell the UI
            log.exception("LLM call failed")
            content = None
            req["_error"] = f"تعذر الاتصال بخدمة الذكاء الاصطناعي: {type(exc).__name__}: {str(exc)[:200]}"
    if content is None:
        content = _fallback(req, subject)
        off, _, _ = find_official(subject, level["id"], req["sequence"], req["lesson"])
        if off and subject["lang"] != "ar":
            content["target_competency"] = next(iter(off["levels"].values()))
            content["objectives"] = off["criteria"][:3]

    return {
        "lang": subject["lang"],
        "level": level["id"],
        "level_name": level["name"],
        "level_short": level["short"] if subject["lang"] == "ar" else level["fr"],
        "subject": subject["id"],
        "subject_name": {"fr": "Français", "en": "English"}.get(subject["lang"], subject["name"]),
        "sequence": req["sequence"],
        "domain": req.get("domain") or "",
        "lesson": req["lesson"] + (f" — {req['text_title']}" if req.get("text_title") else ""),
        "official_source": (find_official(subject, level["id"], req["sequence"], req["lesson"])[0] or {}).get("source"),
        "duration": req.get("duration") or subject["hours"],
        "memo_number": req.get("memo_number") or "1",
        "week": req.get("week") or "",
        "teacher": req.get("teacher") or "",
        "school": req.get("school") or "",
        "class_name": req.get("class_name") or "",
        "school_year": req.get("school_year") or "",
        "target_competency": content.get("target_competency", ""),
        "objectives": [str(x) for x in content.get("objectives", [])],
        "means": [str(x) for x in content.get("means", [])],
        "phases": [
            {
                "name": str(p.get("name", "")),
                "time": str(p.get("time", "")),
                "activities": [str(a) for a in (p.get("activities") or [])],
                "evaluation": str(p.get("evaluation", "")),
            }
            for p in content.get("phases", [])
        ],
        "homework": content.get("homework", ""),
        "source": source,
        "error": req.get("_error"),
    }
