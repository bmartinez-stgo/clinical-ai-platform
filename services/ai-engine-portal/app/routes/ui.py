from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HTML = """<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Engine Portal</title>
    <style>
      :root {
        --bg: #f3efe5;
        --paper: #fffdf8;
        --ink: #18211f;
        --muted: #6a756f;
        --line: #d8d1c0;
        --brand: #0d7a5f;
        --brand-dark: #0a5d49;
        --accent: #d66b2d;
        --danger: #a33d2a;
        --warn: #b37a0a;
        --shadow: 0 14px 34px rgba(24, 33, 31, 0.08);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(214, 107, 45, 0.10), transparent 32%),
          radial-gradient(circle at top right, rgba(13, 122, 95, 0.12), transparent 28%),
          linear-gradient(180deg, #f8f4ea 0%, #f1ece1 100%);
      }
      .shell { max-width: 1280px; margin: 0 auto; padding: 32px 20px 48px; }
      .hero { display: grid; gap: 16px; margin-bottom: 24px; }
      .kicker { color: var(--accent); font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; font-size: 12px; }
      h1 { margin: 0; font-size: clamp(2rem, 5vw, 3.8rem); line-height: 0.95; max-width: 12ch; }
      .lead { max-width: 760px; margin: 0; font-size: 1rem; color: var(--muted); }
      .grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 18px; }
      .card { grid-column: span 12; background: var(--paper); border: 1px solid var(--line); border-radius: 20px; box-shadow: var(--shadow); padding: 24px; }
      .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
      .card h2 { margin: 0; font-size: 1.1rem; }
      .card p { margin: 0 0 16px; color: var(--muted); }
      .login-shell { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
      .login-card { width: min(100%, 460px); background: var(--paper); border: 1px solid var(--line); border-radius: 24px; box-shadow: var(--shadow); padding: 28px; }
      .section-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin: 20px 0 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
      .form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
      .form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      .form-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }
      .span-full { grid-column: 1 / -1; }
      .row { display: grid; gap: 12px; margin-bottom: 12px; }
      label { display: grid; gap: 5px; font-size: 0.85rem; font-weight: 600; }
      label .hint { font-weight: 400; color: var(--muted); font-size: 0.78rem; }
      input[type="text"], input[type="number"], input[type="password"], input[type="date"], select, textarea {
        width: 100%; border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; font: inherit; background: #fff; font-size: 0.9rem;
      }
      input[type="text"]:focus, input[type="number"]:focus, select:focus, textarea:focus {
        outline: 2px solid var(--brand); outline-offset: -1px;
      }
      textarea { min-height: 100px; resize: vertical; }
      textarea.code { font-family: "IBM Plex Mono", monospace; font-size: 0.82rem; min-height: 140px; }
      .checks { display: flex; flex-wrap: wrap; gap: 8px; }
      .check-item { display: flex; align-items: center; gap: 6px; background: rgba(13,122,95,0.06); border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; font-size: 0.85rem; cursor: pointer; user-select: none; }
      .check-item input { width: auto; margin: 0; }
      button { appearance: none; border: 0; border-radius: 999px; background: var(--brand); color: white; padding: 11px 20px; font: inherit; font-size: 0.9rem; font-weight: 700; cursor: pointer; }
      button.secondary { background: var(--brand-dark); }
      button.ghost { background: transparent; border: 1.5px solid var(--brand); color: var(--brand); }
      button.danger { background: var(--danger); }
      button.sm { padding: 7px 14px; font-size: 0.82rem; }
      button:disabled { opacity: 0.55; cursor: wait; }
      .actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
      .status { margin-top: 10px; font-size: 0.88rem; color: var(--muted); }
      .status.error { color: var(--danger); }
      .status.ok { color: var(--brand-dark); }
      pre { margin: 0; padding: 16px; overflow: auto; border-radius: 14px; background: #11201c; color: #dff7ef; font-size: 0.82rem; line-height: 1.45; font-family: "IBM Plex Mono", monospace; }
      .pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px; font-weight: 700; font-size: 0.82rem; }
      .pill-green { background: rgba(13, 122, 95, 0.12); color: var(--brand-dark); }
      .pill-orange { background: rgba(214,107,45,0.12); color: #9e4e1a; }
      .pill-red { background: rgba(163,61,42,0.12); color: var(--danger); }
      .pill-blue { background: rgba(30,80,200,0.10); color: #1e50c8; }
      .toolbar { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 20px; }
      .toolbar-meta { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
      .flag-card { border: 1px solid var(--line); border-radius: 14px; padding: 14px; margin-bottom: 10px; }
      .flag-card h3 { margin: 0 0 8px; font-size: 1rem; display: flex; align-items: center; gap: 8px; }
      .flag-section { font-size: 0.85rem; margin-top: 8px; }
      .flag-section strong { display: block; color: var(--muted); margin-bottom: 4px; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
      .flag-section ul { margin: 0; padding-left: 18px; }
      .flag-section li { margin-bottom: 3px; }
      .result-section { margin-top: 16px; }
      .result-section h3 { font-size: 0.88rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted); margin: 0 0 8px; }
      .result-list { margin: 0; padding-left: 20px; }
      .result-list li { margin-bottom: 4px; font-size: 0.92rem; }
      .reasoning-box { background: #f6f2e8; border: 1px solid var(--line); border-radius: 12px; padding: 14px; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }
      .disclaimer { font-size: 0.82rem; color: var(--muted); font-style: italic; margin-top: 12px; padding: 10px 14px; background: rgba(180,120,0,0.07); border-radius: 10px; }
      .chat-window { display: flex; flex-direction: column; gap: 10px; max-height: 420px; overflow-y: auto; padding: 12px; background: #f6f2e8; border: 1px solid var(--line); border-radius: 14px; margin-bottom: 12px; }
      .chat-bubble { max-width: 80%; padding: 10px 14px; border-radius: 14px; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; }
      .chat-bubble.user { align-self: flex-end; background: var(--brand); color: white; border-bottom-right-radius: 4px; }
      .chat-bubble.assistant { align-self: flex-start; background: white; border: 1px solid var(--line); border-bottom-left-radius: 4px; }
      .chat-input-row { display: flex; gap: 8px; align-items: flex-end; }
      .chat-input-row textarea { flex: 1; min-height: 44px; max-height: 120px; resize: vertical; border-radius: 12px; }
      .chat-empty { color: var(--muted); font-size: 0.85rem; text-align: center; padding: 20px 0; }
      .timing-badge { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; background: rgba(13,122,95,0.08); color: var(--brand-dark); font-size: 0.78rem; font-weight: 700; font-family: "IBM Plex Mono", monospace; }
      .parse-summary { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 10px; }
      .parse-summary th { text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); padding: 4px 8px; border-bottom: 1px solid var(--line); }
      .parse-summary td { padding: 6px 8px; border-bottom: 1px solid rgba(216,209,192,0.5); }
      .parse-summary tr:last-child td { border-bottom: none; }
      [hidden] { display: none !important; }
      code { font-family: "IBM Plex Mono", "SFMono-Regular", monospace; }
      @media (max-width: 720px) {
        .form-grid-2, .form-grid-3 { grid-template-columns: 1fr; }
        .toolbar { align-items: flex-start; flex-direction: column; }
      }
    </style>
  </head>
  <body>
    <!-- LOGIN -->
    <main id="loginView" class="login-shell">
      <section class="login-card">
        <div class="kicker">Clinical AI Platform</div>
        <h1 style="max-width: 10ch; margin-top: 10px;">AI Engine Portal</h1>
        <p class="lead" style="max-width: none; margin-top: 10px;">
          Accede al portal de parseo y diagnóstico clínico asistido por IA.
        </p>
        <div class="row" style="margin-top: 18px;">
          <label>Usuario<input id="username" type="text" value="admin" autocomplete="username" /></label>
          <label>Contraseña<input id="password" type="password" value="admin123" autocomplete="current-password" /></label>
        </div>
        <div class="actions">
          <button id="loginBtn">Iniciar sesión</button>
        </div>
        <div class="status" id="loginStatus">Esperando credenciales.</div>
      </section>
    </main>

    <!-- PORTAL -->
    <main id="portalView" class="shell" hidden>
      <section class="hero">
        <div class="kicker">Clinical AI Platform</div>
        <h1>AI Engine Portal</h1>
        <p class="lead">Parseo de PDFs de laboratorio e inferencia diagnóstica de enfermedades autoinmunes.</p>
      </section>

      <section class="toolbar">
        <div style="display:flex;align-items:center;gap:12px;">
          <div class="pill pill-green" id="sessionState">Sesión activa</div>
          <label style="display:flex;align-items:center;gap:6px;font-size:0.85rem;font-weight:600;margin:0;">
            Idioma
            <select id="langSelect" style="border-radius:8px;padding:5px 10px;border:1px solid var(--line);font:inherit;font-size:0.85rem;background:#fff;">
              <option value="es" selected>Español</option>
              <option value="en">English</option>
            </select>
          </label>
        </div>
        <div class="toolbar-meta">
          <div class="status" id="sessionStatus">Autenticado.</div>
          <button id="logoutBtn" class="danger sm" type="button">Cerrar sesión</button>
        </div>
      </section>

      <section class="grid">

        <!-- STEP 1: PDF PARSE -->
        <article class="card">
          <div class="card-header">
            <h2>Paso 1 — Parsear PDFs de laboratorio</h2>
          </div>
          <p>Carga uno o varios PDFs o imágenes. Cada archivo se procesará como un reporte independiente y se agregará a la serie de laboratorios.</p>
          <div class="row">
            <label>Archivos de laboratorio<span class="hint">puedes seleccionar varios a la vez</span>
              <input id="labFile" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" multiple />
            </label>
          </div>
          <div class="actions">
            <button id="parseBtn">Parsear reportes</button>
            <button id="useParseBtn" class="ghost sm" type="button" hidden>Usar resultados en Paso 2</button>
          </div>
          <div class="status" id="parseStatus">Esperando archivo.</div>
          <div style="margin-top: 14px;" id="parseResultArea" hidden>
            <div id="parseSummary"></div>
            <details style="margin-top:10px;">
              <summary style="cursor:pointer;font-size:0.85rem;color:var(--muted);">Ver JSON del último archivo</summary>
              <pre id="parseOutput" style="margin-top:8px;">{}</pre>
            </details>
          </div>
        </article>

        <!-- STEP 2: CLINICAL FORM -->
        <article class="card">
          <div class="card-header">
            <h2>Paso 2 — Datos clínicos</h2>
          </div>
          <p>Completa la información clínica del paciente y envía a inferencia diagnóstica.</p>

          <!-- Patient -->
          <div class="section-title">Paciente</div>
          <div class="form-grid-3">
            <label>Edad (años)<input id="p_age" type="number" min="0" max="120" placeholder="p. ej. 34" /></label>
            <label>Sexo
              <select id="p_sex">
                <option value="female">Femenino</option>
                <option value="male">Masculino</option>
                <option value="other">Otro</option>
              </select>
            </label>
            <label>Etnicidad<span class="hint">opcional</span><input id="p_ethnicity" type="text" placeholder="p. ej. mestiza" /></label>
            <label>Peso (kg)<span class="hint">opcional</span><input id="p_weight" type="number" step="0.1" placeholder="65.0" /></label>
            <label>Talla (cm)<span class="hint">opcional</span><input id="p_height" type="number" placeholder="162" /></label>
          </div>

          <!-- History -->
          <div class="section-title">Antecedentes clínicos</div>
          <div class="form-grid-2">
            <label>Antec. familiares autoinmunes<span class="hint">separados por coma</span>
              <input id="h_family" type="text" placeholder="p. ej. LES, AR" />
            </label>
            <label>Comorbilidades<span class="hint">separadas por coma</span>
              <input id="h_comorbidities" type="text" placeholder="p. ej. HTA, DM2" />
            </label>
            <label>Medicamentos actuales<span class="hint">separados por coma</span>
              <input id="h_medications" type="text" placeholder="p. ej. Hidroxicloroquina, Prednisona" />
            </label>
            <label>Alergias<span class="hint">separadas por coma</span>
              <input id="h_allergies" type="text" placeholder="p. ej. Penicilina" />
            </label>
            <label>N.° embarazos<span class="hint">opcional</span><input id="h_pregnancies" type="number" min="0" placeholder="0" /></label>
            <label>N.° abortos espontáneos<span class="hint">opcional</span><input id="h_miscarriages" type="number" min="0" placeholder="0" /></label>
            <label>Fecha inicio síntomas<span class="hint">opcional</span><input id="h_onset_date" type="date" /></label>
            <label>Duración síntomas (días)<span class="hint">opcional</span><input id="h_duration" type="number" min="0" placeholder="90" /></label>
          </div>

          <!-- Vitals -->
          <div class="section-title">Signos vitales</div>
          <div class="form-grid-3">
            <label>Presión sistólica (mmHg)<span class="hint">opcional</span><input id="v_systolic" type="number" placeholder="120" /></label>
            <label>Presión diastólica (mmHg)<span class="hint">opcional</span><input id="v_diastolic" type="number" placeholder="80" /></label>
            <label>Temperatura (°C)<span class="hint">opcional</span><input id="v_temp" type="number" step="0.1" placeholder="36.6" /></label>
            <label>Frec. cardíaca (lpm)<span class="hint">opcional</span><input id="v_hr" type="number" placeholder="72" /></label>
          </div>

          <!-- Physical Findings -->
          <div class="section-title">Hallazgos físicos — sistemas afectados</div>
          <div class="checks" id="systemChecks">
            <label class="check-item"><input type="checkbox" value="piel"> Piel / Tegumentario</label>
            <label class="check-item"><input type="checkbox" value="articular"> Articular / Musculoesquelético</label>
            <label class="check-item"><input type="checkbox" value="renal"> Renal / Urinario</label>
            <label class="check-item"><input type="checkbox" value="cardiovascular"> Cardiovascular</label>
            <label class="check-item"><input type="checkbox" value="pulmonar"> Pulmonar / Respiratorio</label>
            <label class="check-item"><input type="checkbox" value="neurologico"> Neurológico</label>
            <label class="check-item"><input type="checkbox" value="hematologico"> Hematológico</label>
            <label class="check-item"><input type="checkbox" value="gastrointestinal"> Gastrointestinal / Hepático</label>
            <label class="check-item"><input type="checkbox" value="ocular"> Ocular</label>
            <label class="check-item"><input type="checkbox" value="vascular"> Vascular / Trombótico</label>
            <label class="check-item"><input type="checkbox" value="tiroideo"> Tiroideo / Endocrino</label>
          </div>
          <div style="margin-top: 10px;">
            <label>Descripción libre de hallazgos<span class="hint">opcional</span>
              <textarea id="pf_free_text" placeholder="p. ej. Eritema malar, alopecia difusa, sinovitis bilateral de rodillas"></textarea>
            </label>
          </div>

          <!-- Lab Series -->
          <div class="section-title">Serie de laboratorios (JSON)</div>
          <p style="margin-bottom: 8px;">Edita o completa el JSON generado por el Paso 1. Debe ser un arreglo de LabSnapshot.</p>
          <label>
            <textarea id="labSeriesJson" class="code" style="min-height: 180px;" placeholder='[{"report_date": "2024-11-15", "results": [...]}]'></textarea>
          </label>
          <div class="actions" style="margin-top: 8px;">
            <button id="useParseBtn2" class="ghost sm" type="button">Cargar desde Paso 1</button>
          </div>
          <div class="status" id="labSeriesStatus"></div>

          <!-- Imaging -->
          <div class="section-title">Estudios de imagen <span style="font-weight:400;font-size:0.8rem;">(opcional)</span></div>
          <label>
            <textarea id="imagingJson" class="code" placeholder='[{"study_date": "2024-10-01", "modality": "RX tórax", "findings": "Sin infiltrados"}]'></textarea>
          </label>

          <!-- Biopsies -->
          <div class="section-title">Biopsias <span style="font-weight:400;font-size:0.8rem;">(opcional)</span></div>
          <label>
            <textarea id="biopsiesJson" class="code" placeholder='[{"date": "2024-09-12", "tissue": "Piel", "findings": "Depósitos de IgG en dermis"}]'></textarea>
          </label>

          <!-- Diagnosis & Observations -->
          <div class="section-title">Impresión diagnóstica y notas</div>
          <div class="form-grid-2">
            <label>Diagnóstico clínico del médico
              <input id="clinical_diagnosis" type="text" placeholder="p. ej. LES probable, en estudio" />
            </label>
            <label>Observaciones adicionales<span class="hint">opcional</span>
              <textarea id="doctor_observations" placeholder="Contexto adicional que considere relevante..."></textarea>
            </label>
          </div>

          <!-- Focus -->
          <div class="section-title">Foco de análisis</div>
          <div class="checks" id="focusChecks">
            <label class="check-item"><input type="checkbox" value="autoimmune" checked> Autoinmune</label>
            <label class="check-item"><input type="checkbox" value="metabolic"> Metabólico</label>
            <label class="check-item"><input type="checkbox" value="infectious"> Infeccioso</label>
            <label class="check-item"><input type="checkbox" value="oncologic"> Oncológico</label>
          </div>

          <div class="actions" style="margin-top: 24px;">
            <button id="diagnoseBtn">Enviar a inferencia diagnóstica</button>
          </div>
          <div class="status" id="diagnoseStatus">Esperando datos.</div>
        </article>

        <!-- STEP 3: RESULT -->
        <article class="card" id="resultCard" hidden>
          <div class="card-header">
            <h2>Resultado diagnóstico</h2>
            <div id="confidencePill"></div>
          </div>

          <div id="flagsContainer"></div>

          <div class="result-section">
            <h3>Diagnóstico diferencial</h3>
            <ul class="result-list" id="differentialList"></ul>
          </div>

          <div class="result-section">
            <h3>Seguimiento recomendado</h3>
            <ul class="result-list" id="followupList"></ul>
          </div>

          <div class="result-section">
            <h3>Razonamiento</h3>
            <div class="reasoning-box" id="reasoningBox"></div>
          </div>

          <div class="disclaimer" id="disclaimerBox"></div>

          <details style="margin-top: 16px;">
            <summary style="cursor: pointer; font-size: 0.85rem; color: var(--muted);">Ver JSON completo</summary>
            <pre id="diagnosticOutput" style="margin-top: 10px;">{}</pre>
          </details>
        </article>

        <!-- STEP 4: CHAT -->
        <article class="card" id="chatCard" hidden>
          <div class="card-header">
            <h2>Consultas de seguimiento</h2>
            <span class="pill pill-green">IA conversacional</span>
          </div>
          <p>Haz preguntas de seguimiento sobre este paciente. El asistente tiene acceso completo al resultado diagnóstico y los datos clínicos.</p>
          <div class="chat-window" id="chatWindow">
            <div class="chat-empty" id="chatEmpty">Escribe una pregunta para comenzar.</div>
          </div>
          <div class="chat-input-row">
            <textarea id="chatInput" placeholder="p. ej. ¿Debería pedir anti-dsDNA dada la trombocitopenia?" rows="2"></textarea>
            <button id="chatSendBtn" class="sm">Enviar</button>
          </div>
          <div class="status" id="chatStatus"></div>
        </article>

        <!-- SESSION -->
        <article class="card">
          <h2>Sesión</h2>
          <p>Token JWT almacenado en local storage, validado al cargar el portal.</p>
          <pre id="tokenOutput">{"token": null}</pre>
        </article>

      </section>
    </main>

    <script>
      const tokenKey = "clinical-ai-engine-portal-token";
      const loginView = document.getElementById("loginView");
      const portalView = document.getElementById("portalView");
      const loginStatus = document.getElementById("loginStatus");
      const sessionState = document.getElementById("sessionState");
      const sessionStatus = document.getElementById("sessionStatus");
      const tokenOutput = document.getElementById("tokenOutput");
      const parseOutput = document.getElementById("parseOutput");
      const parseStatus = document.getElementById("parseStatus");
      const parseResultArea = document.getElementById("parseResultArea");
      const parseSummary = document.getElementById("parseSummary");
      const useParseBtn = document.getElementById("useParseBtn");
      const useParseBtn2 = document.getElementById("useParseBtn2");
      const labSeriesStatus = document.getElementById("labSeriesStatus");
      const diagnoseStatus = document.getElementById("diagnoseStatus");
      const diagnosticOutput = document.getElementById("diagnosticOutput");
      const resultCard = document.getElementById("resultCard");

      let parsedFiles = [];
      function getLang() { return document.getElementById("langSelect").value; }
      function fmtMs(ms) { return ms < 1000 ? `${ms}ms` : `${(ms/1000).toFixed(1)}s`; }

      function pretty(v) { return JSON.stringify(v, null, 2); }
      function readToken() { return window.localStorage.getItem(tokenKey); }
      function writeToken(t) { t ? window.localStorage.setItem(tokenKey, t) : window.localStorage.removeItem(tokenKey); }
      function csvToList(s) { return s.split(",").map(x => x.trim()).filter(Boolean); }

      function setStatus(el, msg, kind = "") {
        el.textContent = msg;
        el.className = "status" + (kind ? " " + kind : "");
      }

      function showLogin() { loginView.hidden = false; portalView.hidden = true; }
      function showPortal() { loginView.hidden = true; portalView.hidden = false; }

      function clearSession() {
        writeToken(null);
        sessionState.textContent = "Sesión inactiva";
        setStatus(sessionStatus, "Se requiere autenticación.");
        tokenOutput.textContent = pretty({ token: null });
        showLogin();
      }

      function renderSession(token) {
        sessionState.textContent = "Sesión activa";
        setStatus(sessionStatus, "Autenticado.");
        tokenOutput.textContent = pretty({ token });
        showPortal();
      }

      async function requestJson(url, options) {
        const response = await fetch(url, options);
        const text = await response.text();
        let body;
        try { body = text ? JSON.parse(text) : {}; } catch { body = { raw: text }; }
        if (!response.ok) throw new Error(pretty({ status: response.status, body }));
        return body;
      }

      async function bootstrapSession() {
        const token = readToken();
        if (!token) { clearSession(); return; }
        setStatus(loginStatus, "Validando sesión existente...");
        try {
          const payload = await requestJson("/auth/validate", {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` },
          });
          renderSession(token);
          setStatus(sessionStatus, `Autenticado como ${payload.subject}.`);
        } catch {
          clearSession();
          setStatus(loginStatus, "Sesión expirada. Inicia sesión nuevamente.", "error");
        }
      }

      document.getElementById("loginBtn").addEventListener("click", async () => {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;
        setStatus(loginStatus, "Iniciando sesión...");
        try {
          const payload = await requestJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
          });
          writeToken(payload.access_token || null);
          renderSession(payload.access_token || null);
          setStatus(sessionStatus, `Autenticado. Vigencia: ${payload.expires_in}s.`);
        } catch (error) {
          setStatus(loginStatus, "Error al iniciar sesión.", "error");
          tokenOutput.textContent = String(error.message || error);
        }
      });

      document.getElementById("logoutBtn").addEventListener("click", () => {
        clearSession();
        setStatus(loginStatus, "Sesión cerrada.");
      });

      document.getElementById("parseBtn").addEventListener("click", async () => {
        const token = readToken();
        const files = [...document.getElementById("labFile").files];
        if (!token) { clearSession(); return; }
        if (!files.length) { setStatus(parseStatus, "Elige al menos un PDF o imagen.", "error"); return; }

        document.getElementById("parseBtn").disabled = true;
        parsedFiles = [];
        parseResultArea.hidden = false;
        useParseBtn.hidden = true;
        parseSummary.innerHTML = "";

        const totalStart = performance.now();
        let allOk = true;

        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          setStatus(parseStatus, `Parseando archivo ${i + 1} / ${files.length}: ${file.name}...`);
          const fileStart = performance.now();
          try {
            const formData = new FormData();
            formData.append("file", file);
            const payload = await requestJson(`/documents/labs/parse?language=${getLang()}`, {
              method: "POST",
              headers: { "Authorization": `Bearer ${token}` },
              body: formData,
            });
            const elapsed = Math.round(performance.now() - fileStart);
            parsedFiles.push({ filename: file.name, result: payload, elapsed });
            parseOutput.textContent = pretty(payload);
          } catch (error) {
            const elapsed = Math.round(performance.now() - fileStart);
            parsedFiles.push({ filename: file.name, result: null, elapsed, error: String(error.message || error) });
            allOk = false;
          }
        }

        const totalElapsed = Math.round(performance.now() - totalStart);

        // Render summary table
        const rows = parsedFiles.map(f => {
          if (f.error) {
            return `<tr><td>${f.filename}</td><td style="color:var(--danger)">Error</td><td>—</td><td><span class="timing-badge">⏱ ${fmtMs(f.elapsed)}</span></td></tr>`;
          }
          const count = (f.result.observations || []).length;
          const date = f.result.report?.report_date || "—";
          return `<tr><td>${f.filename}</td><td>${count} analitos</td><td>${date}</td><td><span class="timing-badge">⏱ ${fmtMs(f.elapsed)}</span></td></tr>`;
        }).join("");
        parseSummary.innerHTML = `
          <table class="parse-summary">
            <thead><tr><th>Archivo</th><th>Analitos</th><th>Fecha reporte</th><th>Tiempo</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
          <div style="margin-top:8px;font-size:0.82rem;color:var(--muted);">
            Total: ${files.length} archivo(s) — <span class="timing-badge">⏱ ${fmtMs(totalElapsed)} total</span>
          </div>`;

        const successCount = parsedFiles.filter(f => f.result).length;
        if (successCount > 0) {
          useParseBtn.hidden = false;
          setStatus(parseStatus, `${successCount} de ${files.length} archivo(s) parseados.`, allOk ? "ok" : "");
        } else {
          setStatus(parseStatus, "Todos los archivos fallaron al parsear.", "error");
        }
        document.getElementById("parseBtn").disabled = false;
      });

      function loadLabSeriesFromParse() {
        const successful = parsedFiles.filter(f => f.result);
        if (!successful.length) {
          setStatus(labSeriesStatus, "No hay resultados de parseo disponibles.", "error");
          return;
        }
        const labSeries = successful.map(f => {
          const reportDate = (f.result.report && f.result.report.report_date)
            || new Date().toISOString().split("T")[0];
          const results = (f.result.observations || []).map(obs => ({
            loinc_code: obs.loinc_code || null,
            test_name: obs.test_name_normalized || obs.test_name_raw || "",
            value: obs.value,
            unit: obs.unit_ucum || obs.unit_raw || null,
            ref_low: obs.reference_range?.low ?? null,
            ref_high: obs.reference_range?.high ?? null,
            interpretation: obs.interpretation || null,
          }));
          return { report_date: reportDate, results };
        });
        const totalObs = labSeries.reduce((acc, s) => acc + s.results.length, 0);
        document.getElementById("labSeriesJson").value = pretty(labSeries);
        setStatus(labSeriesStatus, `${labSeries.length} snapshot(s) cargados — ${totalObs} analitos en total.`, "ok");
      }

      useParseBtn.addEventListener("click", loadLabSeriesFromParse);
      useParseBtn2.addEventListener("click", loadLabSeriesFromParse);

      function buildDiagnosticPayload() {
        const age = parseInt(document.getElementById("p_age").value);
        if (!age || age < 0) throw new Error("La edad del paciente es requerida.");

        const labSeriesRaw = document.getElementById("labSeriesJson").value.trim();
        if (!labSeriesRaw) throw new Error("La serie de laboratorios es requerida.");
        let labSeries;
        try { labSeries = JSON.parse(labSeriesRaw); } catch { throw new Error("JSON de laboratorios inválido."); }

        const clinicalDiagnosis = document.getElementById("clinical_diagnosis").value.trim();
        if (!clinicalDiagnosis) throw new Error("El diagnóstico clínico del médico es requerido.");

        const affected_systems = [...document.querySelectorAll("#systemChecks input:checked")].map(el => el.value);
        const focus = [...document.querySelectorAll("#focusChecks input:checked")].map(el => el.value);
        if (!focus.length) throw new Error("Selecciona al menos un foco de análisis.");

        const imagingRaw = document.getElementById("imagingJson").value.trim();
        let imaging = [];
        if (imagingRaw) {
          try { imaging = JSON.parse(imagingRaw); } catch { throw new Error("JSON de imagenología inválido."); }
        }

        const biopsiesRaw = document.getElementById("biopsiesJson").value.trim();
        let biopsies = [];
        if (biopsiesRaw) {
          try { biopsies = JSON.parse(biopsiesRaw); } catch { throw new Error("JSON de biopsias inválido."); }
        }

        const v_systolic = document.getElementById("v_systolic").value;
        const v_diastolic = document.getElementById("v_diastolic").value;
        const v_temp = document.getElementById("v_temp").value;
        const v_hr = document.getElementById("v_hr").value;

        const h_pregnancies = document.getElementById("h_pregnancies").value;
        const h_miscarriages = document.getElementById("h_miscarriages").value;
        const h_duration = document.getElementById("h_duration").value;
        const h_onset = document.getElementById("h_onset_date").value;

        const p_weight = document.getElementById("p_weight").value;
        const p_height = document.getElementById("p_height").value;
        const p_ethnicity = document.getElementById("p_ethnicity").value.trim();

        return {
          patient: {
            age,
            sex: document.getElementById("p_sex").value,
            ...(p_ethnicity && { ethnicity: p_ethnicity }),
            ...(p_weight && { weight_kg: parseFloat(p_weight) }),
            ...(p_height && { height_cm: parseFloat(p_height) }),
          },
          history: {
            family_autoimmune: csvToList(document.getElementById("h_family").value),
            comorbidities: csvToList(document.getElementById("h_comorbidities").value),
            current_medications: csvToList(document.getElementById("h_medications").value),
            allergies: csvToList(document.getElementById("h_allergies").value),
            ...(h_pregnancies !== "" && { pregnancies: parseInt(h_pregnancies) }),
            ...(h_miscarriages !== "" && { miscarriages: parseInt(h_miscarriages) }),
            ...(h_onset && { symptom_onset_date: h_onset }),
            ...(h_duration !== "" && { symptom_duration_days: parseInt(h_duration) }),
          },
          vitals: {
            ...(v_systolic && { blood_pressure_systolic: parseInt(v_systolic) }),
            ...(v_diastolic && { blood_pressure_diastolic: parseInt(v_diastolic) }),
            ...(v_temp && { temperature_celsius: parseFloat(v_temp) }),
            ...(v_hr && { heart_rate: parseInt(v_hr) }),
          },
          physical_findings: {
            affected_systems,
            free_text: document.getElementById("pf_free_text").value.trim() || null,
          },
          lab_series: labSeries,
          imaging,
          biopsies,
          clinical_diagnosis: clinicalDiagnosis,
          doctor_observations: document.getElementById("doctor_observations").value.trim() || null,
          focus,
          language: getLang(),
        };
      }

      function likelihoodPill(likelihood) {
        const map = { high: "pill-red", moderate: "pill-orange", low: "pill-blue" };
        const labels = { high: "Alta probabilidad", moderate: "Probabilidad moderada", low: "Baja probabilidad" };
        return `<span class="pill ${map[likelihood] || 'pill-blue'}">${labels[likelihood] || likelihood}</span>`;
      }

      function renderDiagnosticResult(result) {
        const confMap = { high: "pill-red", moderate: "pill-orange", low: "pill-blue" };
        const confLabels = { high: "Confianza alta", moderate: "Confianza moderada", low: "Confianza baja" };
        document.getElementById("confidencePill").innerHTML =
          `<span class="pill ${confMap[result.confidence] || 'pill-blue'}">${confLabels[result.confidence] || result.confidence}</span>`;

        const flagsHtml = (result.autoimmune_flags || []).map(flag => `
          <div class="flag-card">
            <h3>${flag.condition} ${likelihoodPill(flag.likelihood)}</h3>
            ${flag.supporting_findings && flag.supporting_findings.length ? `
              <div class="flag-section">
                <strong>Hallazgos de apoyo</strong>
                <ul>${flag.supporting_findings.map(f => `<li>${f}</li>`).join("")}</ul>
              </div>` : ""}
            ${flag.missing_workup && flag.missing_workup.length ? `
              <div class="flag-section">
                <strong>Estudios pendientes</strong>
                <ul>${flag.missing_workup.map(f => `<li>${f}</li>`).join("")}</ul>
              </div>` : ""}
          </div>`).join("");
        document.getElementById("flagsContainer").innerHTML = flagsHtml || "<p style='color:var(--muted)'>Sin banderas autoinmunes.</p>";

        document.getElementById("differentialList").innerHTML =
          (result.differential || []).map(d => `<li>${d}</li>`).join("") || "<li>—</li>";

        document.getElementById("followupList").innerHTML =
          (result.recommended_followup || []).map(f => `<li>${f}</li>`).join("") || "<li>—</li>";

        document.getElementById("reasoningBox").textContent = result.reasoning || "";
        document.getElementById("disclaimerBox").textContent = result.disclaimer || "";
        document.getElementById("diagnosticOutput").textContent = pretty(result);
        resultCard.hidden = false;
        resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      let _lastDiagnosticPayload = null;

      document.getElementById("diagnoseBtn").addEventListener("click", async () => {
        const token = readToken();
        if (!token) { clearSession(); return; }

        let payload;
        try {
          payload = buildDiagnosticPayload();
        } catch (err) {
          setStatus(diagnoseStatus, err.message, "error");
          return;
        }

        setStatus(diagnoseStatus, "Enviando a inferencia diagnóstica... (puede tardar hasta 2 min)");
        document.getElementById("diagnoseBtn").disabled = true;
        resultCard.hidden = true;
        const inferStart = performance.now();

        try {
          const result = await requestJson("/diagnostics/diagnose", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
          });
          const inferElapsed = Math.round(performance.now() - inferStart);
          renderDiagnosticResult(result);
          setStatus(diagnoseStatus, `Inferencia completada — ⏱ ${fmtMs(inferElapsed)}`, "ok");
          openChatForResult(payload, result);
        } catch (error) {
          setStatus(diagnoseStatus, "Error en inferencia diagnóstica.", "error");
          diagnosticOutput.textContent = String(error.message || error);
          resultCard.hidden = false;
        } finally {
          document.getElementById("diagnoseBtn").disabled = false;
        }
      });

      // CHAT
      let chatContext = null;    // diagnostic_context (DiagnosticRequest payload)
      let chatResult = null;     // diagnostic_result (DiagnosticResponse)
      let chatMessages = [];     // [{role, content}]

      const chatCard = document.getElementById("chatCard");
      const chatWindow = document.getElementById("chatWindow");
      const chatEmpty = document.getElementById("chatEmpty");
      const chatInput = document.getElementById("chatInput");
      const chatSendBtn = document.getElementById("chatSendBtn");
      const chatStatus = document.getElementById("chatStatus");

      function appendBubble(role, content) {
        chatEmpty.hidden = true;
        const div = document.createElement("div");
        div.className = `chat-bubble ${role}`;
        div.textContent = content;
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }

      function appendThinking() {
        chatEmpty.hidden = true;
        const div = document.createElement("div");
        div.className = "chat-bubble assistant";
        div.id = "chatThinking";
        div.textContent = "…";
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return div;
      }

      chatSendBtn.addEventListener("click", async () => {
        const token = readToken();
        if (!token) { clearSession(); return; }
        const text = chatInput.value.trim();
        if (!text) return;
        if (!chatContext || !chatResult) {
          setStatus(chatStatus, "Primero ejecuta una inferencia diagnóstica.", "error");
          return;
        }

        chatMessages.push({ role: "user", content: text });
        appendBubble("user", text);
        chatInput.value = "";
        chatSendBtn.disabled = true;
        setStatus(chatStatus, "El asistente está procesando...");

        const thinking = appendThinking();

        try {
          const res = await requestJson("/chat/message", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify({
              diagnostic_context: chatContext,
              diagnostic_result: chatResult,
              messages: chatMessages,
              language: getLang(),
            }),
          });
          thinking.remove();
          chatMessages.push({ role: "assistant", content: res.message });
          appendBubble("assistant", res.message);
          setStatus(chatStatus, "");
        } catch (err) {
          thinking.remove();
          chatMessages.pop();
          setStatus(chatStatus, "Error al procesar la consulta.", "error");
        } finally {
          chatSendBtn.disabled = false;
        }
      });

      chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          chatSendBtn.click();
        }
      });

      function openChatForResult(context, result) {
        chatContext = context;
        chatResult = result;
        chatMessages = [];
        chatWindow.innerHTML = "";
        chatEmpty.hidden = false;
        chatWindow.appendChild(chatEmpty);
        chatCard.hidden = false;
        chatCard.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      bootstrapSession();
    </script>
  </body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def portal_index() -> HTMLResponse:
    return HTMLResponse(HTML)
