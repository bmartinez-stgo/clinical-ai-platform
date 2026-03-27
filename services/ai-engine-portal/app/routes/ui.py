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
        max-width: 11ch;
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
      .auth { grid-column: span 4; }
      .docs { grid-column: span 8; }
      .diag { grid-column: span 12; }
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
      @media (max-width: 920px) {
        .auth, .docs, .diag { grid-column: span 12; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div class="kicker">Clinical AI Platform</div>
        <h1>AI Engine Portal for auth, parsing, and inference.</h1>
        <p class="lead">
          This portal talks to the same public routes exposed through the gateway. Use it to get a token, upload a PDF,
          and send normalized observations to diagnostics without jumping between tools.
        </p>
      </section>

      <section class="grid">
        <article class="card auth">
          <h2>Auth</h2>
          <p>Get a bearer token and keep it in local storage for the next requests.</p>
          <div class="row">
            <label>Username<input id="username" type="text" value="admin" /></label>
            <label>Password<input id="password" type="password" value="admin123" /></label>
          </div>
          <div class="actions">
            <button id="loginBtn">Get Token</button>
            <button id="clearTokenBtn" class="secondary" type="button">Clear Token</button>
          </div>
          <div class="status" id="authStatus">No token loaded.</div>
          <div class="result" style="margin-top: 14px;">
            <div class="pill" id="tokenState">Token missing</div>
            <pre id="tokenOutput">{"token": null}</pre>
          </div>
        </article>

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
      </section>
    </main>

    <script>
      const tokenKey = "clinical-ai-engine-portal-token";
      const tokenOutput = document.getElementById("tokenOutput");
      const tokenState = document.getElementById("tokenState");
      const authStatus = document.getElementById("authStatus");
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
        renderTokenState();
      }

      function renderTokenState() {
        const token = readToken();
        tokenState.textContent = token ? "Token loaded" : "Token missing";
        authStatus.textContent = token ? "Bearer token ready for requests." : "No token loaded.";
        tokenOutput.textContent = pretty({ token });
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

      document.getElementById("loginBtn").addEventListener("click", async () => {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;
        authStatus.textContent = "Requesting token...";
        try {
          const payload = await requestJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
          });
          writeToken(payload.access_token || null);
          authStatus.textContent = "Token retrieved.";
        } catch (error) {
          authStatus.textContent = "Login failed.";
          tokenOutput.textContent = String(error.message || error);
        }
      });

      document.getElementById("clearTokenBtn").addEventListener("click", () => {
        writeToken(null);
      });

      document.getElementById("parseBtn").addEventListener("click", async () => {
        const token = readToken();
        const fileInput = document.getElementById("labFile");
        const file = fileInput.files[0];
        if (!token) {
          parseStatus.textContent = "Load a bearer token first.";
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
          diagnosticStatus.textContent = "Load a bearer token first.";
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

      renderTokenState();
    </script>
  </body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def portal_index() -> HTMLResponse:
    return HTMLResponse(HTML)
