/* ═══════════════════════════════════
   SAATVIKA — Frontend Application JS
   ═══════════════════════════════════ */

const API_BASE = window.location.origin;
let SESSION_ID = "session_" + Date.now();
let currentCase = null;

// ─── Screen Management ───────────────
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function showIntake() { showScreen("intake"); }
function showDashboard() { showScreen("dashboard"); }

// ─── Loading ─────────────────────────
function setLoading(on) {
  document.getElementById("loading").classList.toggle("hidden", !on);
}

// ─── Modal ───────────────────────────
function openModal(id) { document.getElementById(id).classList.remove("hidden"); }
function closeModal(id) { document.getElementById(id).classList.add("hidden"); }

// ─── Intake Form Submit ──────────────
document.getElementById("intake-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("btn-submit-intake");
  btn.disabled = true;
  btn.textContent = "Analysing your situation…";
  setLoading(true);

  const spouseAlive = document.querySelector('input[name="spouse_alive"]:checked')?.value === "true";

  const payload = {
    session_id: SESSION_ID,
    deceased_name:       document.getElementById("deceased_name").value,
    date_of_death:       document.getElementById("date_of_death").value,
    state:               document.getElementById("state").value,
    city:                document.getElementById("city").value,
    employment_type:     document.getElementById("employment_type").value,
    religion:            document.getElementById("religion").value,
    has_property:        document.getElementById("has_property").checked,
    has_bank_accounts:   document.getElementById("has_bank_accounts").checked,
    bank_account_count:  parseInt(document.getElementById("bank_account_count").value) || 0,
    has_nominee_bank:    document.getElementById("has_nominee_bank").checked,
    has_insurance:       document.getElementById("has_insurance").checked,
    insurance_age_months:parseInt(document.getElementById("insurance_age_months").value) || 99,
    has_epf:             document.getElementById("has_epf").checked,
    has_pension:         document.getElementById("has_pension").checked,
    has_home_loan:       document.getElementById("has_home_loan").checked,
    has_home_loan_insurance: document.getElementById("has_home_loan_insurance")?.checked || false,
    will_exists:         document.getElementById("will_exists").checked,
    spouse_alive:        spouseAlive,
    children_count:      parseInt(document.getElementById("children_count").value) || 0,
    minor_children_count:parseInt(document.getElementById("minor_children_count").value) || 0,
  };

  try {
    const res = await fetch(`${API_BASE}/api/intake`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "bypass-tunnel-reminder": "true" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.case_profile) {
      currentCase = data.case_profile;
      updateSidebar(currentCase);
    }

    showDashboard();
    addAgentMessage(data.message, data.agent || "Orchestrator");

    // Show case tasks count
    if (data.case_profile) {
      setTimeout(() => loadTasksIntoModal(data.case_profile.tasks), 500);
    }

  } catch (err) {
    console.error(err);
    alert("Could not connect to SAATVIKA backend. Make sure the server is running on port 8000.");
  } finally {
    setLoading(false);
    btn.disabled = false;
    btn.textContent = "Generate My Task Plan →";
  }
});

// ─── Sidebar Update ──────────────────
function updateSidebar(caseProfile) {
  if (!caseProfile) return;
  document.getElementById("case-id").textContent = caseProfile.case_id || "—";

  const badge = document.getElementById("complexity-badge");
  const level = caseProfile.complexity_score || "MEDIUM";
  badge.textContent = level + " Complexity";
  badge.className = "complexity-badge " + level;

  document.getElementById("total-tasks").textContent = caseProfile.total_tasks || "—";
  document.getElementById("urgent-tasks").textContent = caseProfile.urgent_tasks || "—";
  document.getElementById("est-days").textContent =
    caseProfile.estimated_completion_days ? caseProfile.estimated_completion_days + " days" : "—";
}

// ─── Chat Sending ────────────────────
async function sendMessage() {
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg) return;

  input.value = "";
  addUserMessage(msg);
  setLoading(true);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "bypass-tunnel-reminder": "true" },
      body: JSON.stringify({ session_id: SESSION_ID, message: msg }),
    });
    const data = await res.json();
    renderAgentResponse(data);

    if (data.case_profile) {
      currentCase = data.case_profile;
      updateSidebar(currentCase);
    }
  } catch (err) {
    addAgentMessage("I'm sorry — I couldn't connect to the server. Please make sure the backend is running.", "Orchestrator");
  } finally {
    setLoading(false);
  }
}

async function sendQuick(msg) {
  document.getElementById("chat-input").value = msg;
  await sendMessage();
}

// Enter key sends message (Shift+Enter for newline)
document.getElementById("chat-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ─── Message Rendering ───────────────
function addUserMessage(text) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
  container.appendChild(div);
  scrollToBottom();
}

function addAgentMessage(text, agentName = "Orchestrator", citation = null, warnings = [], checklist = []) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "msg agent";

  const tagClass = getAgentTagClass(agentName);
  const formattedText = formatMarkdown(text || "");

  let citationHtml = "";
  if (citation && citation.source_document && citation.source_document !== "general") {
    citationHtml = `
      <div class="citation-box">
        <strong>⚡ Foundry IQ Source:</strong> ${escapeHtml(citation.source_document)}.md
        <br><small>${escapeHtml(citation.disclaimer || "")}</small>
      </div>`;
  }

  let warningsHtml = "";
  if (warnings && warnings.length > 0) {
    warningsHtml = warnings.map(w =>
      `<div class="warning-box">${formatMarkdown(w)}</div>`
    ).join("");
  }

  let checklistHtml = "";
  if (checklist && checklist.length > 0) {
    checklistHtml = `<div class="checklist">` +
      checklist.slice(0, 6).map(item =>
        `<div class="checklist-item">${escapeHtml(item)}</div>`
      ).join("") +
      `</div>`;
  }

  div.innerHTML = `
    <div class="msg-meta">
      <span class="msg-agent-tag ${tagClass}">${escapeHtml(agentName)}</span>
      <span>${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
    </div>
    <div class="msg-bubble">
      ${formattedText}
      ${warningsHtml}
      ${checklistHtml}
      ${citationHtml}
    </div>`;

  container.appendChild(div);
  scrollToBottom();

  // Update agent indicator
  document.getElementById("agent-indicator").textContent = agentName;
}

function renderAgentResponse(data) {
  const agentName = data.agent || "Orchestrator";
  const message = data.message || data.answer || "I'm processing your request.";
  const citation = data.citation || null;
  const warnings = data.warnings || [];
  const checklist = data.actionable_checklist || [];

  addAgentMessage(message, agentName, citation, warnings, checklist);

  // If there are follow-up suggestions, show as chips
  if (data.follow_up_suggestions && data.follow_up_suggestions.length > 0) {
    const chipsEl = document.getElementById("quick-chips");
    // Don't replace existing chips, just ensure they're visible
    chipsEl.style.display = "flex";
  }
}

function getAgentTagClass(agentName) {
  if (!agentName) return "tag-orchestrator";
  const lower = agentName.toLowerCase();
  if (lower.includes("legal")) return "tag-legal";
  if (lower.includes("financial")) return "tag-financial";
  if (lower.includes("engagement")) return "tag-engagement";
  return "tag-orchestrator";
}

// ─── Task List ───────────────────────
async function showTasks() {
  openModal("task-modal");
  if (currentCase && currentCase.tasks) {
    loadTasksIntoModal(currentCase.tasks);
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/tasks/${SESSION_ID}`, {
      headers: { "bypass-tunnel-reminder": "true" }
    });
    const data = await res.json();
    if (data.tasks) loadTasksIntoModal(data.tasks);
  } catch {
    document.getElementById("task-list-content").innerHTML =
      "<p style='color:var(--text-muted);padding:1rem'>No tasks found. Complete intake form first.</p>";
  }
}

function loadTasksIntoModal(tasks) {
  const container = document.getElementById("task-list-content");
  if (!tasks || tasks.length === 0) {
    container.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No tasks generated yet.</p>";
    return;
  }

  container.innerHTML = tasks.map(task => `
    <div class="task-card">
      <div>
        <span class="task-urgency urgency-${task.urgency || 'MEDIUM'}">${task.urgency || 'MEDIUM'}</span>
      </div>
      <div class="task-body">
        <div class="task-name">${escapeHtml(task.name || '')}</div>
        <div class="task-note">${escapeHtml(task.note || '')}</div>
        <div class="task-agent">→ ${escapeHtml(task.agent || '')} | ${escapeHtml(task.iq_source || '')}</div>
      </div>
    </div>
  `).join("");
}

// ─── Support Resources ───────────────
async function requestSupport() {
  addUserMessage("Show me grief support resources");
  setLoading(true);
  try {
    const res = await fetch(`${API_BASE}/api/support/${SESSION_ID}`, { 
      method: "POST",
      headers: { "bypass-tunnel-reminder": "true" }
    });
    const data = await res.json();

    const msg = data.message + "\n\n" +
      "**Mental Health Helplines:**\n" +
      (data.mental_health_helplines || []).map(h =>
        `• ${h.name}: **${h.number}** (${h.hours})`
      ).join("\n") +
      "\n\n**Legal Aid:** " + (data.legal_aid || "") +
      "\n\n**Self-care reminder:** " + (data.self_care_reminder || "");

    addAgentMessage(msg, "Engagement & Grief Support Agent");
  } catch {
    addAgentMessage("Please call iCall (TISS) at **9152987821** for mental health support.", "Engagement & Grief Support Agent");
  } finally {
    setLoading(false);
  }
}

// ─── Utilities ───────────────────────
function scrollToBottom() {
  const msgs = document.getElementById("chat-messages");
  setTimeout(() => msgs.scrollTop = msgs.scrollHeight, 50);
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatMarkdown(text) {
  if (!text) return "";
  return String(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, "<code>$1</code>")
    .replace(/→\s+(.*)/g, "<strong>→ $1</strong>")
    .replace(/\n/g, "<br>");
}

// ─── Init ─────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  showScreen("landing");
  console.log(
    "%c🪔 SAATVIKA — AI Agent for Grief & Estate Navigation\n" +
    "%cMicrosoft Agents League Hackathon 2026\n" +
    "IQ Layers: Foundry IQ + Fabric IQ + Work IQ",
    "color: #E8862A; font-size: 16px; font-weight: bold;",
    "color: #6B7280; font-size: 12px;"
  );
});
