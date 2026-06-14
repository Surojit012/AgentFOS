/* ========================================
   AgentFOS — Playground Logic
   ======================================== */

// ── Protocol Data ──
const PROTOCOLS = [
    { key: "ondo", name: "Ondo Finance", class: "Tokenized Treasury", apy: "4.7%", risk: "100/100", color: "#74b9ff" },
    { key: "zoth", name: "Zoth", class: "Emerging Market Credit", apy: "10.2%", risk: "75/100", color: "#ffd93d" },
    { key: "maple", name: "Maple Finance", class: "Institutional Private Credit", apy: "8.5%", risk: "90/100", color: "#a29bfe" },
    { key: "centrifuge", name: "Centrifuge", class: "Real World Asset Loans", apy: "7.2%", risk: "100/100", color: "#00d4aa" },
    { key: "backed", name: "Backed Finance", class: "Tokenized ETFs & Bonds", apy: "5.1%", risk: "100/100", color: "#6c5ce7" },
    { key: "opentrade", name: "OpenTrade", class: "Trade Finance", apy: "6.8%", risk: "90/100", color: "#e17055" },
];

// ── Render Protocol Cards ──
function renderProtocols() {
    const grid = document.getElementById("protocolsGrid");
    grid.innerHTML = PROTOCOLS.map(p => `
        <div class="protocol-card">
            <div class="pc-name">${p.name}</div>
            <div class="pc-class">${p.class}</div>
            <div class="pc-metrics">
                <div>
                    <div class="pc-metric-label">APY</div>
                    <div class="pc-metric-value green">${p.apy}</div>
                </div>
                <div>
                    <div class="pc-metric-label">Risk Score</div>
                    <div class="pc-metric-value blue">${p.risk}</div>
                </div>
            </div>
        </div>
    `).join("");
}

// ── Playground Endpoint Templates ──
const TEMPLATES = {
    agent: {
        method: "POST",
        body: JSON.stringify({
            query: "Find low risk RWAs above treasury yields",
            capital: 100000,
            risk_tolerance: "low"
        }, null, 2)
    },
    opportunity: {
        method: "POST",
        body: JSON.stringify({
            asset_classes: ["all"],
            min_apy: 0
        }, null, 2)
    },
    risk: {
        method: "POST",
        body: JSON.stringify({
            protocol_key: "ondo"
        }, null, 2)
    },
    policy: {
        method: "POST",
        body: JSON.stringify({
            action: "allocate",
            protocol_key: "maple",
            amount: 50000,
            risk_tolerance: "low"
        }, null, 2)
    },
    allocate: {
        method: "POST",
        body: JSON.stringify({
            capital: 100000,
            risk_preference: "low"
        }, null, 2)
    },
    health: {
        method: "GET",
        body: "// No request body — GET request"
    }
};

let currentEndpoint = "agent";

// ── Endpoint Selection ──
function initEndpoints() {
    const buttons = document.querySelectorAll(".pg-endpoint");
    const textarea = document.getElementById("requestBody");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            buttons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentEndpoint = btn.dataset.endpoint;
            const tmpl = TEMPLATES[currentEndpoint];
            textarea.value = tmpl.body;
            textarea.readOnly = tmpl.method === "GET";

            // Clear response
            document.getElementById("responseBody").innerHTML =
                '<span class="response-placeholder">// Click "Send" to see the response</span>';
            document.getElementById("responseStatus").textContent = "";
            document.getElementById("responseStatus").className = "pg-status";
        });
    });

    // Set initial
    textarea.value = TEMPLATES.agent.body;
}

// ── Send Request ──
async function sendRequest() {
    const baseUrl = document.getElementById("baseUrl").value.replace(/\/$/, "");
    const tmpl = TEMPLATES[currentEndpoint];
    const url = `${baseUrl}/${currentEndpoint}`;
    const sendBtn = document.getElementById("sendBtn");
    const responseBody = document.getElementById("responseBody");
    const responseStatus = document.getElementById("responseStatus");

    // Loading state
    sendBtn.classList.add("loading");
    sendBtn.innerHTML = `<svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Sending...`;
    responseBody.innerHTML = '<span class="response-placeholder">// Waiting for response...</span>';
    responseStatus.textContent = "";
    responseStatus.className = "pg-status";

    const startTime = performance.now();

    try {
        const fetchOpts = {
            method: tmpl.method,
            headers: { "Content-Type": "application/json" },
        };

        if (tmpl.method === "POST") {
            const bodyText = document.getElementById("requestBody").value;
            fetchOpts.body = bodyText;
        }

        const res = await fetch(url, fetchOpts);
        const elapsed = Math.round(performance.now() - startTime);
        const data = await res.json();

        responseBody.textContent = JSON.stringify(data, null, 2);
        responseStatus.textContent = `${res.status} • ${elapsed}ms`;
        responseStatus.className = `pg-status ${res.ok ? "success" : "error"}`;
    } catch (err) {
        const elapsed = Math.round(performance.now() - startTime);
        responseBody.textContent = `Error: ${err.message}\n\nMake sure your AgentFOS server is running:\n  uvicorn main:app --host 0.0.0.0 --port 8000`;
        responseStatus.textContent = `ERR • ${elapsed}ms`;
        responseStatus.className = "pg-status error";
    } finally {
        sendBtn.classList.remove("loading");
        sendBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg> Send`;
    }
}

// ── Add spin animation ──
const style = document.createElement("style");
style.textContent = `@keyframes spin { to { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }`;
document.head.appendChild(style);

// ── Smooth scroll for nav links ──
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener("click", e => {
        e.preventDefault();
        const target = document.querySelector(a.getAttribute("href"));
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
});

// ── Init ──
renderProtocols();
initEndpoints();
