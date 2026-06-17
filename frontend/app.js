/* ========================================
   AgentFOS — Playground Logic
   ======================================== */

const PHAROS_TX_BASE = "https://atlantic.pharosscan.xyz/tx/";
const REQUEST_TIMEOUT_MS = 120000;

function getRequestErrorMessage(err) {
    const message = err?.message || String(err);
    if (err?.name === "AbortError" || message.toLowerCase().includes("aborted")) {
        return `Request timed out after ${Math.round(REQUEST_TIMEOUT_MS / 1000)}s. Render may still be waking up, or the backend may be waiting on the Pharos write path.`;
    }
    return message;
}

// ── Protocol Data ──
const PROTOCOLS = [
    { key: "ondo", name: "Ondo Finance", class: "Tokenized Treasury", apy: "4.7%", risk: "100/100", color: "#FB6702" },
    { key: "zoth", name: "Zoth", class: "Emerging Market Credit", apy: "10.2%", risk: "75/100", color: "#DCDBDD" },
    { key: "maple", name: "Maple Finance", class: "Institutional Private Credit", apy: "8.5%", risk: "90/100", color: "#8C8F9E" },
    { key: "centrifuge", name: "Centrifuge", class: "Real World Asset Loans", apy: "7.2%", risk: "100/100", color: "#FCFCFC" },
    { key: "backed", name: "Backed Finance", class: "Tokenized ETFs & Bonds", apy: "5.1%", risk: "100/100", color: "#52566E" },
    { key: "opentrade", name: "OpenTrade", class: "Trade Finance", apy: "6.8%", risk: "90/100", color: "#FB6702" },
];

// ── Render Protocol Cards ──
function renderProtocols() {
    const grid = document.getElementById("protocolsGrid");
    grid.innerHTML = PROTOCOLS.map((p, index) => `
        <div class="protocol-card reveal" style="--reveal-delay: ${index * 70}ms">
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
    allocate: {
        method: "POST",
        body: JSON.stringify({
            capital: 100000,
            risk: "medium",
            min_apy_spread: 0
        }, null, 2)
    },
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
            risk_level: "medium",
            min_apy: 0,
            min_tvl: 0
        }, null, 2)
    },
    risk: {
        method: "POST",
        body: JSON.stringify({
            protocol: "ondo"
        }, null, 2)
    },
    policy: {
        method: "POST",
        body: JSON.stringify({
            action: "allocate",
            amount: 50000,
            asset: "maple",
            risk_tolerance: "low",
            max_single_allocation: 0.6,
            min_risk_score: 50
        }, null, 2)
    },
    health: {
        method: "GET",
        body: "// No request body — GET request"
    }
};

let currentEndpoint = "allocate";
let requestInFlight = false;

function formatPct(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
    return `${Number(value).toFixed(2)}%`;
}

function formatUsd(value) {
    return Number(value || 0).toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
    });
}

function shortHash(hash) {
    return hash ? `${hash.slice(0, 10)}...${hash.slice(-8)}` : "--";
}

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

            document.getElementById("responseBody").innerHTML =
                '<span class="response-placeholder">// Click "Send" to see the response</span>';
            document.getElementById("responseStatus").textContent = "";
            document.getElementById("responseStatus").className = "pg-status";
            if (currentEndpoint !== "risk") {
                hideRiskBreakdown();
            }
        });
    });

    textarea.value = TEMPLATES.allocate.body;
}

// ── Send Request ──
async function sendRequest() {
    if (requestInFlight) return;
    requestInFlight = true;

    const baseUrl = document.getElementById("baseUrl").value.replace(/\/$/, "");
    const tmpl = TEMPLATES[currentEndpoint];
    const url = `${baseUrl}/${currentEndpoint}`;
    const sendBtn = document.getElementById("sendBtn");
    const responseBody = document.getElementById("responseBody");
    const responseStatus = document.getElementById("responseStatus");

    sendBtn.classList.add("loading");
    sendBtn.innerHTML = `<svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Sending...`;
    responseBody.innerHTML = '<span class="response-placeholder">// Waiting for response...</span>';
    responseStatus.textContent = "";
    responseStatus.className = "pg-status";

    if (currentEndpoint === "allocate") {
        setProofPending();
    }

    const startTime = performance.now();

    let timeout;

    try {
        const controller = new AbortController();
        timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        const fetchOpts = {
            method: tmpl.method,
            headers: { "Content-Type": "application/json" },
            signal: controller.signal,
        };

        if (tmpl.method === "POST") {
            fetchOpts.body = document.getElementById("requestBody").value;
        }

        const res = await fetch(url, fetchOpts);
        clearTimeout(timeout);
        const elapsed = Math.round(performance.now() - startTime);
        const data = await res.json();

        responseBody.textContent = JSON.stringify(data, null, 2);
        responseStatus.textContent = `${res.status} • ${elapsed}ms`;
        responseStatus.className = `pg-status ${res.ok ? "success" : "error"}`;

        if (currentEndpoint === "allocate" && res.ok) {
            renderAllocationDashboard(data);
        }
        if (currentEndpoint === "risk" && res.ok) {
            renderRiskBreakdown(data);
        }
    } catch (err) {
        const elapsed = Math.round(performance.now() - startTime);
        const message = getRequestErrorMessage(err);
        responseBody.textContent = `Error: ${message}\n\nMake sure the API Base URL points to a live AgentFOS backend.`;
        responseStatus.textContent = `ERR • ${elapsed}ms`;
        responseStatus.className = "pg-status error";
        if (currentEndpoint === "allocate") {
            setProofError(message);
        }
        if (currentEndpoint === "risk") {
            hideRiskBreakdown();
        }
    } finally {
        clearTimeout(timeout);
        requestInFlight = false;
        sendBtn.classList.remove("loading");
        sendBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg> Send`;
    }
}

function setProofPending() {
    document.getElementById("proofDot").className = "proof-dot pending";
    document.getElementById("proofTitle").textContent = "Submitting allocation to Pharos...";
    document.getElementById("proofStatus").textContent = "pending";
    document.getElementById("proofTx").textContent = "--";
    document.getElementById("proofError").textContent = "";
    setProofLink(null);
}

function setProofError(message) {
    document.getElementById("proofDot").className = "proof-dot error";
    document.getElementById("proofTitle").textContent = "Allocation request failed";
    document.getElementById("proofStatus").textContent = "failed";
    document.getElementById("proofError").textContent = message;
}

function renderAllocationDashboard(data) {
    const top = data.allocations?.[0];
    const dashboard = document.getElementById("allocationDashboard");

    document.getElementById("portfolioApy").textContent = formatPct(data.portfolio_avg_apy);
    document.getElementById("portfolioRisk").textContent = data.portfolio_avg_risk_score ?? "--";
    document.getElementById("portfolioSpread").textContent = formatPct(data.portfolio_spread);
    document.getElementById("treasuryRate").textContent = `Treasury ${formatPct(data.treasury_benchmark)}`;
    document.getElementById("dataSource").textContent = `${data.data_source || "unknown"} data`;
    document.getElementById("narrative").textContent = data.narrative || "No allocation narrative returned.";

    if (top) {
        document.getElementById("topProtocol").textContent = top.name;
        document.getElementById("topProtocolMeta").textContent =
            `${top.protocol_key} • ${top.risk_score}/100 risk • ${Math.round(top.apy * 100)} APY bps • ${top.allocation_pct}%`;
    } else {
        document.getElementById("topProtocol").textContent = "No eligible protocol";
        document.getElementById("topProtocolMeta").textContent = "Adjust risk or spread filters";
    }

    renderProof(data, top);
    renderAllocationRows(data.allocations || []);

    dashboard.classList.remove("is-updating");
    void dashboard.offsetWidth;
    dashboard.classList.add("is-updating");
    window.setTimeout(() => dashboard.classList.remove("is-updating"), 700);
}

function renderProof(data, top) {
    const status = data.onchain_status || "unknown";
    const txHash = data.onchain_tx_hash;
    const isSuccess = status === "success" && txHash;

    document.getElementById("proofDot").className = `proof-dot ${isSuccess ? "success" : "error"}`;
    document.getElementById("proofTitle").textContent = isSuccess
        ? `Stored ${top?.protocol_key || "allocation"} on Pharos`
        : "Allocation computed; on-chain write needs attention";
    document.getElementById("proofStatus").textContent = status;
    document.getElementById("proofTx").textContent = shortHash(txHash);
    document.getElementById("proofError").textContent = data.onchain_error || "";

    const link = document.getElementById("proofLink");
    if (isSuccess) {
        setProofLink(`${PHAROS_TX_BASE}${txHash}`);
    } else {
        setProofLink(null);
    }
}

function setProofLink(url) {
    const link = document.getElementById("proofLink");
    if (!url) {
        link.className = "proof-link disabled";
        link.href = "#";
        link.setAttribute("aria-disabled", "true");
        link.removeAttribute("data-url");
        return;
    }

    link.className = "proof-link";
    link.href = url;
    link.dataset.url = url;
    link.setAttribute("aria-disabled", "false");
}

function renderAllocationRows(allocations) {
    const rows = document.getElementById("allocationRows");
    if (!allocations.length) {
        rows.innerHTML = '<tr><td colspan="6">No eligible protocols returned.</td></tr>';
        return;
    }

    rows.innerHTML = allocations.map((item, index) => `
        <tr class="row-enter ${index === 0 ? "top-row" : ""}" style="--row-delay: ${index * 60}ms">
            <td>${index === 0 ? "ON-CHAIN · " : ""}${item.name}</td>
            <td>${formatPct(item.apy)}</td>
            <td>${item.risk_score}/100</td>
            <td>${item.allocation_pct}%</td>
            <td>${formatUsd(item.allocation_amount)}</td>
            <td>${formatPct(item.apy_vs_treasury)}</td>
        </tr>
    `).join("");
}

function provenanceClass(provenance) {
    if (provenance === "live") return "live";
    if (provenance === "degraded") return "degraded";
    return "insufficient";
}

function formatDimensionLabel(key) {
    const labels = {
        liquidity: "Liquidity",
        maturity: "Maturity",
        transparency: "Transparency",
        concentration: "Concentration",
        yield_sustainability: "Yield Sustain."
    };
    if (labels[key]) return labels[key];
    return key
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}

function formatRiskTimestamp(value) {
    if (!value) return "--";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

function getDataQuality(breakdown) {
    const provenances = Object.values(breakdown).map(value => value.provenance || "insufficient");
    if (provenances.includes("insufficient")) {
        return { className: "insufficient", label: "Insufficient Data" };
    }
    if (provenances.includes("degraded")) {
        return { className: "degraded", label: "Degraded Data" };
    }
    return { className: "live", label: "Live Data" };
}

function formatProvenanceLabel(provenance) {
    if (provenance === "live") return "Live Data";
    if (provenance === "degraded") return "Degraded Data";
    return "Insufficient Data";
}

function renderRiskBreakdown(data) {
    const panel = document.getElementById("riskBreakdownPanel");
    const rows = document.getElementById("riskBreakdownRows");
    const breakdown = data.breakdown || data.factors?.breakdown;

    if (!breakdown) {
        hideRiskBreakdown();
        return;
    }

    document.getElementById("riskBreakdownScore").textContent =
        `${data.risk_score ?? "--"} / 100`;
    document.getElementById("riskBreakdownRating").textContent = data.rating || "--";
    document.getElementById("riskBreakdownConfidence").textContent =
        data.overall_confidence || data.factors?.overall_confidence || "--";
    document.getElementById("riskScoredAt").textContent = formatRiskTimestamp(data.scored_at);
    document.getElementById("riskEngineVersion").textContent =
        data.schema_version ? `Risk Engine v${data.schema_version}` : "Risk Engine v2";

    const quality = getDataQuality(breakdown);
    document.getElementById("riskDataQuality").innerHTML = `
        <span>Data Quality</span>
        <strong><i class="quality-dot ${quality.className}"></i>${quality.label}</strong>
    `;

    rows.innerHTML = Object.entries(breakdown).map(([key, value], index) => {
        const provenance = value.provenance || "insufficient";
        return `
            <div class="risk-breakdown-row row-enter" style="--row-delay: ${index * 60}ms">
                <span>${formatDimensionLabel(key)}</span>
                <strong>${value.score}/${value.max}</strong>
                <em class="${provenanceClass(provenance)}">${formatProvenanceLabel(provenance)}</em>
            </div>
        `;
    }).join("");

    panel.classList.remove("hidden");
}

function hideRiskBreakdown() {
    document.getElementById("riskBreakdownPanel").classList.add("hidden");
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

document.getElementById("proofLink").addEventListener("click", event => {
    const url = event.currentTarget.dataset.url;
    if (!url) {
        event.preventDefault();
        return;
    }

    event.preventDefault();
    const opened = window.open(url, "_blank", "noopener,noreferrer");
    if (!opened) {
        window.location.href = url;
    }
});

function initRevealAnimations() {
    const revealTargets = document.querySelectorAll([
        ".section-header",
        ".feature-card",
        ".protocol-card",
        ".flow-step",
        ".allocation-dashboard",
        ".allocation-table-wrap",
        ".playground-container"
    ].join(","));

    revealTargets.forEach((target, index) => {
        target.classList.add("reveal");
        if (!target.style.getPropertyValue("--reveal-delay")) {
            target.style.setProperty("--reveal-delay", `${Math.min(index % 6, 5) * 70}ms`);
        }
    });

    if (!("IntersectionObserver" in window)) {
        revealTargets.forEach(target => target.classList.add("in-view"));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.16, rootMargin: "0px 0px -60px 0px" });

    revealTargets.forEach(target => observer.observe(target));
}

// ── Init ──
renderProtocols();
initEndpoints();
initRevealAnimations();
