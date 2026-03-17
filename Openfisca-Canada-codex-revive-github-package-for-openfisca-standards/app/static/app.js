/* ================================================================
   OpenFisca Canada MVOHWR Overtime Estimator — app.js
   Features: quick estimate, daily breakdown, multi-week history,
             print/PDF, bilingual EN/FR, rights panel
   ================================================================ */

// ---------------------------------------------------------------------------
// Translations
// ---------------------------------------------------------------------------
const TRANSLATIONS = {
  en: {
    title: "Canada MVOHWR Overtime Estimator",
    subtitle: "Citizen-facing preview tool for Motor Vehicle Operator weekly hours.",
    start_guide_link: "Start guide",
    tab_quick: "Quick Estimate",
    tab_daily: "Daily Breakdown",
    tab_history: "My History",
    tab_rights: "Know Your Rights",
    label_bus: "Bus operator hours",
    label_city: "City operator hours",
    label_highway: "Highway operator hours",
    label_other: "Other hours",
    label_rate: "Hourly wage ($)",
    btn_estimate: "Estimate pay",
    btn_calculate_daily: "Calculate daily + weekly OT",
    btn_save_week: "Save this week",
    btn_print: "Print / Save PDF",
    btn_clear_history: "Clear all history",
    daily_intro: "Enter your hours for each day of the week. The tool calculates <strong>both</strong> daily and weekly overtime, then uses whichever is higher (better for you).",
    grid_day: "Day", grid_bus: "Bus", grid_city: "City", grid_highway: "Hwy", grid_other: "Other", grid_holiday: "Hol?",
    day_Mon: "Mon", day_Tue: "Tue", day_Wed: "Wed", day_Thu: "Thu", day_Fri: "Fri", day_Sat: "Sat", day_Sun: "Sun",
    history_intro: "Your saved weekly estimates (stored in this browser only).",
    history_empty: "No saved weeks yet. Use the calculator and click \"Save this week\".",
    history_week_of: "Week of",
    history_confirm_clear: "Delete all saved history? This cannot be undone.",
    rights_title: "What to do if you think you are owed overtime",
    rights_step1: "Use this tool to estimate the overtime hours and pay you believe you are owed.",
    rights_step2: "Gather your pay stubs, work schedules, and any written agreements with your employer.",
    rights_step3: "Talk to your employer first. Show them your records and ask for the difference.",
    rights_step4: 'If your employer does not resolve it, file a complaint with the <strong>Federal Labour Program</strong>.',
    rights_links_title: "Useful links",
    rights_link_guide: "MVOHWR Guide (Canada.ca)",
    rights_link_complaint: "File a Labour Standards Complaint",
    rights_link_law: "Read the MVOHWR Regulation (full text)",
    rights_link_standards: "Federal Labour Standards Overview",
    rights_limits_title: "Important limits of this tool",
    rights_limits_body: 'This is an <strong>informational estimate only</strong>, not legal advice. Final entitlement depends on your complete employment details, contracts, collective agreements, and official interpretation by the Labour Program. When in doubt, contact the Labour Program directly at <strong>1-800-641-4049</strong>.',
    chat_title: "Ask the assistant (Ollama)",
    chat_model_title: "Model selection",
    chat_examples_title: "Example questions:",
    chat_ex1: "I drove 52 city hours this week. How many hours are overtime?",
    chat_ex2: "If my hourly wage is $29 and I worked 64 highway hours, what should I expect in overtime pay?",
    chat_ex3: "I split time between city and highway routes. Which standard hours should I compare against?",
    chat_ex4: "What evidence should I collect before filing a complaint?",
    chat_label: "Your question",
    chat_send: "Send to assistant",
    chat_clear: "New conversation",
    chat_search_legislation: "Search current legislation (fetches MVOHWR text from Canada.ca)",
    chat_you: "You",
    chat_assistant: "Assistant",
    result_classification: "Classification",
    result_majority: "Majority category",
    result_total_hours: "Total hours",
    result_standard: "Standard hours threshold",
    result_ot_hours: "Overtime hours",
    result_regular_pay: "Regular pay",
    result_ot_pay: "Overtime pay (1.5x)",
    result_total_pay: "Total estimated pay",
    result_explanation: "How it works",
    result_daily_ot: "Daily overtime total",
    result_weekly_ot: "Weekly overtime",
    result_best_ot: "Best overtime (for you)",
    result_method: "Method used",
    result_method_daily: "daily (higher)",
    result_method_weekly: "weekly (higher)",
    lang_toggle: "Fran\u00e7ais",
  },
  fr: {
    title: "Estimateur d\u2019heures suppl\u00e9mentaires RMVHV Canada",
    subtitle: "Outil citoyen pour les heures de travail des conducteurs de v\u00e9hicules automobiles.",
    start_guide_link: "Guide de d\u00e9marrage",
    tab_quick: "Estimation rapide",
    tab_daily: "D\u00e9tail quotidien",
    tab_history: "Mon historique",
    tab_rights: "Vos droits",
    label_bus: "Heures \u2013 conducteur d\u2019autobus",
    label_city: "Heures \u2013 conducteur urbain",
    label_highway: "Heures \u2013 conducteur routier",
    label_other: "Heures \u2013 autre",
    label_rate: "Salaire horaire ($)",
    btn_estimate: "Estimer la paie",
    btn_calculate_daily: "Calculer les HS quotidiennes + hebdomadaires",
    btn_save_week: "Sauvegarder cette semaine",
    btn_print: "Imprimer / Enregistrer PDF",
    btn_clear_history: "Effacer tout l\u2019historique",
    daily_intro: "Saisissez vos heures pour chaque jour. L\u2019outil calcule les heures suppl\u00e9mentaires <strong>quotidiennes et hebdomadaires</strong>, puis utilise le r\u00e9sultat le plus \u00e9lev\u00e9 (le plus avantageux pour vous).",
    grid_day: "Jour", grid_bus: "Bus", grid_city: "Urbain", grid_highway: "Route", grid_other: "Autre", grid_holiday: "F\u00eat\u00e9?",
    day_Mon: "Lun", day_Tue: "Mar", day_Wed: "Mer", day_Thu: "Jeu", day_Fri: "Ven", day_Sat: "Sam", day_Sun: "Dim",
    history_intro: "Vos estimations hebdomadaires sauvegard\u00e9es (dans ce navigateur uniquement).",
    history_empty: "Aucune semaine sauvegard\u00e9e. Utilisez le calculateur et cliquez \u00ab\u00a0Sauvegarder cette semaine\u00a0\u00bb.",
    history_week_of: "Semaine du",
    history_confirm_clear: "Supprimer tout l\u2019historique\u00a0? Cette action est irr\u00e9versible.",
    rights_title: "Que faire si vous pensez avoir droit \u00e0 des heures suppl\u00e9mentaires",
    rights_step1: "Utilisez cet outil pour estimer les heures suppl\u00e9mentaires et la paie que vous croyez vous \u00eatre dues.",
    rights_step2: "Rassemblez vos talons de paie, horaires de travail et tout accord \u00e9crit avec votre employeur.",
    rights_step3: "Parlez d\u2019abord \u00e0 votre employeur. Montrez-lui vos documents et demandez la diff\u00e9rence.",
    rights_step4: "Si votre employeur ne r\u00e8gle pas la situation, d\u00e9posez une plainte aupr\u00e8s du <strong>Programme du travail f\u00e9d\u00e9ral</strong>.",
    rights_links_title: "Liens utiles",
    rights_link_guide: "Guide RMVHV (Canada.ca)",
    rights_link_complaint: "D\u00e9poser une plainte \u2013 normes du travail",
    rights_link_law: "Lire le R\u00e8glement RMVHV (texte complet)",
    rights_link_standards: "Normes du travail f\u00e9d\u00e9rales \u2013 aper\u00e7u",
    rights_limits_title: "Limites importantes de cet outil",
    rights_limits_body: "Ceci est une <strong>estimation informative seulement</strong>, pas un avis juridique. Le droit final d\u00e9pend de vos conditions d\u2019emploi compl\u00e8tes, contrats, conventions collectives et de l\u2019interpr\u00e9tation officielle du Programme du travail. En cas de doute, communiquez directement avec le Programme du travail au <strong>1-800-641-4049</strong>.",
    chat_title: "Poser une question \u00e0 l\u2019assistant (Ollama)",
    chat_model_title: "S\u00e9lection du mod\u00e8le",
    chat_examples_title: "Questions types\u00a0:",
    chat_ex1: "J\u2019ai conduit 52\u00a0heures en ville cette semaine. Combien d\u2019heures sont suppl\u00e9mentaires\u00a0?",
    chat_ex2: "Si mon salaire horaire est 29\u00a0$ et que j\u2019ai conduit 64\u00a0heures sur autoroute, quelle paie suppl\u00e9mentaire devrais-je recevoir\u00a0?",
    chat_ex3: "Je partage mon temps entre la ville et l\u2019autoroute. Quel seuil d\u2019heures s\u2019applique\u00a0?",
    chat_ex4: "Quelles preuves dois-je rassembler avant de d\u00e9poser une plainte\u00a0?",
    chat_label: "Votre question",
    chat_send: "Envoyer \u00e0 l\u2019assistant",
    chat_clear: "Nouvelle conversation",
    chat_search_legislation: "Rechercher la l\u00e9gislation actuelle (r\u00e9cup\u00e8re le texte du RMVHV depuis Canada.ca)",
    chat_you: "Vous",
    chat_assistant: "Assistant",
    result_classification: "Classification",
    result_majority: "Cat\u00e9gorie majoritaire",
    result_total_hours: "Heures totales",
    result_standard: "Seuil d\u2019heures normales",
    result_ot_hours: "Heures suppl\u00e9mentaires",
    result_regular_pay: "Paie r\u00e9guli\u00e8re",
    result_ot_pay: "Paie HS (1,5x)",
    result_total_pay: "Paie totale estim\u00e9e",
    result_explanation: "Comment \u00e7a fonctionne",
    result_daily_ot: "Total HS quotidiennes",
    result_weekly_ot: "HS hebdomadaires",
    result_best_ot: "Meilleures HS (pour vous)",
    result_method: "M\u00e9thode utilis\u00e9e",
    result_method_daily: "quotidiennes (plus \u00e9lev\u00e9es)",
    result_method_weekly: "hebdomadaires (plus \u00e9lev\u00e9es)",
    lang_toggle: "English",
  }
};

let currentLang = localStorage.getItem("mvohwr_lang") || "en";

function t(key) { return TRANSLATIONS[currentLang][key] || TRANSLATIONS.en[key] || key; }

function applyLanguage() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    const val = t(key);
    if (val) {
      // Preserve child inputs by only updating text node or innerHTML for labels
      if (el.querySelector("input, textarea, select")) {
        el.childNodes.forEach(node => {
          if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
            node.textContent = val + " ";
          }
        });
      } else {
        el.innerHTML = val;
      }
    }
  });
  document.getElementById("lang-toggle").textContent = t("lang_toggle");
  document.documentElement.lang = currentLang;
  // Re-render daily grid day labels
  document.querySelectorAll(".day-label").forEach(el => {
    const dayKey = el.getAttribute("data-day-key");
    if (dayKey) el.textContent = t(dayKey);
  });
  renderHistory();
}

document.getElementById("lang-toggle").addEventListener("click", () => {
  currentLang = currentLang === "en" ? "fr" : "en";
  localStorage.setItem("mvohwr_lang", currentLang);
  applyLanguage();
});

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

// ---------------------------------------------------------------------------
// Quick Estimate
// ---------------------------------------------------------------------------
const form = document.getElementById("calc-form");
const result = document.getElementById("result");
const quickActions = document.getElementById("quick-actions");
let latestEstimate = null;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());

  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    result.innerHTML = `<strong>Error:</strong> ${data.error}`;
    result.classList.remove("hidden");
    quickActions.classList.add("hidden");
    return;
  }

  latestEstimate = data;
  result.innerHTML = `
    <h2>${t("result_classification")}: ${data.classification}</h2>
    ${data.majority_category ? `<p><strong>${t("result_majority")}:</strong> ${data.majority_category}</p>` : ""}
    <p><strong>${t("result_total_hours")}:</strong> ${data.total_hours}</p>
    <p><strong>${t("result_standard")}:</strong> ${data.standard_hours}h</p>
    <p><strong>${t("result_ot_hours")}:</strong> ${data.overtime_hours}</p>
    ${data.explanation ? `<p class="small-note"><em>${t("result_explanation")}:</em> ${data.explanation}</p>` : ""}
    <hr/>
    <p><strong>${t("result_regular_pay")}:</strong> $${data.regular_pay.toFixed(2)}</p>
    <p><strong>${t("result_ot_pay")}:</strong> $${data.overtime_pay.toFixed(2)}</p>
    <p class="result-highlight">${t("result_total_pay")}: $${data.total_pay.toFixed(2)}</p>
  `;
  result.classList.remove("hidden");
  quickActions.classList.remove("hidden");
});

document.getElementById("btn-save-quick").addEventListener("click", () => {
  if (latestEstimate) saveToHistory(latestEstimate);
});

document.getElementById("btn-print").addEventListener("click", () => window.print());

// ---------------------------------------------------------------------------
// Daily Breakdown
// ---------------------------------------------------------------------------
const DAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const dailyGrid = document.querySelector(".daily-grid");

// Build daily input rows
DAY_KEYS.forEach(day => {
  const row = document.createElement("div");
  row.className = "daily-grid-row";
  row.innerHTML = `
    <div class="daily-grid-cell"><span class="day-label" data-day-key="day_${day}">${t("day_" + day)}</span></div>
    <div class="daily-grid-cell"><input type="number" step="0.1" min="0" value="0" data-day="${day}" data-type="bus" /></div>
    <div class="daily-grid-cell"><input type="number" step="0.1" min="0" value="0" data-day="${day}" data-type="city" /></div>
    <div class="daily-grid-cell"><input type="number" step="0.1" min="0" value="0" data-day="${day}" data-type="highway" /></div>
    <div class="daily-grid-cell"><input type="number" step="0.1" min="0" value="0" data-day="${day}" data-type="other" /></div>
    <div class="daily-grid-cell"><input type="checkbox" data-day="${day}" data-type="holiday" /></div>
  `;
  dailyGrid.appendChild(row);
});

const dailyForm = document.getElementById("daily-form");
const dailyResult = document.getElementById("daily-result");
const dailyActions = document.getElementById("daily-actions");
let latestDailyEstimate = null;

dailyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const days = DAY_KEYS.map(day => ({
    day,
    hours_bus: parseFloat(dailyGrid.querySelector(`[data-day="${day}"][data-type="bus"]`).value) || 0,
    hours_city: parseFloat(dailyGrid.querySelector(`[data-day="${day}"][data-type="city"]`).value) || 0,
    hours_highway: parseFloat(dailyGrid.querySelector(`[data-day="${day}"][data-type="highway"]`).value) || 0,
    hours_other: parseFloat(dailyGrid.querySelector(`[data-day="${day}"][data-type="other"]`).value) || 0,
    is_holiday: dailyGrid.querySelector(`[data-day="${day}"][data-type="holiday"]`).checked,
  }));

  const hourlyRate = parseFloat(dailyForm.elements.daily_hourly_rate.value) || 0;

  const response = await fetch("/api/daily-breakdown", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ days, hourly_rate: hourlyRate }),
  });

  const data = await response.json();
  if (!response.ok) {
    dailyResult.innerHTML = `<strong>Error:</strong> ${data.error}`;
    dailyResult.classList.remove("hidden");
    dailyActions.classList.add("hidden");
    return;
  }

  latestDailyEstimate = data;

  // Build day-by-day results table
  let tableRows = data.days.map(d => {
    const hasOt = d.daily_overtime > 0;
    return `<tr class="${hasOt ? 'ot-row' : ''}">
      <td>${t("day_" + d.day)}</td>
      <td>${d.hours_bus}</td><td>${d.hours_city}</td><td>${d.hours_highway}</td><td>${d.hours_other}</td>
      <td><strong>${d.day_total}</strong></td>
      <td>${d.daily_overtime}</td>
      <td>${d.is_holiday ? "\u2705" : ""}</td>
    </tr>`;
  }).join("");

  const methodLabel = data.overtime_method === "daily" ? t("result_method_daily") : t("result_method_weekly");

  dailyResult.innerHTML = `
    <h2>${t("result_classification")}: ${data.classification}</h2>
    ${data.majority_category ? `<p><strong>${t("result_majority")}:</strong> ${data.majority_category}</p>` : ""}

    <table class="day-results-table">
      <thead><tr>
        <th>${t("grid_day")}</th><th>${t("grid_bus")}</th><th>${t("grid_city")}</th>
        <th>${t("grid_highway")}</th><th>${t("grid_other")}</th>
        <th>Total</th><th>OT</th><th>${t("grid_holiday")}</th>
      </tr></thead>
      <tbody>${tableRows}</tbody>
      <tfoot><tr>
        <td colspan="5">${t("result_total_hours")}</td>
        <td>${data.weekly_total_hours}</td>
        <td>${data.daily_overtime_total}</td>
        <td>${data.holiday_count > 0 ? data.holiday_count : ""}</td>
      </tr></tfoot>
    </table>

    <p><strong>${t("result_standard")}:</strong> ${data.weekly_threshold}h</p>
    <p><strong>${t("result_daily_ot")}:</strong> ${data.daily_overtime_total}h</p>
    <p><strong>${t("result_weekly_ot")}:</strong> ${data.weekly_overtime}h</p>
    <p><strong>${t("result_best_ot")}:</strong> ${data.best_overtime_hours}h (${t("result_method")}: ${methodLabel})</p>
    <hr/>
    <p><strong>${t("result_regular_pay")}:</strong> $${data.regular_pay.toFixed(2)}</p>
    <p><strong>${t("result_ot_pay")}:</strong> $${data.overtime_pay.toFixed(2)}</p>
    <p class="result-highlight">${t("result_total_pay")}: $${data.total_pay.toFixed(2)}</p>
  `;
  dailyResult.classList.remove("hidden");
  dailyActions.classList.remove("hidden");
});

document.getElementById("btn-save-daily").addEventListener("click", () => {
  if (latestDailyEstimate) saveToHistory(latestDailyEstimate);
});

document.getElementById("btn-print-daily").addEventListener("click", () => window.print());

// ---------------------------------------------------------------------------
// History (localStorage)
// ---------------------------------------------------------------------------
const HISTORY_KEY = "mvohwr_history";

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
  catch { return []; }
}

function saveHistory(items) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items));
}

function saveToHistory(estimate) {
  const items = loadHistory();
  const entry = {
    id: Date.now(),
    date: new Date().toISOString().slice(0, 10),
    estimate,
  };
  items.unshift(entry);
  // Keep last 52 weeks max
  if (items.length > 52) items.length = 52;
  saveHistory(items);
  renderHistory();
  // Switch to history tab
  document.querySelector('[data-tab="history"]').click();
}

function renderHistory() {
  const list = document.getElementById("history-list");
  const items = loadHistory();

  if (items.length === 0) {
    list.innerHTML = `<li class="history-empty">${t("history_empty")}</li>`;
    return;
  }

  list.innerHTML = items.map(item => {
    const e = item.estimate;
    return `<li class="history-item">
      <div>
        <strong>${t("history_week_of")} ${item.date}</strong><br/>
        ${e.weekly_total_hours || e.total_hours || 0}h total &middot;
        ${e.best_overtime_hours || e.overtime_hours || 0}h OT &middot;
        $${(e.total_pay || 0).toFixed(2)}
        ${e.mode === "daily-breakdown" ? " (daily)" : " (quick)"}
      </div>
      <button class="btn-danger btn-sm" onclick="deleteHistoryItem(${item.id})">&times;</button>
    </li>`;
  }).join("");
}

window.deleteHistoryItem = function(id) {
  const items = loadHistory().filter(i => i.id !== id);
  saveHistory(items);
  renderHistory();
};

document.getElementById("btn-clear-history").addEventListener("click", () => {
  if (confirm(t("history_confirm_clear"))) {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
  }
});

// ---------------------------------------------------------------------------
// Chat (Ollama) — multi-turn conversation
// ---------------------------------------------------------------------------
const chatForm = document.getElementById("chat-form");
const chatResult = document.getElementById("chat-result");
const exampleQuestions = document.querySelectorAll(".example-question");
const modelButtons = document.querySelectorAll(".model-button");
const modelSelected = document.getElementById("model-selected");

let selectedModel = "llama3.1";
// Conversation history: array of {role: "user"|"assistant", content: string}
let chatHistory = [];

function activateModel(model) {
  selectedModel = model;
  modelButtons.forEach(button => {
    button.classList.toggle("active", button.dataset.model === model);
  });
  modelSelected.textContent = `Selected model: ${model}`;
}

modelButtons.forEach(button => {
  button.addEventListener("click", () => activateModel(button.dataset.model));
});

exampleQuestions.forEach(button => {
  button.addEventListener("click", () => {
    chatForm.elements.message.value = button.textContent;
    chatForm.elements.message.focus();
  });
});

function renderChatHistory() {
  if (chatHistory.length === 0) {
    chatResult.classList.add("hidden");
    return;
  }

  let html = '<div class="chat-thread">';
  for (const turn of chatHistory) {
    if (turn.role === "user") {
      html += `<div class="chat-bubble chat-user"><strong>${t("chat_you")}:</strong> ${escapeHtml(turn.content)}</div>`;
    } else {
      html += `<div class="chat-bubble chat-assistant"><strong>${t("chat_assistant")}:</strong> ${turn.content.replace(/\n/g, "<br/>")}</div>`;
    }
  }
  html += "</div>";
  chatResult.innerHTML = html;
  chatResult.classList.remove("hidden");
  // Scroll to bottom of chat
  chatResult.scrollTop = chatResult.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatForm.elements.message.value.trim();
  if (!message) return;

  // Add user message to history and render immediately
  chatHistory.push({ role: "user", content: message });
  renderChatHistory();
  chatForm.elements.message.value = "";

  const estimate = latestDailyEstimate || latestEstimate;
  const searchLegislation = document.getElementById("chat-search-legislation").checked;

  // Send full conversation history to the backend
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      estimate,
      model: selectedModel,
      history: chatHistory.slice(0, -1),  // all turns before the current one
      search_legislation: searchLegislation,
    }),
  });
  const data = await response.json();

  if (!response.ok) {
    chatHistory.push({ role: "assistant", content: `Error: ${data.error}` });
    renderChatHistory();
    return;
  }

  // Add assistant reply to history
  chatHistory.push({ role: "assistant", content: data.reply });
  renderChatHistory();
});

// Clear chat button
document.getElementById("btn-clear-chat").addEventListener("click", () => {
  chatHistory = [];
  renderChatHistory();
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
applyLanguage();
renderHistory();
