from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HTML = """<!doctype html>
<html lang="en">
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
      .shell {
        max-width: 1280px;
        margin: 0 auto;
        padding: 32px 20px 48px;
      }
      .hero {
        display: grid;
        gap: 16px;
        margin-bottom: 24px;
      }
      .kicker {
        color: var(--accent);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 12px;
      }
      h1 {
        margin: 0;
        font-size: clamp(2rem, 5vw, 3.8rem);
        line-height: 0.95;
        max-width: 12ch;
      }
      .lead {
        max-width: 760px;
        margin: 0;
        font-size: 1rem;
        color: var(--muted);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 18px;
      }
      .card {
        grid-column: span 12;
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 20px;
        box-shadow: var(--shadow);
        padding: 20px;
      }
      .card h2 {
        margin: 0 0 12px;
        font-size: 1.1rem;
      }
      .card p {
        margin: 0 0 16px;
        color: var(--muted);
      }
      .docs { grid-column: span 7; }
      .diag { grid-column: span 5; }
      .session { grid-column: span 12; }
      .login-shell {
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
      }
      .login-card {
        width: min(100%, 460px);
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 24px;
        box-shadow: var(--shadow);
        padding: 28px;
      }
      .row {
        display: grid;
        gap: 12px;
        margin-bottom: 12px;
      }
      label {
        display: grid;
        gap: 6px;
        font-size: 0.9rem;
        font-weight: 600;
      }
      input, textarea {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 12px 14px;
        font: inherit;
        background: #fff;
      }
      textarea {
        min-height: 180px;
        resize: vertical;
      }
      button {
        appearance: none;
        border: 0;
        border-radius: 999px;
        background: var(--brand);
        color: white;
        padding: 12px 18px;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
      }
      button.secondary {
        background: var(--brand-dark);
      }
      button.danger {
        background: var(--danger);
      }
      button:disabled {
        opacity: 0.55;
        cursor: wait;
      }
      .actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .status {
        margin-top: 12px;
        font-size: 0.9rem;
        color: var(--muted);
      }
      .status.error {
        color: var(--danger);
      }
      pre {
        margin: 0;
        padding: 16px;
        overflow: auto;
        border-radius: 16px;
        background: #11201c;
        color: #dff7ef;
        font-size: 0.85rem;
        line-height: 1.45;
      }
      .result {
        display: grid;
        gap: 12px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(13, 122, 95, 0.1);
        color: var(--brand-dark);
        font-weight: 700;
        font-size: 0.85rem;
      }
      .toolbar {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: center;
        margin-bottom: 20px;
      }
      .toolbar-meta {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        align-items: center;
      }
      [hidden] { display: none !important; }
      code {
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
      }
      @media (max-width: 920px) {
        .docs, .diag, .session { grid-column: span 12; }
        .toolbar {
          align-items: flex-start;
          flex-direction: column;
        }
      }
    </style>
  </head>
  <body>
    <main id="loginView" class="login-shell">
      <section class="login-card">
        <div class="kicker">Clinical AI Platform</div>
        <h1 style="max-width: 10ch; margin-top: 10px;">AI Engine Portal</h1>
        <p class="lead" style="max-width: none; margin-top: 10px;">
          Sign in to access document parsing and diagnostic workflows through the production gateway.
        </p>
        <div class="row" style="margin-top: 18px;">
          <label>Username<input id="username" type="text" value="admin" autocomplete="username" /></label>
          <label>Password<input id="password" type="password" value="admin123" autocomplete="current-password" /></label>
        </div>
        <div class="actions">
          <button id="loginBtn">Sign In</button>
        </div>
        <div class="status" id="loginStatus">Waiting for credentials.</div>
      </section>
    </main>

    <main id="portalView" class="shell" hidden>
      <section class="hero">
        <div class="kicker">Clinical AI Platform</div>
        <h1>AI Engine Portal</h1>
        <p class="lead">
          Operate the production parsing and inference services from one place after authentication.
        </p>
      </section>

      <section class="toolbar">
        <div>
          <div class="pill" id="sessionState">Session active</div>
        </div>
        <div class="toolbar-meta">
          <div class="status" id="sessionStatus">Authenticated.</div>
          <button id="logoutBtn" class="danger" type="button">Sign Out</button>
        </div>
      </section>

      <section class="grid">
        <article class="card docs">
          <h2>Document Reader</h2>
          <p>Upload a PDF or image to <code>/documents/labs/parse</code> through the public gateway.</p>
          <div class="row">
            <label>Laboratory file<input id="labFile" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" /></label>
          </div>
          <div class="actions">
            <button id="parseBtn">Parse Laboratory Report</button>
          </div>
          <div class="status" id="parseStatus">Waiting for a file.</div>
          <div class="result" style="margin-top: 14px;">
            <pre id="parseOutput">{}</pre>
          </div>
        </article>

        <article class="card diag">
          <h2>Diagnostics</h2>
          <p>Paste or reuse normalized observations and send them to <code>/diagnostics/infer</code>.</p>
          <div class="row">
            <label>Diagnostic payload JSON<textarea id="diagnosticPayload">{
  "patient_context": {},
  "observations": [],
  "request_context": {
    "goal": "Summarize notable findings"
  }
}</textarea></label>
          </div>
          <div class="actions">
            <button id="useParseBtn" class="secondary" type="button">Use Last Parse Output</button>
            <button id="diagnosticsBtn">Run Diagnostics</button>
          </div>
          <div class="status" id="diagnosticStatus">Waiting for input.</div>
          <div class="result" style="margin-top: 14px;">
            <pre id="diagnosticOutput">{}</pre>
          </div>
        </article>

        <article class="card session">
          <h2>Session</h2>
          <p>The portal keeps the bearer token in local storage and validates it before exposing production functions.</p>
          <div class="result">
            <pre id="tokenOutput">{"token": null}</pre>
          </div>
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
      const diagnosticOutput = document.getElementById("diagnosticOutput");
      const diagnosticStatus = document.getElementById("diagnosticStatus");
      const diagnosticPayload = document.getElementById("diagnosticPayload");

      let lastParseResult = null;

      function pretty(value) {
        return JSON.stringify(value, null, 2);
      }

      function readToken() {
        return window.localStorage.getItem(tokenKey);
      }

      function writeToken(token) {
        if (token) {
          window.localStorage.setItem(tokenKey, token);
        } else {
          window.localStorage.removeItem(tokenKey);
        }
      }

      function setLoginMessage(message, isError = false) {
        loginStatus.textContent = message;
        loginStatus.className = isError ? "status error" : "status";
      }

      function setSessionMessage(message, isError = false) {
        sessionStatus.textContent = message;
        sessionStatus.className = isError ? "status error" : "status";
      }

      function showLogin() {
        loginView.hidden = false;
        portalView.hidden = true;
      }

      function showPortal() {
        loginView.hidden = true;
        portalView.hidden = false;
      }

      function clearSession() {
        writeToken(null);
        sessionState.textContent = "Session inactive";
        setSessionMessage("Authentication required.");
        tokenOutput.textContent = pretty({ token: null });
        showLogin();
      }

      function renderSession(token) {
        sessionState.textContent = "Session active";
        setSessionMessage("Authenticated.");
        tokenOutput.textContent = pretty({ token });
        showPortal();
      }

      async function requestJson(url, options) {
        const response = await fetch(url, options);
        const text = await response.text();
        let body;
        try {
          body = text ? JSON.parse(text) : {};
        } catch {
          body = { raw: text };
        }
        if (!response.ok) {
          throw new Error(pretty({ status: response.status, body }));
        }
        return body;
      }

      async function validateToken(token) {
        return requestJson("/auth/validate", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });
      }

      async function bootstrapSession() {
        const token = readToken();
        if (!token) {
          clearSession();
          return;
        }

        setLoginMessage("Validating existing session...");
        try {
          const payload = await validateToken(token);
          renderSession(token);
          setSessionMessage(`Authenticated as ${payload.subject}. Expires at epoch ${payload.expires_at}.`);
        } catch (error) {
          clearSession();
          setLoginMessage("Session expired. Sign in again.", true);
        }
      }

      document.getElementById("loginBtn").addEventListener("click", async () => {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;
        setLoginMessage("Signing in...");
        try {
          const payload = await requestJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
          });
          writeToken(payload.access_token || null);
          renderSession(payload.access_token || null);
          setSessionMessage(`Authenticated. Token lifetime: ${payload.expires_in} seconds.`);
        } catch (error) {
          setLoginMessage("Sign-in failed.", true);
          tokenOutput.textContent = String(error.message || error);
        }
      });

      document.getElementById("logoutBtn").addEventListener("click", () => {
        clearSession();
        setLoginMessage("Signed out.");
      });

      document.getElementById("parseBtn").addEventListener("click", async () => {
        const token = readToken();
        const fileInput = document.getElementById("labFile");
        const file = fileInput.files[0];
        if (!token) {
          clearSession();
          return;
        }
        if (!file) {
          parseStatus.textContent = "Choose a PDF or image first.";
          return;
        }

        const formData = new FormData();
        formData.append("file", file);
        parseStatus.textContent = "Parsing document...";
        try {
          const payload = await requestJson("/documents/labs/parse", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
            body: formData,
          });
          lastParseResult = payload;
          parseOutput.textContent = pretty(payload);
          parseStatus.textContent = "Document parsed.";
        } catch (error) {
          parseStatus.textContent = "Parse request failed.";
          parseOutput.textContent = String(error.message || error);
        }
      });

      document.getElementById("useParseBtn").addEventListener("click", () => {
        if (!lastParseResult) {
          diagnosticStatus.textContent = "No parse result available yet.";
          return;
        }
        diagnosticPayload.value = pretty({
          patient_context: {
            patient: lastParseResult.patient || {},
            report: lastParseResult.report || {},
          },
          observations: lastParseResult.observations || [],
          request_context: {
            goal: "Summarize notable findings",
          },
        });
        diagnosticStatus.textContent = "Inserted the last parse output.";
      });

      document.getElementById("diagnosticsBtn").addEventListener("click", async () => {
        const token = readToken();
        if (!token) {
          clearSession();
          return;
        }
        diagnosticStatus.textContent = "Running diagnostics...";
        try {
          const payload = JSON.parse(diagnosticPayload.value);
          const result = await requestJson("/diagnostics/infer", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
          });
          diagnosticOutput.textContent = pretty(result);
          diagnosticStatus.textContent = "Diagnostics response received.";
        } catch (error) {
          diagnosticStatus.textContent = "Diagnostics request failed.";
          diagnosticOutput.textContent = String(error.message || error);
        }
      });

      bootstrapSession();
    </script>
  </body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def portal_index() -> HTMLResponse:
    return HTMLResponse(HTML)
