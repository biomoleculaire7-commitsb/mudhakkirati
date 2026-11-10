import { useEffect, useMemo, useRef, useState } from 'react'
import { api, storage } from './api.js'

const OTHER = '__other__'
const thisYear = () => {
  const d = new Date(); const y = d.getMonth() >= 7 ? d.getFullYear() : d.getFullYear() - 1
  return `${y}/${y + 1}`
}

const UI = {
  ar: { competency: 'الكفاءة المستهدفة', objectives: 'الوضعيات / الأهداف التعلمية', means: 'الوسائل التعليمية', phases: 'المراحل', time: 'الزمن', activities: 'سير نشاطات المعلم والمتعلم', evaluation: 'التقويم', homework: 'الواجب المنزلي', sequence: 'المقطع', domain: 'الميدان', content: 'المحتوى المعرفي', week: 'الأسبوع', duration: 'زمن الإنجاز', teacher: 'الأستاذ', klass: 'القسم', memo: 'المذكرة رقم' },
  fr: { competency: 'Compétence visée', objectives: "Objectifs d'apprentissage", means: 'Supports', phases: 'Étapes', time: 'Durée', activities: 'Déroulement', evaluation: 'Évaluation', homework: 'Travail à la maison', sequence: 'Projet / Séquence', domain: 'Domaine', content: 'Contenu', week: 'Semaine', duration: 'Durée', teacher: 'Enseignant(e)', klass: 'Classe', memo: 'Fiche N°' },
  en: { competency: 'Target competency', objectives: 'Learning objectives', means: 'Materials', phases: 'Stages', time: 'Time', activities: 'Procedure', evaluation: 'Assessment', homework: 'Homework', sequence: 'Sequence', domain: 'Focus', content: 'Lesson', week: 'Week', duration: 'Time', teacher: 'Teacher', klass: 'Class', memo: 'Lesson plan N°' },
}

function AutoText({ value, onChange, className = '', dir, placeholder }) {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current; if (!el) return
    el.style.height = 'auto'; el.style.height = el.scrollHeight + 'px'
  }, [value])
  return <textarea ref={ref} rows={1} dir={dir} className={`auto ${className}`} value={value}
    placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
}

function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </label>
  )
}

export default function App() {
  const [cur, setCur] = useState(null)
  const [health, setHealth] = useState(null)
  const [loadErr, setLoadErr] = useState('')

  const [level, setLevel] = useState(4)
  const [subjectId, setSubjectId] = useState('arabic')
  const [seqSel, setSeqSel] = useState('0')
  const [seqFree, setSeqFree] = useState('')
  const [lessonSel, setLessonSel] = useState(OTHER)
  const [lessonFree, setLessonFree] = useState('')
  const [domain, setDomain] = useState('')
  const [notes, setNotes] = useState('')
  const [meta, setMeta] = useState(() => storage.get('teacher-meta', {
    teacher: '', school: '', class_name: '', school_year: thisYear(), week: '', memo_number: '1', duration: '',
  }))

  const [memo, setMemo] = useState(null)
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState('')
  const [error, setError] = useState('')
  const [basket, setBasket] = useState(() => storage.get('basket', []))

  useEffect(() => {
    api.curriculum().then(setCur).catch((e) => setLoadErr(e.message))
    api.health().then(setHealth).catch(() => {})
  }, [])
  useEffect(() => storage.set('teacher-meta', meta), [meta])
  useEffect(() => storage.set('basket', basket), [basket])

  const subject = useMemo(() => cur?.subjects.find((s) => s.id === subjectId), [cur, subjectId])
  const sequences = subject?.levels?.[String(level)] || []
  const seqObj = seqSel === OTHER ? null : sequences[Number(seqSel)]
  const sequence = seqSel === OTHER ? seqFree.trim() : (seqObj?.title || '')
  const lessonItems = (seqObj?.lessons || []).map((l) => (typeof l === 'string' ? { title: l } : l))
  const lessons = lessonItems.map((l) => l.title)
  const lesson = lessonSel === OTHER ? lessonFree.trim() : lessonSel
  const lessonObj = lessonItems.find((l) => l.title === lessonSel)
  const official = seqObj?.official
  const [textTitle, setTextTitle] = useState('')
  const [showOfficial, setShowOfficial] = useState(false)

  // reset dependent selections
  useEffect(() => { setSeqSel(sequences.length ? '0' : OTHER) }, [subjectId, level, cur])
  useEffect(() => {
    setLessonSel(lessons.length ? lessons[0] : OTHER)
    setDomain(lessonItems[0]?.domain || seqObj?.domain || '')
  }, [seqSel, subjectId, level, cur])
  useEffect(() => {
    if (lessonObj?.domain) setDomain(lessonObj.domain)
    setTextTitle('')
  }, [lessonSel])

  const setM = (k) => (e) => setMeta({ ...meta, [k]: e.target.value })

  const request = (lessonName) => ({
    level, subject: subjectId, sequence, lesson: lessonName, notes: notes || null,
    domain: (lessonItems.find((l) => l.title === lessonName)?.domain) || domain || null,
    text_title: lessonName === lesson ? (textTitle.trim() || null) : null,
    ...Object.fromEntries(Object.entries(meta).map(([k, v]) => [k, v || null])),
  })

  async function onGenerate() {
    setError('')
    if (!sequence || !lesson) { setError('اختر المقطع واكتب عنوان الدرس (المحتوى المعرفي).'); return }
    setBusy(true); setProgress('جارٍ إعداد المذكرة…')
    try {
      const m = await api.generate(request(lesson))
      setMemo(m)
      if (m.error) setError('تعذر الاتصال بنموذج الذكاء الاصطناعي، فأُنشئ هيكل مذكرة قابل للتعديل: ' + m.error)
      setMeta((x) => ({ ...x, memo_number: String((Number(x.memo_number) || 0) + 1) }))
    } catch (e) { setError(e.message) } finally { setBusy(false); setProgress('') }
  }

  async function onGenerateSequence() {
    setError('')
    if (!lessons.length) { setError('هذا المقطع لا يحتوي على قائمة دروس جاهزة؛ ولّد الدروس واحداً واحداً وأضفها إلى الملف.'); return }
    setBusy(true)
    let n = Number(meta.memo_number) || 1
    const out = []
    try {
      for (let i = 0; i < lessons.length; i++) {
        setProgress(`توليد ${i + 1} / ${lessons.length}: ${lessons[i]}`)
        const m = await api.generate({ ...request(lessons[i]), memo_number: String(n++) })
        out.push(m)
      }
      setBasket((b) => [...b, ...out])
      setMemo(out[out.length - 1])
      setMeta((x) => ({ ...x, memo_number: String(n) }))
    } catch (e) { setError(e.message); if (out.length) setBasket((b) => [...b, ...out]) }
    finally { setBusy(false); setProgress('') }
  }

  async function download(list) {
    setError('')
    try { await api.exportDocx(list) } catch (e) { setError(e.message) }
  }

  // ---- memo editing helpers
  const up = (patch) => setMemo((m) => ({ ...m, ...patch }))
  const upPhase = (i, patch) => setMemo((m) => ({ ...m, phases: m.phases.map((p, j) => (j === i ? { ...p, ...patch } : p)) }))
  const L = UI[memo?.lang || 'ar']
  const mdir = memo?.lang === 'ar' || !memo ? 'rtl' : 'ltr'

  if (loadErr) return <div className="fatal">تعذر الاتصال بالخادم: {loadErr}</div>
  if (!cur) return <div className="fatal">جارٍ التحميل…</div>

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">م</span>
          <div>
            <h1>مذكراتي</h1>
            <p>مولّد مذكرات التعليم المتوسط وفق مناهج الجيل الثاني</p>
          </div>
        </div>
        <div className={`status ${health?.ai ? 'on' : 'off'}`}>
          {health?.ai ? `الذكاء الاصطناعي مفعّل · ${health.model}` : 'وضع القوالب (بدون مفتاح API)'}
        </div>
      </header>

      <main className="layout">
        <aside className="panel">
          <h2>الدرس</h2>
          <div className="grid2">
            <Field label="المستوى">
              <select value={level} onChange={(e) => setLevel(Number(e.target.value))}>
                {cur.levels.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </Field>
            <Field label="المادة">
              <select value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
                {cur.subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </Field>
          </div>

          <Field label="المقطع التعلمي">
            <select value={seqSel} onChange={(e) => setSeqSel(e.target.value)}>
              {sequences.map((s, i) => <option key={i} value={String(i)}>{s.title}</option>)}
              <option value={OTHER}>✎ مقطع آخر (كتابة حرة)</option>
            </select>
          </Field>
          {seqSel === OTHER && <input className="mt" value={seqFree} onChange={(e) => setSeqFree(e.target.value)} placeholder="اكتب عنوان المقطع" />}

          {official && (
            <div className="official">
              <div className="official-head">
                <span>✓ مطابق للمخطط السنوي الرسمي</span>
                <button className="link" onClick={() => setShowOfficial((v) => !v)}>{showOfficial ? 'إخفاء' : 'عرض'}</button>
              </div>
              <div className="official-meta">{seqObj.term} · {seqObj.hours}</div>
              {showOfficial && (
                <div className="official-body" dir="auto">
                  {Object.entries(official.resources).map(([k, v]) => <p key={k} dir="auto" style={{whiteSpace: "pre-line"}}><b>{k}:</b> {v.length > 600 ? v.slice(0, 600) + " …" : v}</p>)}
                  <p><b>المهمات:</b> {official.tasks.join('؛ ')}</p>
                  <p className="src">{official.source}</p>
                </div>
              )}
            </div>
          )}

          <Field label="الميدان">
            <select value={domain} onChange={(e) => setDomain(e.target.value)}>
              <option value="">— يحدده المولّد —</option>
              {subject?.domains.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </Field>

          <Field label="المحتوى المعرفي (الدرس)">
            <select value={lessonSel} onChange={(e) => setLessonSel(e.target.value)}>
              {lessons.map((l) => <option key={l} value={l}>{l}</option>)}
              <option value={OTHER}>✎ درس آخر (كتابة حرة)</option>
            </select>
          </Field>
          {lessonSel === OTHER && <input className="mt" value={lessonFree} onChange={(e) => setLessonFree(e.target.value)} placeholder="مثال: ثري الحرب — فهم المنطوق" />}
          {lessonObj?.hint && <p className="lesson-hint">{lessonObj.hint}</p>}

          <Field label={lessonObj?.needs_text ? 'السند / عنوان النص (مطلوب لهذه الحصة)' : 'السند / عنوان النص (اختياري)'}>
            <input className={lessonObj?.needs_text && !textTitle ? 'need' : ''} value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)} placeholder="مثال: ذكرى وندم — مالك بن نبي، ص 10" />
          </Field>

          <Field label="توجيهات إضافية (اختياري)">
            <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="مثال: النص في الكتاب ص 10، ركّز على عطف البيان…" />
          </Field>

          <h2>معلومات المذكرة</h2>
          <div className="grid2">
            <Field label="الأستاذ"><input value={meta.teacher} onChange={setM('teacher')} /></Field>
            <Field label="المتوسطة"><input value={meta.school} onChange={setM('school')} /></Field>
            <Field label="القسم"><input value={meta.class_name} onChange={setM('class_name')} placeholder="4 م 2" /></Field>
            <Field label="السنة الدراسية"><input value={meta.school_year} onChange={setM('school_year')} /></Field>
            <Field label="رقم المذكرة"><input value={meta.memo_number} onChange={setM('memo_number')} /></Field>
            <Field label="الأسبوع"><input value={meta.week} onChange={setM('week')} /></Field>
            <Field label="المدة"><input value={meta.duration} onChange={setM('duration')} placeholder={subject?.hours} /></Field>
          </div>

          <div className="actions">
            <button className="primary" disabled={busy} onClick={onGenerate}>{busy ? '…' : 'ولّد المذكرة'}</button>
            <button className="ghost" disabled={busy || !lessons.length} onClick={onGenerateSequence}
              title="يولّد مذكرة لكل درس في المقطع ويضيفها إلى الملف">ولّد المقطع كاملاً</button>
          </div>
          {progress && <div className="progress"><span className="spinner" />{progress}</div>}
          {error && <div className="error">{error}</div>}
          <p className="note">{cur._note}</p>
        </aside>

        <section className="workspace">
          {!memo ? (
            <div className="empty">
              <div className="empty-art">📄</div>
              <h3>اختر الدرس ثم اضغط «ولّد المذكرة»</h3>
              <p>ستظهر المذكرة هنا بتخطيط الجيل الثاني، قابلة للتعديل مباشرة، ثم تحمّلها بصيغة Word.</p>
            </div>
          ) : (
            <>
              <div className="toolbar">
                <span className={`badge ${memo.source}`}>{memo.source === 'ai' ? 'مولّدة بالذكاء الاصطناعي' : 'هيكل قالب — أكمله'}</span>
                <div className="spacer" />
                <button className="ghost" onClick={() => setBasket((b) => [...b, memo])}>＋ أضف إلى الملف</button>
                <button className="primary" onClick={() => download([memo])}>⬇ تحميل Word</button>
              </div>

              <article className="paper" dir={mdir}>
                <div className="hdr">
                  <div className="box num"><b>{L.memo}</b><input className="big" value={memo.memo_number} onChange={(e) => up({ memo_number: e.target.value })} /></div>
                  <div className="box main">
                    <div className="kv"><b>{L.sequence} :</b><input value={memo.sequence} onChange={(e) => up({ sequence: e.target.value })} /></div>
                    <div className="kv"><b>{L.domain} :</b><input value={memo.domain} onChange={(e) => up({ domain: e.target.value })} /></div>
                    <div className="kv"><b>{L.content} :</b><input value={memo.lesson} onChange={(e) => up({ lesson: e.target.value })} /></div>
                  </div>
                  <div className="box side">
                    <div className="kv"><b>{L.week} :</b><input value={memo.week} onChange={(e) => up({ week: e.target.value })} /></div>
                    <div className="kv"><b>{L.duration} :</b><input value={memo.duration} onChange={(e) => up({ duration: e.target.value })} /></div>
                    <div className="kv"><b>{L.teacher} :</b><input value={memo.teacher} onChange={(e) => up({ teacher: e.target.value })} /></div>
                  </div>
                  <div className="box num"><b>{L.klass}</b><input className="big" value={memo.class_name || memo.level_short} onChange={(e) => up({ class_name: e.target.value })} /></div>
                </div>

                <div className="obj">
                  <div className="box">
                    <h4>{L.competency}</h4>
                    <AutoText value={memo.target_competency} onChange={(v) => up({ target_competency: v })} />
                    <h4>{L.objectives}</h4>
                    <AutoText value={memo.objectives.join('\n')} onChange={(v) => up({ objectives: v.split('\n') })} />
                  </div>
                  <div className="box">
                    <h4>{L.means}</h4>
                    <AutoText value={memo.means.join('\n')} onChange={(v) => up({ means: v.split('\n') })} />
                  </div>
                </div>

                <table className="prog">
                  <thead><tr><th>{L.phases}</th><th>{L.time}</th><th>{L.activities}</th><th>{L.evaluation}</th></tr></thead>
                  <tbody>
                    {memo.phases.map((p, i) => (
                      <tr key={i}>
                        <td className="phase"><AutoText value={p.name} onChange={(v) => upPhase(i, { name: v })} /></td>
                        <td className="time"><input value={p.time} onChange={(e) => upPhase(i, { time: e.target.value })} /></td>
                        <td><AutoText value={p.activities.join('\n')} onChange={(v) => upPhase(i, { activities: v.split('\n') })} /></td>
                        <td className="eval"><AutoText value={p.evaluation} onChange={(v) => upPhase(i, { evaluation: v })} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="hw"><b>{L.homework} :</b><AutoText value={memo.homework || ''} onChange={(v) => up({ homework: v })} /></div>
              </article>
              <p className="tip">كل سطر في خانة «سير النشاطات» يصبح فقرة في ملف Word، والإجابات بعد «ج:» تُلوَّن بالأزرق.</p>
            </>
          )}

          {basket.length > 0 && (
            <div className="basket">
              <div className="basket-head">
                <h3>ملف المذكرات ({basket.length})</h3>
                <div className="spacer" />
                <button className="ghost" onClick={() => setBasket([])}>إفراغ</button>
                <button className="primary" onClick={() => download(basket)}>⬇ تحميل الكل في ملف Word واحد</button>
              </div>
              <ol>
                {basket.map((m, i) => (
                  <li key={i}>
                    <button className="link" onClick={() => setMemo(m)}>مذكرة {m.memo_number} — {m.subject_name} · {m.lesson}</button>
                    <button className="x" onClick={() => setBasket((b) => b.filter((_, j) => j !== i))} aria-label="حذف">×</button>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
