"""Builds Word (.docx) lesson plans in the Algerian 2nd-generation layout (RTL for Arabic, LTR for FR/EN)."""
import io
import re

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AR_FONT = "Simplified Arabic"
LAT_FONT = "Times New Roman"
BLUE = RGBColor(0x1F, 0x4E, 0x9A)
RED = RGBColor(0xC0, 0x1F, 0x1F)
GRAY_FILL = "E7ECF3"

LABELS = {
    "ar": {
        "republic": "الجمهورية الجزائرية الديمقراطية الشعبية",
        "ministry": "وزارة التربية الوطنية",
        "school": "المتوسطة", "year": "السنة الدراسية",
        "memo": "المذكرة رقم", "sequence": "المقطع", "domain": "الميدان", "content": "المحتوى المعرفي",
        "week": "الأسبوع", "duration": "زمن الإنجاز", "teacher": "الأستاذ", "class": "القسم", "subject": "المادة",
        "competency": "الكفاءة المستهدفة", "objectives": "الوضعيات / الأهداف التعلمية", "means": "الوسائل التعليمية",
        "phases": "المراحل", "time": "الزمن", "activities": "سير نشاطات المعلم والمتعلم", "evaluation": "التقويم",
        "homework": "الواجب المنزلي", "answer": ["ج:", "ج :"],
    },
    "fr": {
        "republic": "République Algérienne Démocratique et Populaire",
        "ministry": "Ministère de l'Éducation Nationale",
        "school": "CEM", "year": "Année scolaire",
        "memo": "Fiche N°", "sequence": "Projet / Séquence", "domain": "Domaine", "content": "Contenu",
        "week": "Semaine", "duration": "Durée", "teacher": "Enseignant(e)", "class": "Classe", "subject": "Matière",
        "competency": "Compétence visée", "objectives": "Objectifs d'apprentissage", "means": "Supports",
        "phases": "Étapes", "time": "Durée", "activities": "Déroulement (activités enseignant / apprenants)", "evaluation": "Évaluation",
        "homework": "Travail à la maison", "answer": ["R :", "R:", "Réponse :"],
    },
    "en": {
        "republic": "People's Democratic Republic of Algeria",
        "ministry": "Ministry of National Education",
        "school": "Middle school", "year": "School year",
        "memo": "Lesson plan N°", "sequence": "Sequence", "domain": "Focus", "content": "Lesson",
        "week": "Week", "duration": "Time", "teacher": "Teacher", "class": "Class", "subject": "Subject",
        "competency": "Target competency", "objectives": "Learning objectives", "means": "Materials",
        "phases": "Stages", "time": "Time", "activities": "Procedure (teacher / learners)", "evaluation": "Assessment",
        "homework": "Homework", "answer": ["A:", "Answer:"],
    },
}


# ---------- low-level OOXML helpers ----------

def _set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _set_table_borders(table, size=8):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def _set_table_rtl(table):
    bidi = OxmlElement("w:bidiVisual")
    table._tbl.tblPr.append(bidi)


def _set_col_widths(table, widths_cm):
    table.autofit = False
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(sum(widths_cm) * 567)))
    for idx, w in enumerate(widths_cm):
        table.columns[idx].width = Cm(w)
    for row in table.rows:
        for idx, w in enumerate(widths_cm):
            row.cells[idx].width = Cm(w)


def _para_rtl(p, rtl: bool):
    if rtl:
        pPr = p._p.get_or_add_pPr()
        pPr.append(OxmlElement("w:bidi"))


def _run(p, text, rtl, size=12, bold=False, color=None, underline=False):
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.underline = underline
    r.font.name = LAT_FONT
    if color:
        r.font.color.rgb = color
    rPr = r._r.get_or_add_rPr()
    fonts = rPr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rPr.insert(0, fonts)
    fonts.set(qn("w:ascii"), LAT_FONT)
    fonts.set(qn("w:hAnsi"), LAT_FONT)
    fonts.set(qn("w:cs"), AR_FONT)
    szcs = OxmlElement("w:szCs")
    szcs.set(qn("w:val"), str(int(size * 2)))
    rPr.append(szcs)
    if bold:
        rPr.append(OxmlElement("w:bCs"))
    if rtl:
        rPr.append(OxmlElement("w:rtl"))
    return r


class Writer:
    def __init__(self, lang):
        self.lang = lang
        self.rtl = lang == "ar"
        self.L = LABELS[lang]

    def cell_para(self, cell, first_used: dict, center=False):
        """Reuse the empty first paragraph of a cell, then append new ones."""
        key = id(cell._tc)
        if not first_used.get(key):
            first_used[key] = True
            p = cell.paragraphs[0]
        else:
            p = cell.add_paragraph()
        _para_rtl(p, self.rtl)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(0)
        return p

    def label_value(self, p, label, value, size=12):
        _run(p, f"{label} : ", self.rtl, size=size, bold=True)
        _run(p, value or "………………", self.rtl, size=size, color=RED if value else None)

    def activity(self, p, text, size=12):
        """Render 'question ج: answer' with the answer in blue, like teachers' hand-made memos."""
        for marker in self.L["answer"]:
            if marker in text:
                q, a = text.split(marker, 1)
                if q.strip():
                    _run(p, q.rstrip() + " ", self.rtl, size=size)
                _run(p, marker + " ", self.rtl, size=size, bold=True, color=BLUE)
                _run(p, a.strip(), self.rtl, size=size, color=BLUE)
                return
        m = re.match(r"^([^:：]{2,40})[:：]\s*(.*)$", text)
        if m and len(m.group(1).split()) <= 6:
            _run(p, m.group(1) + " : ", self.rtl, size=size, bold=True, underline=True)
            _run(p, m.group(2), self.rtl, size=size)
        else:
            _run(p, text, self.rtl, size=size)


def _add_memo(doc, memo, first: bool):
    lang = memo.get("lang", "ar")
    w = Writer(lang)
    L = w.L
    used = {}

    if not first:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # Official heading
    for text, size in ((L["republic"], 12), (L["ministry"], 12)):
        p = doc.add_paragraph()
        _para_rtl(p, w.rtl)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        _run(p, text, w.rtl, size=size, bold=True)

    top = doc.add_table(rows=1, cols=2)
    if w.rtl:
        _set_table_rtl(top)
    _set_col_widths(top, [9.5, 9.5])
    w.label_value(w.cell_para(top.cell(0, 0), used), L["school"], memo.get("school"), 11)
    p = w.cell_para(top.cell(0, 1), used)
    w.label_value(p, L["year"], memo.get("school_year"), 11)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if w.rtl else WD_ALIGN_PARAGRAPH.RIGHT
    doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # Header box: memo N° | sequence/domain/content | week/time/teacher | class
    hdr = doc.add_table(rows=1, cols=4)
    if w.rtl:
        _set_table_rtl(hdr)
    _set_table_borders(hdr, 12)
    _set_col_widths(hdr, [2.4, 8.6, 5.4, 2.6])
    c0, c1, c2, c3 = hdr.rows[0].cells
    for c in (c0, c1, c2, c3):
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = w.cell_para(c0, used, center=True)
    _run(p, L["memo"], w.rtl, 11, bold=True)
    p = w.cell_para(c0, used, center=True)
    _run(p, str(memo.get("memo_number", "")), w.rtl, 18, bold=True, color=RED)

    w.label_value(w.cell_para(c1, used), L["sequence"], memo.get("sequence"))
    w.label_value(w.cell_para(c1, used), L["domain"], memo.get("domain"))
    w.label_value(w.cell_para(c1, used), L["content"], memo.get("lesson"))

    w.label_value(w.cell_para(c2, used), L["subject"], memo.get("subject_name"))
    w.label_value(w.cell_para(c2, used), L["week"], memo.get("week"))
    w.label_value(w.cell_para(c2, used), L["duration"], memo.get("duration"))
    w.label_value(w.cell_para(c2, used), L["teacher"], memo.get("teacher"))

    p = w.cell_para(c3, used, center=True)
    _run(p, L["class"], w.rtl, 11, bold=True)
    p = w.cell_para(c3, used, center=True)
    _run(p, memo.get("class_name") or memo.get("level_short", ""), w.rtl, 14, bold=True, color=RED)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # Objectives | means
    obj = doc.add_table(rows=1, cols=2)
    if w.rtl:
        _set_table_rtl(obj)
    _set_table_borders(obj, 8)
    _set_col_widths(obj, [12.5, 6.5])
    oc, mc = obj.rows[0].cells
    if memo.get("target_competency"):
        p = w.cell_para(oc, used)
        _run(p, L["competency"] + " : ", w.rtl, 12, bold=True, color=RED, underline=True)
        _run(p, memo["target_competency"], w.rtl, 12)
    p = w.cell_para(oc, used)
    _run(p, L["objectives"] + " :", w.rtl, 12, bold=True, color=RED, underline=True)
    for o in memo.get("objectives", []):
        _run(w.cell_para(oc, used), "– " + o, w.rtl, 12)
    p = w.cell_para(mc, used)
    _run(p, L["means"] + " :", w.rtl, 12, bold=True, color=RED, underline=True)
    for m in memo.get("means", []):
        _run(w.cell_para(mc, used), "– " + m, w.rtl, 12)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # Main progression table
    phases = memo.get("phases", [])
    tbl = doc.add_table(rows=1 + len(phases), cols=4)
    if w.rtl:
        _set_table_rtl(tbl)
    _set_table_borders(tbl, 8)
    _set_col_widths(tbl, [3.0, 1.7, 10.5, 3.8])
    for i, title in enumerate((L["phases"], L["time"], L["activities"], L["evaluation"])):
        cell = tbl.rows[0].cells[i]
        _set_cell_shading(cell, GRAY_FILL)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        _run(w.cell_para(cell, used, center=True), title, w.rtl, 12, bold=True)
    for r, ph in enumerate(phases, start=1):
        cells = tbl.rows[r].cells
        cells[0].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cells[1].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        _run(w.cell_para(cells[0], used, center=True), ph.get("name", ""), w.rtl, 12, bold=True, color=BLUE)
        _run(w.cell_para(cells[1], used, center=True), ph.get("time", ""), w.rtl, 12, bold=True, color=RED)
        acts = ph.get("activities") or [""]
        for a in acts:
            w.activity(w.cell_para(cells[2], used), a)
        ev = ph.get("evaluation", "")
        m = re.match(r"^([^:：]{2,25})[:：]\s*(.*)$", ev)
        p = w.cell_para(cells[3], used)
        if m:
            _run(p, m.group(1) + " :", w.rtl, 11, bold=True, color=RED, underline=True)
            _run(w.cell_para(cells[3], used), m.group(2), w.rtl, 11)
        else:
            _run(p, ev, w.rtl, 11)

    if memo.get("homework"):
        p = doc.add_paragraph()
        _para_rtl(p, w.rtl)
        p.paragraph_format.space_before = Pt(6)
        _run(p, L["homework"] + " : ", w.rtl, 12, bold=True, underline=True)
        _run(p, memo["homework"], w.rtl, 12)


def build_docx(memos: list[dict]) -> bytes:
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1)
    sec.top_margin = sec.bottom_margin = Cm(1)

    style = doc.styles["Normal"]
    style.font.name = LAT_FONT
    style.font.size = Pt(12)
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:cs"), AR_FONT)
    style.paragraph_format.space_after = Pt(0)

    for i, memo in enumerate(memos):
        _add_memo(doc, memo, first=(i == 0))
    # python-docx leaves alignment of tables default; center them
    for t in doc.tables:
        t.alignment = WD_TABLE_ALIGNMENT.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
