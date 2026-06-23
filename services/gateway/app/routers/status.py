from __future__ import annotations

import asyncio
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PROMETHEUS = "http://kube-prometheus-stack-prometheus.observability.svc.cluster.local:9090"
_TIMEOUT = 8.0
_HISTORY_DAYS = 30
_HISTORY_STEP = "6h"   # 4 points/day → smooth daily aggregation


@dataclass
class _Svc:
    id: str
    name_es: str
    name_en: str
    group: str
    namespace: str
    pod_prefix: str


_SERVICES: list[_Svc] = [
    _Svc("auth",            "Autenticación",               "Authentication",      "core",   "cap-prod-auth",            r"auth-"),
    _Svc("document-reader", "Procesamiento de Documentos", "Document Processing", "core",   "cap-prod-document-reader", r"document-reader-[^rw]"),
    _Svc("ai-diagnostic",   "Diagnóstico AI",              "AI Diagnostics",      "core",   "cap-prod-ai-diagnostic",   r"ai-diagnostic-"),
    _Svc("clinical-chat",   "Chat Clínico",                "Clinical Chat",       "core",   "cap-prod-clinical-chat",   r"clinical-chat-"),
    _Svc("clinical-rag",    "Base de Conocimiento",        "Knowledge Base",      "core",   "cap-prod-clinical-rag",    r"clinical-rag-"),
    _Svc("ai-engine",       "Motor de Extracción",         "Extraction Engine",   "models", "cap-prod-ai-engine",       r"ai-engine-"),
    _Svc("ocr-engine",      "Motor OCR",                   "OCR Engine",          "models", "cap-prod-ocr-engine",      r"ocr-engine-"),
    _Svc("vllm-reasoning",  "Modelo de Lenguaje",          "Language Model",      "models", "cap-prod-vllm-reasoning",  r"vllm-reasoning-"),
    _Svc("vllm-server",     "Modelo de Visión",            "Vision Model",        "models", "cap-prod-vllm-server",     r"vllm-server-"),
]

_SEVERITY = {"operational": 0, "unknown": 0, "degraded": 1, "partial_outage": 2, "major_outage": 3}

# Excluded routes for user-facing latency (infra probes)
_INFRA_ROUTES = r"/health|/ready|/metrics|/status.*|/gw/.*"


async def _prom_query(client: httpx.AsyncClient, query: str) -> list[dict]:
    url = f"{_PROMETHEUS}/api/v1/query?query={urllib.parse.quote(query)}"
    try:
        r = await client.get(url, timeout=_TIMEOUT)
        return r.json().get("data", {}).get("result", [])
    except Exception:
        return []


async def _prom_range(client: httpx.AsyncClient, query: str, start: int, end: int, step: str) -> list[dict]:
    params = f"query={urllib.parse.quote(query)}&start={start}&end={end}&step={urllib.parse.quote(step)}"
    url = f"{_PROMETHEUS}/api/v1/query_range?{params}"
    try:
        r = await client.get(url, timeout=_TIMEOUT)
        return r.json().get("data", {}).get("result", [])
    except Exception:
        return []


def _safe_float(v: Any, fallback: float | None = None) -> float | None:
    try:
        x = float(v)
        if x != x:  # NaN
            return fallback
        return x
    except (TypeError, ValueError):
        return fallback


def _svc_status(pod_prefix: str, ns: str, readiness: dict[str, dict[str, int]]) -> str:
    ns_pods = readiness.get(ns)
    if ns_pods is None:
        return "unknown"
    pattern = re.compile(pod_prefix)
    matching = {pod: val for pod, val in ns_pods.items() if pattern.match(pod)}
    if not matching:
        return "unknown"
    total = len(matching)
    ready = sum(1 for v in matching.values() if v == 1)
    if ready == 0:
        return "major_outage"
    if ready < total:
        return "degraded"
    return "operational"


def _compute_history(
    ts_values: list[tuple[float, str]],
    days: int = _HISTORY_DAYS,
) -> list[dict]:
    """
    Takes a list of (timestamp, value) pairs and returns one entry per day
    (most recent first reversed to oldest first) over the last `days` days.
    Each entry: {date: "YYYY-MM-DD", uptime_pct: float|None}
    """
    now = datetime.now(timezone.utc)
    result = []
    for d in range(days - 1, -1, -1):
        day_end = now - timedelta(days=d)
        day_start = day_end - timedelta(days=1)
        day_pts = [
            float(v) for ts, v in ts_values
            if day_start.timestamp() <= ts < day_end.timestamp()
        ]
        if not day_pts:
            pct = None
        else:
            pct = round(sum(day_pts) / len(day_pts) * 100, 1)
        result.append({"date": day_start.strftime("%Y-%m-%d"), "uptime_pct": pct})
    return result


def _overall(statuses: list[str]) -> str:
    worst = max((_SEVERITY.get(s, 0) for s in statuses), default=0)
    return ["operational", "degraded", "partial_outage", "major_outage"][min(worst, 3)]


@router.get("/status/api", include_in_schema=False)
async def status_api():
    now = int(time.time())
    start = now - _HISTORY_DAYS * 86400

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Run all Prometheus queries concurrently
        (
            readiness_instant,
            readiness_range,
            p50_result,
            p95_result,
            rps_result,
            err_result,
        ) = await asyncio.gather(
            _prom_query(client,
                'kube_pod_status_ready{namespace=~"cap-prod-.*",condition="true"}'),
            _prom_range(client,
                'max by(namespace)(kube_pod_status_ready{namespace=~"cap-prod-.*",condition="true"})',
                start, now, _HISTORY_STEP),
            _prom_query(client,
                f'histogram_quantile(0.50,sum by(le)(rate(platform_http_request_duration_seconds_bucket'
                f'{{namespace="cap-prod-gateway",http_route!~"{_INFRA_ROUTES}"}}[10m])))*1000'),
            _prom_query(client,
                f'histogram_quantile(0.95,sum by(le)(rate(platform_http_request_duration_seconds_bucket'
                f'{{namespace="cap-prod-gateway",http_route!~"{_INFRA_ROUTES}"}}[10m])))*1000'),
            _prom_query(client,
                f'sum(rate(platform_http_requests_total{{namespace="cap-prod-gateway",'
                f'http_route!~"{_INFRA_ROUTES}"}}[10m]))*60'),
            _prom_query(client,
                f'sum(rate(platform_http_requests_total{{namespace="cap-prod-gateway",'
                f'http_status_code=~"5..",http_route!~"{_INFRA_ROUTES}"}}[10m]))'
                f'/sum(rate(platform_http_requests_total{{namespace="cap-prod-gateway",'
                f'http_route!~"{_INFRA_ROUTES}"}}[10m]))*100'),
        )

    # Build instant readiness map: {namespace: {pod: ready_value}}
    readiness_map: dict[str, dict[str, int]] = {}
    for item in readiness_instant:
        ns = item["metric"].get("namespace", "")
        pod = item["metric"].get("pod", "")
        val = int(float(item["value"][1]))
        readiness_map.setdefault(ns, {})[pod] = val

    # Build history map: {namespace: [(ts, val), ...]}
    history_map: dict[str, list[tuple[float, str]]] = {}
    for series in readiness_range:
        ns = series["metric"].get("namespace", "")
        history_map[ns] = [(float(ts), v) for ts, v in series["values"]]

    # Build per-service data
    services = []
    for svc in _SERVICES:
        status = _svc_status(svc.pod_prefix, svc.namespace, readiness_map)
        ts_vals = history_map.get(svc.namespace, [])
        history = _compute_history(ts_vals)
        valid = [d["uptime_pct"] for d in history if d["uptime_pct"] is not None]
        uptime_30d = round(sum(valid) / len(valid), 1) if valid else None
        services.append({
            "id": svc.id,
            "name_es": svc.name_es,
            "name_en": svc.name_en,
            "group": svc.group,
            "status": status,
            "uptime_30d": uptime_30d,
            "history": history,
        })

    # Platform metrics (gateway)
    p50 = _safe_float(p50_result[0]["value"][1] if p50_result else None)
    p95 = _safe_float(p95_result[0]["value"][1] if p95_result else None)
    rps = _safe_float(rps_result[0]["value"][1] if rps_result else None)
    err = _safe_float(err_result[0]["value"][1] if err_result else None)

    return {
        "overall": _overall([s["status"] for s in services]),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "services": services,
        "platform_metrics": {
            "latency_p50_ms": round(p50, 1) if p50 is not None else None,
            "latency_p95_ms": round(p95, 1) if p95 is not None else None,
            "requests_per_min": round(rps, 1) if rps is not None else None,
            "error_rate_pct": round(err, 2) if err is not None else 0.0,
        },
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
.container{max-width:780px;margin:0 auto;padding:0 20px;width:100%}

header{background:var(--card);border-bottom:1px solid var(--border);padding:14px 0}
.header-inner{display:flex;align-items:center;justify-content:space-between}
.brand-name{font-size:.9375rem;font-weight:600;color:var(--text)}
.brand-sub{font-size:.75rem;color:var(--text-muted);margin-top:1px}
.lang-btn{background:transparent;border:1px solid var(--border);border-radius:6px;
  padding:4px 11px;font-size:.8125rem;color:var(--text-muted);cursor:pointer;font-weight:500;
  transition:border-color .15s,color .15s}
.lang-btn:hover{border-color:#94a3b8;color:var(--text)}

main{flex:1;padding:28px 0}

/* Overall banner */
.overall-card{border-radius:var(--radius);padding:20px 24px;display:flex;
  align-items:center;gap:16px;margin-bottom:24px;border:1px solid transparent;
  transition:background .3s,border-color .3s}
.overall-card.operational{background:var(--green-bg);border-color:var(--green-border)}
.overall-card.degraded{background:var(--yellow-bg);border-color:var(--yellow-border)}
.overall-card.partial_outage{background:var(--orange-bg);border-color:var(--orange-border)}
.overall-card.major_outage{background:var(--red-bg);border-color:var(--red-border)}
.overall-card.checking{background:var(--gray-bg);border-color:var(--gray-border)}
.overall-title{font-size:1.0625rem;font-weight:700;color:var(--text)}
.overall-sub{font-size:.8125rem;color:var(--text-muted);margin-top:2px}

/* Platform metrics strip */
.metrics-strip{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:16px 20px;margin-bottom:24px;display:grid;
  grid-template-columns:repeat(4,1fr);gap:16px}
.metric-item{text-align:center}
.metric-label{font-size:.6875rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;
  color:var(--text-muted);margin-bottom:4px}
.metric-value{font-size:1.125rem;font-weight:700;color:var(--text);letter-spacing:-.02em}
.metric-unit{font-size:.75rem;color:var(--text-muted);font-weight:400}
.metric-source{font-size:.625rem;color:var(--text-light);margin-top:2px}
@media(max-width:520px){.metrics-strip{grid-template-columns:repeat(2,1fr)}}

/* Dots */
.dot{display:inline-block;border-radius:50%;flex-shrink:0;transition:background .3s}
.dot-lg{width:18px;height:18px}
.dot-sm{width:9px;height:9px}
.dot.operational{background:var(--green)}
.dot.degraded{background:var(--yellow)}
.dot.partial_outage{background:var(--orange)}
.dot.major_outage{background:var(--red)}
.dot.unknown{background:#d1d5db}
.dot.checking{background:#d1d5db;animation:pulse 1.2s ease infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

/* Service sections */
.section{margin-bottom:20px}
.section-title{font-size:.6875rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;color:var(--text-muted);margin-bottom:8px}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}

/* Service row */
.service-row{display:flex;align-items:center;gap:12px;padding:14px 20px;
  border-bottom:1px solid #f8fafc;flex-wrap:wrap}
.service-row:last-child{border-bottom:none}
.svc-left{display:flex;align-items:center;gap:10px;min-width:0;flex:0 0 210px}
.svc-name{font-size:.9375rem;font-weight:500;color:var(--text);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.svc-history{flex:1;min-width:180px;display:flex;flex-direction:column;gap:4px}
.history-bars{display:flex;gap:2px;align-items:center}
.bar{width:8px;height:22px;border-radius:2px;flex-shrink:0;cursor:default;
  transition:opacity .15s;position:relative}
.bar:hover{opacity:.8}
.bar-op{background:#22c55e}
.bar-deg{background:#fbbf24}
.bar-partial{background:#f97316}
.bar-out{background:#ef4444}
.bar-none{background:#e2e8f0}
.history-meta{display:flex;justify-content:space-between;align-items:center}
.uptime-pct{font-size:.75rem;font-weight:600;color:var(--text)}
.history-range{font-size:.6875rem;color:var(--text-light)}
.svc-status-text{font-size:.8125rem;font-weight:500;flex:0 0 120px;text-align:right}
.svc-status-text.operational{color:var(--green)}
.svc-status-text.degraded{color:var(--yellow)}
.svc-status-text.partial_outage{color:var(--orange)}
.svc-status-text.major_outage{color:var(--red)}
.svc-status-text.unknown{color:#9ca3af}

/* Skeleton */
.skeleton-row{display:flex;align-items:center;gap:12px;padding:14px 20px;border-bottom:1px solid #f8fafc}
.skeleton-row:last-child{border-bottom:none}
.skel{background:#e2e8f0;border-radius:4px;animation:skel .9s ease infinite alternate}
@keyframes skel{from{opacity:.6}to{opacity:1}}
.sk-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.sk-name{height:13px;width:140px}
.sk-bars{height:22px;flex:1}
.sk-pct{height:11px;width:38px}

/* Tooltip */
.tooltip{position:fixed;background:#1e293b;color:#f1f5f9;font-size:.75rem;
  padding:5px 9px;border-radius:5px;pointer-events:none;opacity:0;
  transition:opacity .1s;white-space:nowrap;z-index:999;line-height:1.4}

footer{background:var(--card);border-top:1px solid var(--border);padding:12px 0}
.footer-inner{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.footer-text{font-size:.8125rem;color:var(--text-light)}
.footer-refresh{font-size:.8125rem;color:var(--text-muted)}
.dot-live{width:6px;height:6px;display:inline-block;border-radius:50%;
  background:#22c55e;margin-right:5px;animation:live 2s ease-in-out infinite}
@keyframes live{0%,100%{opacity:1}50%{opacity:.2}}

@media(max-width:600px){
  .svc-left{flex:0 0 100%;margin-bottom:6px}
  .svc-status-text{flex:0 0 auto}
  .metrics-strip{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>

<header>
  <div class="container">
    <div class="header-inner">
      <div>
        <div class="brand-name">Clinical AI Platform</div>
        <div class="brand-sub" id="brand-sub">Estado del Sistema</div>
      </div>
      <button class="lang-btn" id="lang-btn" onclick="toggleLang()">EN</button>
    </div>
  </div>
</header>

<main>
  <div class="container">

    <!-- Overall -->
    <div class="overall-card checking" id="overall-card">
      <div class="dot dot-lg checking" id="overall-dot"></div>
      <div>
        <div class="overall-title" id="overall-title">Verificando…</div>
        <div class="overall-sub" id="overall-sub"></div>
      </div>
    </div>

    <!-- Platform metrics -->
    <div class="metrics-strip" id="metrics-strip">
      <div class="metric-item">
        <div class="metric-label" id="ml-p50">Latencia p50</div>
        <div class="metric-value"><span id="mv-p50">—</span><span class="metric-unit"> ms</span></div>
        <div class="metric-source" id="ms-src">API Gateway · Prometheus</div>
      </div>
      <div class="metric-item">
        <div class="metric-label" id="ml-p95">Latencia p95</div>
        <div class="metric-value"><span id="mv-p95">—</span><span class="metric-unit"> ms</span></div>
        <div class="metric-source">&nbsp;</div>
      </div>
      <div class="metric-item">
        <div class="metric-label" id="ml-rps">Solicitudes / min</div>
        <div class="metric-value"><span id="mv-rps">—</span></div>
        <div class="metric-source">&nbsp;</div>
      </div>
      <div class="metric-item">
        <div class="metric-label" id="ml-err">Tasa de Error</div>
        <div class="metric-value"><span id="mv-err">—</span><span class="metric-unit"> %</span></div>
        <div class="metric-source">&nbsp;</div>
      </div>
    </div>

    <!-- Core services -->
    <div class="section">
      <div class="section-title" id="header-core">Servicios Principales</div>
      <div class="card" id="group-core">
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
      </div>
    </div>

    <!-- AI Models -->
    <div class="section">
      <div class="section-title" id="header-models">Modelos de IA</div>
      <div class="card" id="group-models">
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
        <div class="skeleton-row"><div class="skel sk-dot"></div><div class="skel sk-name"></div><div class="skel sk-bars"></div><div class="skel sk-pct"></div></div>
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

<div class="tooltip" id="tooltip"></div>

<script>
var lang=localStorage.getItem('cap_lang')||'es';
var lastData=null,countdownSec=30,countdownId=null;

var S={
  brand_sub:      {es:'Estado del Sistema',                en:'System Status'},
  checking:       {es:'Verificando…',                en:'Checking…'},
  overall_op:     {es:'Todos los Sistemas Operacionales', en:'All Systems Operational'},
  overall_deg:    {es:'Rendimiento Degradado',            en:'Degraded Performance'},
  overall_partial:{es:'Interrupción Parcial',        en:'Partial Outage'},
  overall_major:  {es:'Interrupción Mayor',          en:'Major Service Outage'},
  svc_of:         {es:'de',                               en:'of'},
  svc_ok:         {es:'servicios operacionales',          en:'services operational'},
  header_core:    {es:'Servicios Principales',            en:'Core Services'},
  header_models:  {es:'Modelos de IA',                    en:'AI Models'},
  st_op:          {es:'Operacional',                      en:'Operational'},
  st_deg:         {es:'Degradado',                        en:'Degraded'},
  st_partial:     {es:'Interrupción Parcial',        en:'Partial Outage'},
  st_major:       {es:'Interrupción Mayor',          en:'Major Outage'},
  st_unknown:     {es:'Desconocido',                      en:'Unknown'},
  ml_p50:         {es:'Latencia p50',                     en:'Latency p50'},
  ml_p95:         {es:'Latencia p95',                     en:'Latency p95'},
  ml_rps:         {es:'Solicitudes / min',                en:'Requests / min'},
  ml_err:         {es:'Tasa de Error',                    en:'Error Rate'},
  ms_src:         {es:'API Gateway · Prometheus',    en:'API Gateway · Prometheus'},
  last_chk:       {es:'Verificado: ',                     en:'Last checked: '},
  refresh_in:     {es:'Actualizando en ',                 en:'Refreshing in '},
  refresh_now:    {es:'Actualizando…',               en:'Refreshing…'},
  err:            {es:'Error de conexión',           en:'Connection error'},
  days_ago:       {es:'hace ## días',                en:'## days ago'},
  today:          {es:'hoy',                              en:'today'},
  uptime_day:     {es:'Disponibilidad: ##%',              en:'Uptime: ##%'},
  no_data:        {es:'Sin datos',                        en:'No data'},
};

var OVERALL_KEY={operational:'overall_op',degraded:'overall_deg',partial_outage:'overall_partial',major_outage:'overall_major'};
var STATUS_KEY={operational:'st_op',degraded:'st_deg',partial_outage:'st_partial',major_outage:'st_major',unknown:'st_unknown'};

function t(k){return(S[k]&&S[k][lang])||k;}
function el(id){return document.getElementById(id);}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function toggleLang(){
  lang=lang==='es'?'en':'es';
  localStorage.setItem('cap_lang',lang);
  applyLang();
  if(lastData)renderStatus(lastData);
}

function applyLang(){
  document.documentElement.lang=lang;
  el('lang-btn').textContent=lang==='es'?'EN':'ES';
  el('brand-sub').textContent=t('brand_sub');
  if(!lastData)el('overall-title').textContent=t('checking');
  el('header-core').textContent=t('header_core');
  el('header-models').textContent=t('header_models');
  el('ml-p50').textContent=t('ml_p50');
  el('ml-p95').textContent=t('ml_p95');
  el('ml-rps').textContent=t('ml_rps');
  el('ml-err').textContent=t('ml_err');
  el('ms-src').textContent=t('ms_src');
}

function barClass(pct){
  if(pct===null)return 'bar-none';
  if(pct>=99)return 'bar-op';
  if(pct>=95)return 'bar-deg';
  if(pct>=80)return 'bar-partial';
  return 'bar-out';
}

var tooltip=el('tooltip');
function showTip(e,html){tooltip.innerHTML=html;tooltip.style.opacity='1';moveTip(e);}
function moveTip(e){tooltip.style.left=(e.clientX+12)+'px';tooltip.style.top=(e.clientY-30)+'px';}
function hideTip(){tooltip.style.opacity='0';}

function buildBars(history){
  var html='<div class="history-bars">';
  var days=history.length;
  history.forEach(function(d,i){
    var ago=days-1-i;
    var label=ago===0?t('today'):t('days_ago').replace('##',ago);
    var uptipLine=d.uptime_pct!==null
      ?t('uptime_day').replace('##',d.uptime_pct)
      :t('no_data');
    var tipHtml=esc(d.date)+'<br>'+esc(uptipLine);
    html+='<div class="bar '+barClass(d.uptime_pct)+'" '
      +'onmouseenter="showTip(event,\''+tipHtml+'\')" '
      +'onmousemove="moveTip(event)" '
      +'onmouseleave="hideTip()"></div>';
  });
  html+='</div>';
  return html;
}

function renderStatus(data){
  var overall=data.overall;
  var card=el('overall-card');
  card.className='overall-card '+overall;
  el('overall-dot').className='dot dot-lg '+overall;
  el('overall-title').textContent=t(OVERALL_KEY[overall]||'checking');
  var ops=data.services.filter(function(s){return s.status==='operational';}).length;
  var total=data.services.length;
  el('overall-sub').textContent=ops+' '+t('svc_of')+' '+total+' '+t('svc_ok');

  // Platform metrics
  var m=data.platform_metrics||{};
  el('mv-p50').textContent=m.latency_p50_ms!=null?m.latency_p50_ms:'—';
  el('mv-p95').textContent=m.latency_p95_ms!=null?m.latency_p95_ms:'—';
  el('mv-rps').textContent=m.requests_per_min!=null?m.requests_per_min:'—';
  el('mv-err').textContent=m.error_rate_pct!=null?m.error_rate_pct.toFixed(2):'0.00';

  var groups={core:[],models:[]};
  data.services.forEach(function(s){if(groups[s.group])groups[s.group].push(s);});

  ['core','models'].forEach(function(gid){
    var container=el('group-'+gid);
    if(!container)return;
    var html='';
    groups[gid].forEach(function(s){
      var name=lang==='es'?s.name_es:s.name_en;
      var stKey=STATUS_KEY[s.status]||'st_unknown';
      var valid=s.history.filter(function(d){return d.uptime_pct!==null;});
      var avgPct=valid.length?Math.round(valid.reduce(function(a,d){return a+d.uptime_pct;},0)/valid.length*10)/10:null;
      var pctLabel=avgPct!=null?avgPct+'%':'—';
      var rangeLabel=valid.length?valid.length+' '+(lang==='es'?'días':'days'):'—';

      html+='<div class="service-row">'
        +'<div class="svc-left"><div class="dot dot-sm '+s.status+'"></div>'
        +'<div class="svc-name">'+esc(name)+'</div></div>'
        +'<div class="svc-history">'
        +buildBars(s.history)
        +'<div class="history-meta"><span class="uptime-pct">'+pctLabel+'</span>'
        +'<span class="history-range">'+esc(rangeLabel)+'</span></div>'
        +'</div>'
        +'<div class="svc-status-text '+s.status+'">'+t(stKey)+'</div>'
        +'</div>';
    });
    container.innerHTML=html;
  });

  var checkedAt=new Date(data.checked_at);
  var locale=lang==='es'?'es-MX':'en-US';
  el('last-checked').innerHTML='<span class="dot-live"></span>'+t('last_chk')
    +checkedAt.toLocaleTimeString(locale,{hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

function startCountdown(){
  countdownSec=30;
  if(countdownId)clearInterval(countdownId);
  countdownId=setInterval(function(){
    countdownSec--;
    if(countdownSec<=0){clearInterval(countdownId);el('countdown').textContent=t('refresh_now');fetchStatus();}
    else{el('countdown').textContent=t('refresh_in')+countdownSec+'s';}
  },1000);
  el('countdown').textContent=t('refresh_in')+countdownSec+'s';
}

function fetchStatus(){
  fetch('/status/api')
    .then(function(r){return r.json();})
    .then(function(data){lastData=data;renderStatus(data);startCountdown();})
    .catch(function(){
      el('overall-card').className='overall-card major_outage';
      el('overall-dot').className='dot dot-lg major_outage';
      el('overall-title').textContent=t('err');
      el('overall-sub').textContent='';
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
