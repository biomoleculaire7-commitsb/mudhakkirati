const BASE = import.meta.env.VITE_API_URL || ''

async function json(res) {
  if (!res.ok) {
    let msg = `خطأ ${res.status}`
    try { const j = await res.json(); msg = j.detail?.[0]?.msg || j.detail || msg } catch {}
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return res.json()
}

export const api = {
  health: () => fetch(`${BASE}/api/health`).then(json),
  curriculum: () => fetch(`${BASE}/api/curriculum`).then(json),
  generate: (body) =>
    fetch(`${BASE}/api/generate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    }).then(json),
  async exportDocx(memos, filename) {
    const res = await fetch(`${BASE}/api/export`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ memos, filename }),
    })
    if (!res.ok) throw new Error(`تعذر إنشاء ملف Word (${res.status})`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = (filename || (memos.length === 1 ? `مذكرة - ${memos[0].lesson}` : `مذكرات - ${memos[0].sequence}`))
      .replace(/[\\/:*?"<>|]+/g, ' ') + '.docx'
    document.body.appendChild(a); a.click(); a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 2000)
  },
}

export const storage = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback } catch { return fallback } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)) } catch {} },
}
