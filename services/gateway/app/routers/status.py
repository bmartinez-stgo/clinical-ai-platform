from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_TIMEOUT = 5.0
_DEGRADED_MS = 1_000
_PARTIAL_MS = 3_000


@dataclass
class _Svc:
    id: str
    name_es: str
    name_en: str
    group: str
    url: str


_SERVICES: list[_Svc] = [
    _Svc("auth",            "Autenticación",               "Authentication",      "core",   "http://auth.cap-prod-auth.svc.cluster.local:8081/health"),
    _Svc("document-reader", "Procesamiento de Documentos", "Document Processing", "core",   "http://document-reader.cap-prod-document-reader.svc.cluster.local:8082/health"),
    _Svc("ai-diagnostic",   "Diagnóstico AI",              "AI Diagnostics",      "core",   "http://ai-diagnostic.cap-prod-ai-diagnostic.svc.cluster.local:8083/health"),
    _Svc("clinical-chat",   "Chat Clínico",                "Clinical Chat",       "core",   "http://clinical-chat.cap-prod-clinical-chat.svc.cluster.local:8086/health"),
    _Svc("clinical-rag",    "Base de Conocimiento",        "Knowledge Base",      "core",   "http://clinical-rag.cap-prod-clinical-rag.svc.cluster.local:8085/health"),
    _Svc("ai-engine",       "Motor de Extracción",         "Extraction Engine",   "models", "http://ai-engine.cap-prod-ai-engine.svc.cluster.local:8090/health"),
    _Svc("ocr-engine",      "Motor OCR",                   "OCR Engine",          "models", "http://ocr-engine.cap-prod-ocr-engine.svc.cluster.local:8091/health"),
    _Svc("vllm-reasoning",  "Modelo de Lenguaje",          "Language Model",      "models", "http://vllm-reasoning.cap-prod-vllm-reasoning.svc.cluster.local:8000/health"),
    _Svc("vllm-server",     "Modelo de Visión",            "Vision Model",        "models", "http://vllm-server.cap-prod-vllm-server.svc.cluster.local:8000/health"),
]

_SEVERITY: dict[str, int] = {
    "operational": 0,
    "degraded": 1,
    "unknown": 1,
    "partial_outage": 2,
    "major_outage": 3,
}


async def _check(svc: _Svc) -> dict:
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(svc.url)
        ms = int((time.monotonic() - t0) * 1000)
        if r.status_code >= 500:
            status = "major_outage"
        elif r.status_code >= 400:
            status = "partial_outage"
        elif ms >= _PARTIAL_MS:
            status = "partial_outage"
        elif ms >= _DEGRADED_MS:
            status = "degraded"
        else:
            status = "operational"
    except (httpx.TimeoutException, httpx.ConnectError):
        ms = int(_TIMEOUT * 1000)
        status = "major_outage"
    except Exception:
        ms = None
        status = "unknown"
    return {
        "id": svc.id,
        "name_es": svc.name_es,
        "name_en": svc.name_en,
        "group": svc.group,
        "status": status,
        "latency_ms": ms,
    }


def _overall(services: list[dict]) -> str:
    worst = max((_SEVERITY.get(s["status"], 0) for s in services), default=0)
    return ["operational", "degraded", "partial_outage", "major_outage"][min(worst, 3)]


@router.get("/status/api", include_in_schema=False)
async def status_api():
    services = list(await asyncio.gather(*[_check(s) for s in _SERVICES]))
    return {
        "overall": _overall(services),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "services": services,
    }


_PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estado del Sistema &mdash; Clinical AI Platform</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --green:#16a34a;--green-bg:#f0fdf4;--green-border:#bbf7d0;
  --yellow:#b45309;--yellow-bg:#fffbeb;--yellow-border:#fde68a;
  --orange:#c2410c;--orange-bg:#fff7ed;--orange-border:#fed7aa;
  --red:#b91c1c;--red-bg:#fef2f2;--red-border:#fecaca;
  --gray:#6b7280;--gray-bg:#f9fafb;--gray-border:#e5e7eb;
  --text:#0f172a;--text-muted:#64748b;--text-light:#94a3b8;
  --bg:#f1f5f9;--card:#fff;--border:#e2e8f0;
  --radius:10px;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,sans-serif;
}
body{background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column}
.container{max-width:720px;margin:0 auto;padding:0 20px;width:100%}

/* Header */
header{background:var(--card);border-bottom:1px solid var(--border);padding:16px 0}
.header-inner{display:flex;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center;gap:10px}
.brand-name{font-size:1rem;font-weight:600;color:var(--text)}
.brand-sub{font-size:0.75rem;color:var(--text-muted);margin-top:1px}
.lang-btn{
  background:transparent;border:1px solid var(--border);
  border-radius:6px;padding:5px 12px;font-size:0.8125rem;
  color:var(--text-muted);cursor:pointer;font-weight:500;
  transition:border-color .15s,color .15s
}
.lang-btn:hover{border-color:#94a3b8;color:var(--text)}

/* Main */
main{flex:1;padding:32px 0}

/* Overall banner */
.overall-card{
  border-radius:var(--radius);padding:22px 24px;
  display:flex;align-items:center;gap:18px;
  margin-bottom:28px;border:1px solid transparent;
  transition:background .3s,border-color .3s
}
.overall-card.operational{background:var(--green-bg);border-color:var(--green-border)}
.overall-card.degraded{background:var(--yellow-bg);border-color:var(--yellow-border)}
.overall-card.partial_outage{background:var(--orange-bg);border-color:var(--orange-border)}
.overall-card.major_outage{background:var(--red-bg);border-color:var(--red-border)}
.overall-card.checking{background:var(--gray-bg);border-color:var(--gray-border)}
.overall-icon{flex-shrink:0}
.overall-title{font-size:1.125rem;font-weight:700;color:var(--text);line-height:1.3}
.overall-sub{font-size:0.875rem;color:var(--text-muted);margin-top:3px}

/* Status dot */
.dot{
  display:inline-block;border-radius:50%;flex-shrink:0;
  transition:background .3s
}
.dot-lg{width:20px;height:20px}
.dot-sm{width:10px;height:10px}
.dot.operational{background:var(--green)}
.dot.degraded{background:var(--yellow)}
.dot.partial_outage{background:var(--orange)}
.dot.major_outage{background:var(--red)}
.dot.unknown{background:var(--gray)}
.dot.checking{background:var(--gray);animation:pulse 1.2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

/* Service sections */
.section{margin-bottom:24px}
.section-title{
  font-size:0.6875rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;color:var(--text-muted);margin-bottom:8px
}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.service-row{
  display:flex;align-items:center;gap:12px;
  padding:13px 20px;border-bottom:1px solid #f8fafc
}
.service-row:last-child{border-bottom:none}
.service-name{flex:1;font-size:0.9375rem;font-weight:500;color:var(--text)}
.service-status-text{font-size:0.8125rem;font-weight:500}
.service-status-text.operational{color:var(--green)}
.service-status-text.degraded{color:var(--yellow)}
.service-status-text.partial_outage{color:var(--orange)}
.service-status-text.major_outage{color:var(--red)}
.service-status-text.unknown{color:var(--gray)}
.service-latency{
  font-size:0.75rem;color:var(--text-light);text-align:right;
  min-width:52px;font-variant-numeric:tabular-nums
}
.skeleton-row{
  display:flex;align-items:center;gap:12px;padding:13px 20px;
  border-bottom:1px solid #f8fafc
}
.skeleton-row:last-child{border-bottom:none}
.skel{background:#e2e8f0;border-radius:4px;animation:skel .9s ease infinite alternate}
@keyframes skel{from{opacity:.6}to{opacity:1}}
.skel-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.skel-name{height:14px;flex:1}
.skel-status{height:12px;width:72px}
.skel-lat{height:11px;width:38px}

/* Footer */
footer{background:var(--card);border-top:1px solid var(--border);padding:14px 0}
.footer-inner{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.footer-text{font-size:0.8125rem;color:var(--text-light)}
.footer-refresh{font-size:0.8125rem;color:var(--text-muted)}
.dot-indicator{width:6px;height:6px;display:inline-block;border-radius:50%;background:#22c55e;margin-right:5px;animation:live 2s ease-in-out infinite}
@keyframes live{0%,100%{opacity:1}50%{opacity:.2}}

@media(max-width:480px){
  .overall-card{padding:16px}
  .service-row{padding:12px 16px}
  .service-status-text{display:none}
  .overall-title{font-size:1rem}
}
</style>
</head>
<body>

<header>
  <div class="container">
    <div class="header-inner">
      <div class="brand">
        <div>
          <div class="brand-name">Clinical AI Platform</div>
          <div class="brand-sub" id="brand-sub">Estado del Sistema</div>
        </div>
      </div>
      <button class="lang-btn" id="lang-btn" onclick="toggleLang()">EN</button>
    </div>
  </div>
</header>

<main>
  <div class="container">

    <div class="overall-card checking" id="overall-card">
      <div class="overall-icon">
        <div class="dot dot-lg checking" id="overall-dot"></div>
      </div>
      <div>
        <div class="overall-title" id="overall-title">Verificando...</div>
        <div class="overall-sub" id="overall-sub"></div>
      </div>
    </div>

    <div class="section">
      <div class="section-title" id="header-core">Servicios Principales</div>
      <div class="card" id="group-core">
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
      </div>
    </div>

    <div class="section">
      <div class="section-title" id="header-models">Modelos de IA</div>
      <div class="card" id="group-models">
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
        <div class="skeleton-row"><div class="skel skel-dot"></div><div class="skel skel-name"></div><div class="skel skel-status"></div><div class="skel skel-lat"></div></div>
      </div>
    </div>

  </div>
</main>

<footer>
  <div class="container">
    <div class="footer-inner">
      <span class="footer-text" id="last-checked"></span>
      <span class="footer-refresh" id="countdown"></span>
    </div>
  </div>
</footer>

<script>
var lang = localStorage.getItem('cap_lang') || 'es';
var lastData = null;
var countdownSec = 30;
var countdownId = null;

var STRINGS = {
  brand_sub:       {es:'Estado del Sistema',             en:'System Status'},
  checking:        {es:'Verificando…',               en:'Checking…'},
  overall_op:      {es:'Todos los Sistemas Operacionales',en:'All Systems Operational'},
  overall_deg:     {es:'Rendimiento Degradado',           en:'Degraded Performance'},
  overall_partial: {es:'Interrupción Parcial del Servicio',en:'Partial Service Outage'},
  overall_major:   {es:'Interrupción Mayor del Servicio',  en:'Major Service Outage'},
  svc_count:       {es:'servicios operacionales',         en:'services operational'},
  of:              {es:'de',                              en:'of'},
  header_core:     {es:'Servicios Principales',           en:'Core Services'},
  header_models:   {es:'Modelos de IA',                  en:'AI Models'},
  status_op:       {es:'Operacional',                    en:'Operational'},
  status_deg:      {es:'Rendimiento Degradado',           en:'Degraded Performance'},
  status_partial:  {es:'Interrupción Parcial',       en:'Partial Outage'},
  status_major:    {es:'Interrupción Mayor',         en:'Major Outage'},
  status_unknown:  {es:'Desconocido',                    en:'Unknown'},
  last_checked:    {es:'Verificado: ',                   en:'Last checked: '},
  refresh_in:      {es:'Actualizando en ',               en:'Refreshing in '},
  refresh_now:     {es:'Actualizando…',              en:'Refreshing…'},
  fetch_error:     {es:'Error de conexión',         en:'Connection error'},
};

var OVERALL_KEY = {
  operational:   'overall_op',
  degraded:      'overall_deg',
  partial_outage:'overall_partial',
  major_outage:  'overall_major',
};

var STATUS_KEY = {
  operational:   'status_op',
  degraded:      'status_deg',
  partial_outage:'status_partial',
  major_outage:  'status_major',
  unknown:       'status_unknown',
};

function s(key) { return (STRINGS[key] && STRINGS[key][lang]) || key; }

function el(id) { return document.getElementById(id); }

function toggleLang() {
  lang = lang === 'es' ? 'en' : 'es';
  localStorage.setItem('cap_lang', lang);
  applyLang();
  if (lastData) renderStatus(lastData);
}

function applyLang() {
  document.documentElement.lang = lang;
  el('lang-btn').textContent = lang === 'es' ? 'EN' : 'ES';
  el('brand-sub').textContent = s('brand_sub');
  if (!lastData) el('overall-title').textContent = s('checking');
  el('header-core').textContent = s('header_core');
  el('header-models').textContent = s('header_models');
}

function renderStatus(data) {
  var overall = data.overall;
  var card = el('overall-card');
  card.className = 'overall-card ' + overall;
  var dot = el('overall-dot');
  dot.className = 'dot dot-lg ' + overall;
  el('overall-title').textContent = s(OVERALL_KEY[overall] || 'checking');

  var ops = data.services.filter(function(x){return x.status==='operational';}).length;
  var total = data.services.length;
  el('overall-sub').textContent = ops + ' ' + s('of') + ' ' + total + ' ' + s('svc_count');

  var groups = {core:[], models:[]};
  data.services.forEach(function(sv) {
    if (groups[sv.group]) groups[sv.group].push(sv);
  });

  ['core','models'].forEach(function(gid) {
    var container = el('group-' + gid);
    if (!container) return;
    var html = '';
    groups[gid].forEach(function(sv) {
      var name = lang === 'es' ? sv.name_es : sv.name_en;
      var stKey = STATUS_KEY[sv.status] || 'status_unknown';
      var lat = sv.latency_ms != null ? sv.latency_ms + 'ms' : '—';
      html += '<div class="service-row">'
        + '<div class="dot dot-sm ' + sv.status + '"></div>'
        + '<div class="service-name">' + htmlEsc(name) + '</div>'
        + '<div class="service-status-text ' + sv.status + '">' + s(stKey) + '</div>'
        + '<div class="service-latency">' + lat + '</div>'
        + '</div>';
    });
    container.innerHTML = html;
  });

  var checkedAt = new Date(data.checked_at);
  var locale = lang === 'es' ? 'es-MX' : 'en-US';
  el('last-checked').innerHTML = '<span class="dot-indicator"></span>' + s('last_checked')
    + checkedAt.toLocaleTimeString(locale, {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

function htmlEsc(str) {
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}

function startCountdown() {
  countdownSec = 30;
  if (countdownId) clearInterval(countdownId);
  countdownId = setInterval(function() {
    countdownSec--;
    if (countdownSec <= 0) {
      clearInterval(countdownId);
      el('countdown').textContent = s('refresh_now');
      fetchStatus();
    } else {
      el('countdown').textContent = s('refresh_in') + countdownSec + 's';
    }
  }, 1000);
  el('countdown').textContent = s('refresh_in') + countdownSec + 's';
}

function fetchStatus() {
  fetch('/status/api')
    .then(function(r){ return r.json(); })
    .then(function(data) {
      lastData = data;
      renderStatus(data);
      startCountdown();
    })
    .catch(function() {
      var card = el('overall-card');
      card.className = 'overall-card major_outage';
      el('overall-dot').className = 'dot dot-lg major_outage';
      el('overall-title').textContent = s('fetch_error');
      el('overall-sub').textContent = '';
      startCountdown();
    });
}

applyLang();
fetchStatus();
</script>
</body>
</html>
"""


@router.get("/status", response_class=HTMLResponse, include_in_schema=False)
async def status_page():
    return HTMLResponse(_PAGE)
