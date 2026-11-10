"""Official English sequences MS1–MS4 from the Ministry's annual plans (septembre 2022).
One-off builder: python -m app.data.english_official path/to/english1am.pdf ... english4am.pdf
(The PDFs' column layout is interleaved, so each sequence's official block is stored as raw reference text for the generator.)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SRC = "Annual plan — English MS{n}, Ministry of National Education (September 2022)"

TITLES = {
    1: ["Me and my Friends", "Me and my Family", "Me and my Daily Activities", "Me and my School", "Me, my Country and the World"],
    2: ["Me, my Friends and my Family", "Me and my Shopping", "Me and my Health", "Me and my Travels"],
    3: ["Me, My Abilities, My Interests and My Personality", "Me and My Lifestyles", "Me and the Scientific World", "Me and My Environment"],
    4: ["Me, Universal Landmarks and Outstanding Figures in History, Literature and Arts", "Me, my Personality and Life Experiences", "Me, my Community and Citizenship"],
}
TEXT_TYPE = {1: "descriptive", 2: "descriptive and narrative", 3: "descriptive, narrative and prescriptive", 4: "descriptive, narrative, argumentative and prescriptive"}

GUIDE = ("Each sequence follows the plan's situations: Situation 1 — initial PDP lesson(s) (listening & speaking); "
         "Situation 2 — learning PPU/PDP lessons (language: lexis, grammar, pronunciation integrated as a skill, not as an isolated lesson; reading & writing); "
         "Situation 3 — learning to integrate (group work); Situation 4 — integration/assessment (solo work). "
         "Assessment descriptors: oral interaction, interpretation of oral and written messages, production of oral and written messages.")


def clean(block: str) -> str:
    lines = []
    for ln in block.splitlines():
        if re.search(r"[؀-ۿ]", ln) or not ln.strip():
            continue
        lines.append(re.sub(r"\s{2,}", " | ", ln.strip()))
    return "\n".join(lines)


def extract(pdf: str, n: int) -> tuple[dict, list[str]]:
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    prof = re.search(r"Exit Profile:\s*At the end of level.*?(?=\n\s*\n|VALUES)", txt, re.S)
    profile = re.sub(r"\s+", " ", prof.group(0)) if prof else ""
    comp = re.search(r"Target.*?competencies(.*?)(?:Learnin|Learning\s+Estimated|Sequences)", txt, re.S)
    target = re.sub(r"\s+", " ", comp.group(1)).strip() if comp else ""
    starts = [m.start() for m in re.finditer(r"\n[^\n]*Sequences[^\n]*\n", txt)]
    blocks = [txt[s:(starts[i + 1] if i + 1 < len(starts) else len(txt))] for i, s in enumerate(starts)]
    return {"profile": profile, "target": target}, [clean(b)[:3500] for b in blocks]


def lessons(title):
    return [
        {"title": f"Initial situation + PDP lesson: listening & speaking ({title})", "domain": "Listening",
         "hint": "Situation 1: present the sequence's initial situation, then a listening & speaking PDP lesson (pre-, while-, post-listening)."},
        {"title": "PPU lesson 1: language (grammar & lexis)", "domain": "Grammar & Vocabulary", "needs_text": True,
         "hint": "Write the target grammar/lexis point from the plan in « Support / text title »; pronunciation integrated as a skill."},
        {"title": "PPU lesson 2: language (grammar & lexis)", "domain": "Grammar & Vocabulary", "needs_text": True,
         "hint": "Presentation – Practice – Use of the second language point of the sequence."},
        {"title": "PPU lesson 3: language (grammar & lexis)", "domain": "Grammar & Vocabulary", "needs_text": True},
        {"title": "PDP lesson: reading & writing", "domain": "Reading", "needs_text": True,
         "hint": "Pre-, while- and post-reading, leading to a short writing task."},
        {"title": "Learning to integrate (group work)", "domain": "Writing",
         "hint": "Situation 3: a meaningful integration task done in groups."},
        {"title": "Integration — assessment (solo work)", "domain": "Writing",
         "hint": "Situation 4: individual integration situation assessed with the plan's descriptors."},
        {"title": "Remedial work", "domain": "Grammar & Vocabulary"},
    ]


def build(paths: dict[int, str]) -> dict:
    out = {}
    for n, pdf in paths.items():
        meta, blocks = extract(pdf, n)
        seqs = []
        for i, title in enumerate(TITLES[n], start=1):
            raw = blocks[i - 1] if i - 1 < len(blocks) else ""
            seqs.append({
                "title": f"Sequence {i}: {title}",
                "official": {
                    "source": SRC.format(n=n),
                    "levels": {"Exit profile": meta["profile"] or f"At the end of level {n}, the learner will be able to interact, interpret and produce oral and written {TEXT_TYPE[n]} messages/texts.",
                               "Target competencies": meta["target"][:900]},
                    "resources": {"Official plan extract (columns: learning objectives, lexis, grammar, pronunciation, situations, descriptors)": raw},
                    "situation": "Initial situation (Situation 1 of the plan) related to the learner's environment and interests.",
                    "tasks": ["Oral interaction", "Interpretation of oral and written messages", "Production of oral and written messages"],
                    "criteria": ["Relevance", "Correct use of language", "Coherence", "Excellence/creativity"],
                },
                "lessons": lessons(title),
            })
        out[n] = seqs
    return out


if __name__ == "__main__":
    paths = {}
    for p in sys.argv[1:]:
        m = re.search(r"english(\d)am", p)
        if m:
            paths[int(m.group(1))] = p
    built = build(paths)
    path = Path(__file__).parent / "curriculum.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    en = next(x for x in data["subjects"] if x["id"] == "english")
    for n, seqs in built.items():
        en["levels"][str(n)] = seqs
        en.setdefault("guidelines", {})[str(n)] = GUIDE
        en.setdefault("verified", {})[str(n)] = SRC.format(n=n)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print({n: [len(s["official"]["resources"].popitem()[1]) for s in v] for n, v in built.items()})
