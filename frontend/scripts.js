926/* ═══════════════════════════════════════════════════════════════
   ExamMemory AI — scripts.js
   Fixes applied:
   1.  API_BASE env-var injection (works on Netlify)
   2.  Full offline/demo mode — site works with no backend
   3.  Modal: Escape key, focus trap, aria-hidden toggle
   4.  Quiz: loading spinner, separate DOM from revision quiz
   5.  userId validation guards
   6.  Search: clear button, open article from result
   7.  Streak calendar, category accuracy bars rendered from data
   8.  Dark mode toggle (persisted in localStorage)
   9.  Offline banner with dismiss
   10. Quiz mode banner
   11. buildDailyQuiz — parallel fetch, graceful fallback
   12. Date auto-update in dashboard
   ═══════════════════════════════════════════════════════════════ */

"use strict";

/* ── CONFIG ───────────────────────────────────────────────────── */
const API_BASE = (() => {
  // 1. Injected config (optional): window.EXAMMEMORY_API = "https://your-api.fly.dev"
  if (window.EXAMMEMORY_API) return window.EXAMMEMORY_API.replace(/\/$/, "");
  // 2. Same-origin when served by FastAPI on :8000
  if (window.location.port === "8000") return window.location.origin;
  // 3. Deployed site (Netlify etc.) — use same-origin so /api proxy in netlify.toml works
  const host = window.location.hostname;
  if (host !== "localhost" && host !== "127.0.0.1") return window.location.origin;
  // 4. Local dev fallback
  return "http://127.0.0.1:8000";
})();

const DEMO_MODE_ARTICLES = [
  {
    id: "d1", title: "RBI cuts repo rate by 25 bps to 6.25% — first cut since 2020",
    source_name: "RBI", category: "Economy", importance_score: 9.2, include: true,
    tags: ["RBI","Monetary Policy","Repo Rate","MPC"],
    why_important: "First rate cut in 5 years — high-priority for Banking, UPSC GS3, SSC CGL.",
    quick: { why_in_news:"MPC reduced repo rate to ease growth.", key_facts:["Repo rate: 6.25%","CRR: 4%","SLR: 18%","GDP forecast 6.8% FY26"], background:"RBI raised rates in 2022-23 to curb inflation.", exam_relevance:"UPSC GS3 / Economy / Banking exam", keywords:["repo rate","MPC","monetary policy","inflation targeting"], revision_notes:"RBI→MPC→6.25%→first cut since May 2020" },
    deep: { why_in_news:"MPC unanimously voted to cut by 25 bps amid easing CPI.", key_facts:["Repo: 6.25%","Reverse repo: 3.35%","CRR: 4%","SLR: 18%"], background:"Post-COVID tightening cycle. CPI now near 4% target.", exam_relevance:"UPSC GS3 Mains — Economic Policy, RBI Act, Monetary Framework", keywords:["transmission lag","accommodative stance","capital flows","rupee"], revision_notes:"Growth vs inflation trade-off; US Fed still hawkish — analyse divergence" },
    mcqs: [{ question:"Which body decides India's repo rate?", options:["Finance Ministry","Monetary Policy Committee","SEBI","NABARD"], answer:"Monetary Policy Committee", explanation:"The MPC, constituted under RBI Act 1934, sets the policy repo rate by majority vote." }]
  },
  {
    id: "d2", title: "India ranks 63rd in Global Innovation Index 2025 — highest ever",
    source_name: "WIPO", category: "Reports & Indexes", importance_score: 8.8, include: true,
    tags: ["GII","WIPO","Innovation","Rankings"],
    why_important: "India's best-ever GII rank — ask in virtually every exam.",
    quick: { why_in_news:"India climbed to 63rd in GII.", key_facts:["Published by: WIPO","India rank: 63rd","Previous: 66th","Top: Switzerland"], background:"GII measures innovation ecosystem across 132 economies.", exam_relevance:"SSC CGL / Banking / UPSC Prelims", keywords:["GII","WIPO","intellectual property","innovation"], revision_notes:"GII 2025 → WIPO → India 63rd (best ever) → Switzerland tops" },
    deep: { why_in_news:"India's consistent rise in GII shows improved IP ecosystem.", key_facts:["63rd out of 132","Published annually by WIPO","India top in Central & South Asia"], background:"India entered top 40 in some sub-indices like ICT services exports.", exam_relevance:"UPSC GS3 — S&T, Economic Development, Innovation Policy", keywords:["startup ecosystem","R&D spending","patent filings","digital infrastructure"], revision_notes:"GII trajectory: 81st in 2015 → 63rd in 2025; policy: NIP 2018, SIPP" },
    mcqs: [{ question:"The Global Innovation Index is published by which organisation?", options:["World Bank","UNDP","WIPO","IMF"], answer:"WIPO", explanation:"GII is published annually by WIPO (World Intellectual Property Organization)." }]
  },
  {
    id: "d3", title: "Supreme Court upholds Right to Privacy under Article 21 in digital data case",
    source_name: "Supreme Court", category: "Polity", importance_score: 8.1, include: true,
    tags: ["Article 21","Privacy","Supreme Court","DPDP Act"],
    why_important: "Constitutional law — critical for UPSC GS2 and State PSC.",
    quick: { why_in_news:"SC extended Right to Privacy to digital personal data.", key_facts:["Article 21: Right to Life","Privacy sub-right of Art 21","Case linked to DPDP Act 2023"], background:"Puttaswamy judgment 2017 established privacy as fundamental right.", exam_relevance:"UPSC GS2 / State PSC / CLAT", keywords:["Article 21","DPDP","fundamental right","data fiduciary"], revision_notes:"Art 21 → Privacy → Puttaswamy 2017 → DPDP Act 2023" },
    deep: { why_in_news:"SC ruling reinforces constitutional backing for Digital Personal Data Protection Act.", key_facts:["9-judge bench in Puttaswamy","DPDP Act: data fiduciary, data principal"], background:"India lacked data protection law until DPDP 2023. SC ruling gives constitutional teeth.", exam_relevance:"UPSC GS2 Mains — Governance, Rights, Judiciary", keywords:["informational privacy","surveillance","reasonable restriction","Article 19(1)(a)"], revision_notes:"Link: Art 21 → Privacy → Aadhaar case → DPDP 2023 → SC digital ruling" },
    mcqs: [{ question:"In which landmark case did the Supreme Court recognise Right to Privacy as a Fundamental Right?", options:["Kesavananda Bharati","Puttaswamy v Union of India","Maneka Gandhi v UOI","S.R. Bommai v UOI"], answer:"Puttaswamy v Union of India", explanation:"A 9-judge constitution bench in 2017 unanimously held that privacy is intrinsic to Article 21." }]
  },
  {
    id: "d4", title: "India-UAE CEPA extended — bilateral trade target revised to $100B by 2030",
    source_name: "MEA", category: "International Relations", importance_score: 8.4, include: true,
    tags: ["CEPA","UAE","Trade","MEA"],
    why_important: "India's trade deals are high-yield for every exam.",
    quick: { why_in_news:"India and UAE extended and strengthened the CEPA.", key_facts:["CEPA signed: Feb 2022","Trade target: $100B by 2030","UAE: 3rd largest trade partner"], background:"CEPA = Comprehensive Economic Partnership Agreement.", exam_relevance:"UPSC GS2 / SSC CGL / Banking", keywords:["CEPA","FTA","bilateral trade","rupee-dirham"], revision_notes:"UAE CEPA 2022 → extended 2025 → $100B target 2030 → 3rd largest partner" },
    deep: { why_in_news:"India deepens strategic economic partnership with UAE under I2U2 framework.", key_facts:["I2U2: India, Israel, UAE, USA","CEPA covers goods, services, IP"], background:"UAE is gateway to Gulf and Africa markets; large Indian diaspora (3.5M).", exam_relevance:"UPSC GS2 Mains — IR, India's foreign policy, economic diplomacy", keywords:["I2U2","Gulf diplomacy","diaspora","rupee internationalisation"], revision_notes:"CEPA → I2U2 → Gulf pivot → energy, food security, fintech" },
    mcqs: [{ question:"CEPA stands for:", options:["Common Economic Partnership Act","Comprehensive Economic Partnership Agreement","Central Export Promotion Agency","Cooperative Export and Partnership Agreement"], answer:"Comprehensive Economic Partnership Agreement", explanation:"CEPA is a broad trade pact covering goods, services, investment, and IP." }]
  },
  {
    id: "d5", title: "PM Surya Ghar Muft Bijli Yojana: 1 crore homes targeted for rooftop solar",
    source_name: "PIB", category: "Government Schemes", importance_score: 8.6, include: true,
    tags: ["Solar","PM Surya Ghar","MNRE","Renewable Energy"],
    why_important: "Government schemes with ministry + target = guaranteed exam question.",
    quick: { why_in_news:"PM Surya Ghar Muft Bijli Yojana launched to expand rooftop solar.", key_facts:["Target: 1 crore households","Free 300 units/month for eligible","Ministry: MNRE","Budget: ₹75,000 crore"], background:"India's renewable energy push — 500 GW by 2030.", exam_relevance:"SSC CGL / Banking / UPSC Prelims", keywords:["rooftop solar","MNRE","green energy","subsidies"], revision_notes:"Scheme → MNRE → 1 crore homes → 300 free units/month" },
    deep: { why_in_news:"Part of India's solar mission to reduce household electricity bills and carbon footprint.", key_facts:["Subsidy via DBT","Net metering allows surplus sale to grid","State nodal agencies involved"], background:"India solar capacity: 80+ GW installed. Target: 280 GW solar by 2030.", exam_relevance:"UPSC GS3 — Environment, Energy, Government Schemes", keywords:["net metering","DBT","NDC","just transition","solar mission"], revision_notes:"Link to ISA, Paris Agreement, NDC, India's 2070 net-zero commitment" },
    mcqs: [{ question:"PM Surya Ghar Muft Bijli Yojana is administered by which ministry?", options:["Ministry of Power","Ministry of Finance","Ministry of New and Renewable Energy","Ministry of Housing"], answer:"Ministry of New and Renewable Energy", explanation:"MNRE is the nodal ministry for all renewable energy schemes including rooftop solar." }]
  },
  {
    id: "d6", title: "Celebrity spotted at airport — fashion and travel update",
    source_name: "Entertainment Desk", category: "Entertainment", importance_score: 1.0, include: false,
    tags: ["Celebrity"],
    why_important: "Not relevant for any government exam.",
    quick: null, deep: null, mcqs: []
  }
];

const DEMO_DASHBOARD = {
  today_news_count: 12, revision_due_count: 8, retention_score: 82,
  streak_days: 9, weak_areas: ["Economy", "Environment"],
  category_accuracy: [
    { name:"Economy", pct:88 },{ name:"Polity", pct:74 },
    { name:"Environment", pct:61 },{ name:"Int'l Relations", pct:79 },{ name:"Sci & Tech", pct:85 }
  ]
};

const DEMO_REVISION = {
  message:"8 topics from yesterday — start your 2-minute revision.",
  questions: DEMO_MODE_ARTICLES.filter(a=>a.include && a.mcqs.length).map(a=>({
    schedule_id: "s_"+a.id, article_title: a.title, category: a.category,
    mcq: a.mcqs[0]
  }))
};

/* ── STATE ────────────────────────────────────────────────────── */
let selectedExam    = localStorage.getItem("exammemory_exam") || "UPSC";
let userId          = localStorage.getItem("exammemory_user_id");
let authToken       = localStorage.getItem("exammemory_auth_token");
let authUser        = null;
let authTab         = "login";
let articles        = [];
let revisionQuestions = [];
let dailyQuizPool   = [];
let quizMode        = "daily";   // "daily" | "revision"
let quizIndex       = 0;
let correctAnswers  = 0;
let answeredCurrent = false;
let isDemo          = false;
let firstFocusableInModal = null;

/* ── DOM REFS ─────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const menuButton        = $("menu-button");
const nav               = $("nav");
const offlineBanner     = $("offline-banner");
const offlineClose      = $("offline-close");
const quizModeBanner    = $("quiz-mode-banner");
const quizModeLabel     = $("quiz-mode-label");
const switchDailyBtn    = $("switch-daily-quiz");
const themeToggle       = $("theme-toggle");
const themeIcon         = $("theme-icon");
const articleList       = $("article-list");
const searchInput       = $("topic-search");
const searchResults     = $("search-results");
const searchClear       = $("search-clear");
const articleModal      = $("article-modal");
const modalBody         = $("modal-body");
const modalClose        = $("modal-close");
const startRevisionBtn  = $("start-revision");
const revisionMessage   = $("revision-message");
const quizLoading       = $("quiz-loading");
const quizQuestion      = $("quiz-question");
const quizOptions       = $("quiz-options");
const quizResultEl      = $("quiz-result");
const nextQuestionBtn   = $("next-question");
const donutFill         = $("donut-fill");
const authOpen          = $("auth-open");
const authLogout        = $("auth-logout");
const authLabel         = $("auth-label");
const authModal         = $("auth-modal");
const authModalClose    = $("auth-modal-close");
const authForm          = $("auth-form");
const authError         = $("auth-error");
const authNameWrap      = $("auth-name-wrap");
const authSubmitLabel   = $("auth-submit-label");
const authGuestNote     = $("auth-guest-note");

/* ── API HELPER ───────────────────────────────────────────────── */
function parseApiError(err, status) {
  if (status === 405) {
    return "Auth API not available — restart the backend (see README). Use http://127.0.0.1:8000 not index.html.";
  }
  const d = err?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map(x => x.msg || x).join("; ");
  return `Request failed (${status})`;
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  const res = await fetch(`${API_BASE}${path}`, {
    headers,
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(parseApiError(err, res.status));
  }
  return res.json();
}

/* ── DEMO MODE ACTIVATION ─────────────────────────────────────── */
function activateDemo() {
  isDemo = true;
  offlineBanner.hidden = false;
  document.body.classList.add("has-banner");
}

/* ── AUTH UI ──────────────────────────────────────────────────── */
function renderAuthBar() {
  if (isDemo) {
    authLabel.textContent = "Sign in";
    authLogout.hidden = true;
    authGuestNote.textContent = "Connect the backend to enable accounts and cross-device sync.";
    return;
  }
  if (authUser?.email) {
    const short = authUser.email.split("@")[0];
    authLabel.textContent = short.length > 12 ? short.slice(0, 11) + "…" : short;
    authLogout.hidden = false;
    authGuestNote.textContent = "Signed in — progress syncs to your account on every device.";
  } else {
    authLabel.textContent = "Sign in";
    authLogout.hidden = true;
    authGuestNote.textContent = "Guest mode works locally. Create an account to sync across phone and laptop.";
  }
}

function setAuthTab(tab) {
  authTab = tab;
  $$("[data-auth-tab]").forEach(btn => {
    const on = btn.dataset.authTab === tab;
    btn.classList.toggle("active", on);
    btn.setAttribute("aria-selected", String(on));
  });
  authNameWrap.hidden = tab !== "signup";
  authSubmitLabel.textContent = tab === "signup" ? "Create account" : "Log in";
  $("auth-password").autocomplete = tab === "signup" ? "new-password" : "current-password";
  authError.hidden = true;
}

function openAuthModal(tab = "login") {
  const signedIn = !!authUser?.email;
  $("auth-signed-in").hidden = !signedIn;
  $("auth-forms-wrap").hidden = signedIn;
  if (signedIn) {
    $("auth-signed-email").textContent = authUser.email;
  } else {
    setAuthTab(tab);
    $("auth-email").focus();
  }
  authModal.classList.add("open");
  authModal.setAttribute("aria-hidden", "false");
}

function closeAuthModal() {
  authModal.classList.remove("open");
  authModal.setAttribute("aria-hidden", "true");
  authError.hidden = true;
}

function applyAuthSession(data) {
  authToken = data.token;
  authUser = data.user;
  userId = data.user.id;
  localStorage.setItem("exammemory_auth_token", authToken);
  localStorage.setItem("exammemory_user_id", userId);
  if (data.user.target_exam) {
    selectedExam = data.user.target_exam;
    localStorage.setItem("exammemory_exam", selectedExam);
    $$("[data-exam]").forEach(b => b.classList.toggle("active", b.dataset.exam === selectedExam));
  }
  renderAuthBar();
  closeAuthModal();
}

function clearAuthSession() {
  authToken = null;
  authUser = null;
  localStorage.removeItem("exammemory_auth_token");
  renderAuthBar();
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  if (isDemo) {
    authError.textContent = "Start the backend server to use accounts.";
    authError.hidden = false;
    return;
  }
  const email = $("auth-email").value.trim();
  const password = $("auth-password").value;
  const name = $("auth-name").value.trim() || "Student";
  authError.hidden = true;
  $("auth-submit").disabled = true;

  try {
    const path = authTab === "signup" ? "/api/auth/signup" : "/api/auth/login";
    const body = authTab === "signup"
      ? { email, password, name, target_exam: selectedExam, guest_user_id: userId }
      : { email, password };
    const data = await api(path, { method: "POST", body: JSON.stringify(body) });
    applyAuthSession(data);
    await refreshUserData();
  } catch (err) {
    authError.textContent = err.message || "Could not sign in. Try again.";
    authError.hidden = false;
  } finally {
    $("auth-submit").disabled = false;
  }
}

async function restoreAuthSession() {
  if (!authToken || isDemo) return false;
  try {
    const user = await api("/api/auth/me");
    authUser = user;
    userId = user.id;
    localStorage.setItem("exammemory_user_id", userId);
    if (user.target_exam) {
      selectedExam = user.target_exam;
      localStorage.setItem("exammemory_exam", selectedExam);
      $$("[data-exam]").forEach(b => b.classList.toggle("active", b.dataset.exam === selectedExam));
    }
    renderAuthBar();
    return true;
  } catch {
    clearAuthSession();
    return false;
  }
}

async function refreshUserData() {
  await loadArticles();
  await loadDashboard();
  await loadRevision();
  await buildDailyQuiz();
}

/* ── USER MANAGEMENT ──────────────────────────────────────────── */
async function ensureUser() {
  if (isDemo) { userId = "demo_user"; renderAuthBar(); return; }
  if (await restoreAuthSession()) return;
  if (userId) {
    try {
      await api(`/api/users/${userId}`);
      renderAuthBar();
      return;
    } catch {
      userId = null;
      localStorage.removeItem("exammemory_user_id");
    }
  }
  const user = await api("/api/users", {
    method: "POST",
    body: JSON.stringify({ name: "Student", target_exam: selectedExam }),
  });
  userId = user.id;
  localStorage.setItem("exammemory_user_id", userId);
  renderAuthBar();
}

/* ── DATE ─────────────────────────────────────────────────────── */
function renderDate() {
  const d = new Date();
  $("today-date").textContent = d.toLocaleDateString("en-IN", { day:"numeric", month:"long", year:"numeric" });
}

/* ── STREAK CALENDAR ──────────────────────────────────────────── */
function renderStreak(days) {
  const row = $("streak-row");
  row.innerHTML = "";
  const labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  const today = new Date().getDay(); // 0=Sun
  // Show last 7 days
  for (let i = 6; i >= 0; i--) {
    const dayIdx = (today - i + 7) % 7;
    const done = i >= (7 - days) && days > 0;
    const isToday = i === 0;
    const el = document.createElement("div");
    el.className = "streak-day";
    el.innerHTML = `<div class="streak-pip ${isToday ? "today" : done ? "done" : ""}"></div><span>${labels[dayIdx]}</span>`;
    row.appendChild(el);
  }
}

/* ── CATEGORY ACCURACY BARS ───────────────────────────────────── */
function renderAccBars(cats) {
  const container = $("acc-bars");
  if (!container || !cats.length) return;
  container.innerHTML = cats.map(c => {
    const cls = c.pct >= 75 ? "" : c.pct >= 55 ? "warn" : "low";
    return `<div class="acc-item">
      <div class="acc-label"><span>${c.name}</span><span>${c.pct}%</span></div>
      <div class="acc-track"><div class="acc-fill ${cls}" style="width:${c.pct}%"></div></div>
    </div>`;
  }).join("");
}

/* ── DASHBOARD ────────────────────────────────────────────────── */
async function loadDashboard() {
  let data;
  if (isDemo) {
    data = DEMO_DASHBOARD;
  } else {
    data = await api(`/api/dashboard/${userId}`);
  }
  $("news-count").textContent      = data.today_news_count;
  $("revision-count").textContent  = data.revision_due_count;
  $("retention-score").textContent = `${data.retention_score}%`;
  $("streak-count").textContent    = `${data.streak_days}d`;

  const weakArea = $("weak-area");
  if (data.weak_areas?.length) {
    weakArea.innerHTML = data.weak_areas.map(a =>
      `<div><span class="dot economy"></span><span>${a} needs review</span></div>`
    ).join("");
  }

  renderStreak(data.streak_days || 0);
  if (data.category_accuracy) renderAccBars(data.category_accuracy);
}

/* ── ARTICLE RENDERING ────────────────────────────────────────── */
function modeNote(article) {
  const deep = ["UPSC","State PSC"].includes(selectedExam);
  const block = deep ? article.deep : article.quick;
  return block?.revision_notes || article.why_important || "";
}

function renderArticleSkeleton() {
  return `<div class="article-card" style="pointer-events:none">
    <div>
      <div class="skeleton wide"></div>
      <div class="skeleton short"></div>
      <div class="skeleton" style="width:60%;height:12px;margin-top:6px"></div>
    </div>
  </div>`.repeat(3);
}

function renderArticles() {
  if (!articles.length) {
    articleList.innerHTML = `<p class="loading">No articles available. Start the backend to fetch live feeds.</p>`;
    return;
  }
  const sorted = [...articles].sort((a,b) =>
    Number(b.include) - Number(a.include) || b.importance_score - a.importance_score
  );
  articleList.innerHTML = sorted.map(article => {
    const note = modeNote(article);
    return `
    <article class="article-card ${article.include ? "" : "rejected"}" data-id="${article.id}">
      <div>
        <div class="article-meta">
          <span class="article-score">${article.include ? "Include" : "Rejected"} · ${article.importance_score}/10</span>
          <span class="article-source">${article.source_name} · ${article.category}${article.language === "hi" ? " · हिंदी" : ""}</span>
        </div>
        <h3><button type="button" class="link-title" data-open="${article.id}">${article.title}</button></h3>
        <p class="article-why">${article.why_important}</p>
        <p style="font-size:13px;color:var(--muted);margin:6px 0"><strong style="color:var(--ink)">${selectedExam}:</strong> ${note}</p>
        <div class="article-tags">
          ${(article.tags||[]).map(t=>`<span class="tag">${t}</span>`).join("")}
        </div>
      </div>
      <button class="read-button" ${article.include?"":"disabled"} data-read="${article.id}">Mark read</button>
    </article>`;
  }).join("");

  // Repopulate search results with new articles
  renderSearchResults(searchInput.value);
}

async function loadArticles() {
  articleList.innerHTML = renderArticleSkeleton();
  if (isDemo) {
    articles = DEMO_MODE_ARTICLES;
    renderArticles();
    return;
  }
  const params = new URLSearchParams({ exam: selectedExam, include_rejected:"true" });
  articles = await api(`/api/articles?${params}`);
  renderArticles();
}

/* ── ARTICLE MODAL ────────────────────────────────────────────── */
async function openArticle(id) {
  // Find article — first check cache, then fetch if live
  let article = articles.find(a => a.id === id || a.id === String(id));
  if (!isDemo && article) {
    try { article = await api(`/api/articles/${id}`); } catch {}
  }
  if (!article) return;

  const isDeep = ["UPSC","State PSC"].includes(selectedExam);
  const block = (isDeep ? article.deep : article.quick) || article.quick || article.deep || {};
  const mcq = article.mcqs?.[0];

  modalBody.innerHTML = `
    <p id="modal-title">${article.source_name} · ${article.category} · ${article.importance_score}/10</p>
    <h3>${article.title}</h3>
    ${block.why_in_news ? `<p><strong>Why in News:</strong> ${block.why_in_news}</p>` : ""}
    ${block.key_facts?.length ? `<p><strong>Key Facts:</strong></p><ul>${block.key_facts.map(f=>`<li>${f}</li>`).join("")}</ul>` : ""}
    ${block.background ? `<p><strong>Background:</strong> ${block.background}</p>` : ""}
    ${block.exam_relevance ? `<p><strong>Exam Relevance:</strong> ${block.exam_relevance}</p>` : ""}
    ${block.keywords?.length ? `<p><strong>Keywords:</strong> ${block.keywords.join(", ")}</p>` : ""}
    ${block.revision_notes ? `<p><strong>2-Minute Revision:</strong> ${block.revision_notes}</p>` : ""}
    ${mcq ? `<div class="mcq-box"><strong>MCQ</strong><p>${mcq.question}</p><span>Answer: ${mcq.answer}</span>${mcq.explanation?`<p style="margin-top:8px;font-size:12.5px">${mcq.explanation}</p>`:""}</div>` : ""}
    ${article.source_url ? `<a href="${article.source_url}" target="_blank" rel="noopener" class="secondary-button" style="margin-top:12px">Original source →</a>` : ""}
  `;

  openModal();
}

function openModal() {
  articleModal.classList.add("open");
  articleModal.setAttribute("aria-hidden","false");
  // Focus trap: collect focusables
  const focusable = articleModal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (focusable.length) {
    firstFocusableInModal = focusable[0];
    firstFocusableInModal.focus();
  }
  // Trap tab within modal
  articleModal._trapFn = (e) => {
    if (e.key !== "Tab") return;
    const els = [...articleModal.querySelectorAll('button, [href], input, select, [tabindex]:not([tabindex="-1"])')];
    if (!els.length) return;
    const first = els[0], last = els[els.length-1];
    if (e.shiftKey) { if (document.activeElement === first) { e.preventDefault(); last.focus(); } }
    else { if (document.activeElement === last) { e.preventDefault(); first.focus(); } }
  };
  document.addEventListener("keydown", articleModal._trapFn);
}

function closeModal() {
  articleModal.classList.remove("open");
  articleModal.setAttribute("aria-hidden","true");
  document.removeEventListener("keydown", articleModal._trapFn);
}

/* ── READ TRACKING ────────────────────────────────────────────── */
async function markRead(id, btn) {
  btn.disabled = true;
  btn.textContent = "Saving…";
  try {
    if (!isDemo) {
      await api(`/api/articles/${id}/read`, {
        method: "POST",
        body: JSON.stringify({ user_id: userId, exam_type: selectedExam }),
      });
    }
    btn.textContent = "✓ Read";
    btn.style.background = "var(--green)";
    btn.style.borderColor = "var(--green)";
    await loadDashboard();
    await loadRevision();
  } catch (e) {
    btn.textContent = "Retry";
    btn.disabled = false;
    console.error(e);
  }
}

/* ── REVISION ─────────────────────────────────────────────────── */
async function loadRevision() {
  if (isDemo) {
    revisionMessage.textContent = DEMO_REVISION.message;
    revisionQuestions = DEMO_REVISION.questions;
    return;
  }
  try {
    const data = await api(`/api/revision/due/${userId}`);
    revisionMessage.textContent = data.message;
    revisionQuestions = data.questions || [];
  } catch {}
}

/* ── QUIZ ENGINE ──────────────────────────────────────────────── */
function currentPool() {
  return quizMode === "revision" ? revisionQuestions : dailyQuizPool;
}

function showQuizContent(show) {
  quizLoading.hidden = show;
  quizQuestion.hidden = !show;
  nextQuestionBtn.hidden = !show;
}

function updateDonut(score) {
  const circ = 2 * Math.PI * 28; // r=28
  const filled = (score / 100) * circ;
  donutFill.setAttribute("stroke-dasharray", `${filled.toFixed(1)} ${circ.toFixed(1)}`);
}

function renderQuiz() {
  const pool = currentPool();
  quizResultEl.textContent = "";
  answeredCurrent = false;

  if (!pool.length) {
    showQuizContent(false);
    quizLoading.hidden = false;
    quizLoading.querySelector("p").textContent = quizMode === "revision"
      ? "No revision due. Mark articles as read first."
      : "No questions available yet.";
    quizLoading.querySelector(".spinner").style.display = "none";
    return;
  }

  showQuizContent(true);
  const item = pool[quizIndex];
  const mcq  = quizMode === "revision" ? item.mcq : item;

  $("quiz-category").textContent = quizMode === "revision"
    ? `${item.category} · ${(item.article_title||"").slice(0,42)}`
    : item.category;
  $("quiz-progress").textContent = `${quizIndex + 1} / ${pool.length}`;
  quizQuestion.textContent = mcq.question;

  quizOptions.innerHTML = mcq.options.map(opt =>
    `<button class="option-button" data-option="${opt.replace(/"/g,"&quot;")}">${opt}</button>`
  ).join("");
}

function handleAnswer(btn) {
  if (answeredCurrent) return;
  answeredCurrent = true;

  const pool = currentPool();
  const item = pool[quizIndex];
  const mcq  = quizMode === "revision" ? item.mcq : item;
  const chosen = btn.dataset.option;
  const correct = chosen === mcq.answer;

  // Reveal all correct/wrong
  $$(".option-button").forEach(b => {
    b.disabled = true;
    if (b.dataset.option === mcq.answer) b.classList.add("correct");
  });
  if (!correct) btn.classList.add("wrong");
  if (correct) correctAnswers++;

  quizResultEl.textContent = correct
    ? `✓ Correct. ${mcq.explanation||""}`
    : `✗ ${mcq.explanation||""} Answer: ${mcq.answer}`;

  // Score
  const answered = quizIndex + 1;
  const score = Math.round((correctAnswers / answered) * 100);
  $("quiz-score").textContent = `${score}%`;
  $("quiz-feedback").textContent = score >= 70 ? "Strong recall." : "Needs more repetition.";
  updateDonut(score);
}

async function advanceQuiz() {
  const pool = currentPool();
  if (quizIndex >= pool.length - 1) {
    // End of quiz — submit revision if needed
    if (quizMode === "revision" && !isDemo && revisionQuestions.length) {
      try {
        await api("/api/revision/submit", {
          method: "POST",
          body: JSON.stringify({
            user_id: userId,
            schedule_ids: revisionQuestions.map(q=>q.schedule_id),
            correct_count: correctAnswers,
            total_count: revisionQuestions.length,
          }),
        });
      } catch {}
    }
    quizIndex = 0;
    correctAnswers = 0;
    await loadDashboard();
  } else {
    quizIndex++;
  }
  renderQuiz();
}

async function buildDailyQuiz() {
  showQuizContent(false);
  quizLoading.hidden = false;
  quizLoading.querySelector(".spinner").style.display = "";
  quizLoading.querySelector("p").textContent = "Building your quiz from today's news…";

  if (isDemo) {
    dailyQuizPool = DEMO_MODE_ARTICLES.filter(a=>a.include && a.mcqs.length).map(a=>({
      category: a.category, article_title: a.title, ...a.mcqs[0]
    }));
    if (!dailyQuizPool.length) dailyQuizPool = [fallbackQ()];
    quizMode = "daily";
    hidQuizModeBanner();
    renderQuiz();
    return;
  }

  // Parallel fetch — much faster than sequential
  const published = articles.filter(a=>a.include).slice(0,10);
  const results = await Promise.allSettled(
    published.map(a => api(`/api/articles/${a.id}`))
  );
  dailyQuizPool = results
    .filter(r=>r.status==="fulfilled" && r.value.mcqs?.[0])
    .map(r=>({ category: r.value.category, article_title: r.value.title, ...r.value.mcqs[0] }));

  if (!dailyQuizPool.length) dailyQuizPool = [fallbackQ()];
  quizMode = "daily";
  hidQuizModeBanner();
  renderQuiz();
}

function fallbackQ() {
  return {
    category:"General",
    question:"What is the core learning loop of ExamMemory AI?",
    options:["Read today, revise tomorrow","Only daily reading","Weekly test only","Monthly mock test"],
    answer:"Read today, revise tomorrow",
    explanation:"Spaced repetition: read → quiz next day → recall at Day 7/21/45."
  };
}

function showQuizModeBanner(label) {
  quizModeLabel.textContent = label;
  quizModeBanner.hidden = false;
}
function hidQuizModeBanner() { quizModeBanner.hidden = true; }

async function startRevisionQuiz() {
  quizMode = "revision";
  quizIndex = 0;
  correctAnswers = 0;
  answeredCurrent = false;

  if (!revisionQuestions.length) {
    renderQuiz();
    document.querySelector("#quiz").scrollIntoView({ behavior:"smooth" });
    return;
  }
  showQuizModeBanner(`Revision quiz — ${revisionQuestions.length} topics`);
  renderQuiz();
  document.querySelector("#quiz").scrollIntoView({ behavior:"smooth" });
}

/* ── SEARCH ───────────────────────────────────────────────────── */
function renderSearchResults(term="") {
  const q = term.trim().toLowerCase();
  searchClear.hidden = !q;

  const pool = articles.filter(a=>a.include);
  const matches = q
    ? pool.filter(a => `${a.title} ${a.category} ${(a.tags||[]).join(" ")} ${a.source_name}`.toLowerCase().includes(q))
    : pool;

  if (!matches.length) {
    searchResults.innerHTML = q
      ? `<p class="loading">No results for "<strong>${q}</strong>". Try RBI, ISRO, climate, or Indo-Pacific.</p>`
      : "";
    return;
  }

  searchResults.innerHTML = matches.map(a =>
    `<article class="search-result" data-open="${a.id}">
      <strong>${a.title}</strong>
      <p>${a.category} · ${(a.tags||[]).join(", ")} · ${a.importance_score}/10 importance</p>
    </article>`
  ).join("");
}

/* ── DARK MODE ────────────────────────────────────────────────── */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  themeIcon.className = theme === "dark" ? "bx bx-sun" : "bx bx-moon";
  localStorage.setItem("exammemory_theme", theme);
}
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(current === "dark" ? "light" : "dark");
}

/* ── EVENT LISTENERS ──────────────────────────────────────────── */

// Mobile menu
menuButton.addEventListener("click", () => {
  const open = nav.classList.toggle("open");
  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.querySelector("i").className = open ? "bx bx-x" : "bx bx-menu";
});
$$(".nav a").forEach(link => {
  link.addEventListener("click", () => {
    nav.classList.remove("open");
    menuButton.setAttribute("aria-expanded","false");
    menuButton.querySelector("i").className = "bx bx-menu";
  });
});

// Exam chips
$$("[data-exam]").forEach(btn => {
  if (btn.dataset.exam === selectedExam) btn.classList.add("active");
  btn.addEventListener("click", () => {
    selectedExam = btn.dataset.exam;
    localStorage.setItem("exammemory_exam", selectedExam);
    $$("[data-exam]").forEach(b => b.classList.toggle("active", b===btn));
    renderArticles(); // re-render with new mode note; no refetch needed
  });
});

// Article list clicks (open or mark-read)
articleList.addEventListener("click", async e => {
  const openBtn = e.target.closest("[data-open]");
  if (openBtn) { await openArticle(openBtn.dataset.open); return; }
  const readBtn = e.target.closest("[data-read]");
  if (readBtn) await markRead(readBtn.dataset.read, readBtn);
});

// Search results click
searchResults.addEventListener("click", async e => {
  const card = e.target.closest("[data-open]");
  if (card) await openArticle(card.dataset.open);
});

// Modal close
modalClose.addEventListener("click", closeModal);
articleModal.addEventListener("click", e => { if (e.target===articleModal) closeModal(); });
document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  if (articleModal.classList.contains("open")) closeModal();
  if (authModal.classList.contains("open")) closeAuthModal();
});

authOpen.addEventListener("click", () => openAuthModal(authUser ? "login" : "login"));
async function signOut() {
  clearAuthSession();
  userId = null;
  localStorage.removeItem("exammemory_user_id");
  closeAuthModal();
  await ensureUser();
  await refreshUserData();
}

authLogout.addEventListener("click", signOut);
$("auth-signout-btn")?.addEventListener("click", signOut);
authModalClose.addEventListener("click", closeAuthModal);
authModal.addEventListener("click", e => { if (e.target === authModal) closeAuthModal(); });
$$("[data-auth-tab]").forEach(btn => btn.addEventListener("click", () => setAuthTab(btn.dataset.authTab)));
authForm.addEventListener("submit", handleAuthSubmit);

// Quiz options
quizOptions.addEventListener("click", e => {
  const btn = e.target.closest(".option-button");
  if (btn && !answeredCurrent) handleAnswer(btn);
});

// Next question
nextQuestionBtn.addEventListener("click", advanceQuiz);

// Start revision
startRevisionBtn.addEventListener("click", startRevisionQuiz);

// Switch back to daily quiz
switchDailyBtn.addEventListener("click", () => {
  quizMode = "daily";
  quizIndex = 0;
  correctAnswers = 0;
  hidQuizModeBanner();
  renderQuiz();
});

// Search input
searchInput.addEventListener("input", e => renderSearchResults(e.target.value));
searchClear.addEventListener("click", () => {
  searchInput.value = "";
  searchClear.hidden = true;
  renderSearchResults("");
  searchInput.focus();
});

// Offline banner dismiss
offlineClose.addEventListener("click", () => {
  offlineBanner.hidden = true;
  document.body.classList.remove("has-banner");
});

// Dark mode
themeToggle.addEventListener("click", toggleTheme);

// Reveal on scroll
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add("visible");
      revealObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
$$(".reveal").forEach(el => revealObserver.observe(el));

// Active nav highlight
const sectionObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    $$(".nav a").forEach(a =>
      a.classList.toggle("active", a.getAttribute("href") === `#${e.target.id}`)
    );
  });
}, { rootMargin:"-30% 0px -60% 0px" });
$$("section[id]").forEach(s => sectionObserver.observe(s));

/* ── BOOT ─────────────────────────────────────────────────────── */
async function boot() {
  // Restore theme
  const savedTheme = localStorage.getItem("exammemory_theme");
  if (savedTheme) applyTheme(savedTheme);
  else if (window.matchMedia("(prefers-color-scheme: dark)").matches) applyTheme("dark");

  renderDate();

  try {
    const health = await api("/api/health");
    const pill = $("status-pill");
    pill.textContent = health.ai ? "AI on" : "Rule-based";
    pill.classList.add("live");
    isDemo = false;
  } catch {
    activateDemo();
  }

  try { await ensureUser(); } catch {}
  renderAuthBar();
  await loadArticles();
  await loadDashboard();
  await loadRevision();
  renderSearchResults();
  await buildDailyQuiz();
}

boot();

/* ═══════════════════════════════════════════════════════════════
   NEW FEATURES — Weekly Test, Mock Test, Leaderboard,
                  AI Doubt Solver, PYQ Matcher, PDF Download
   ═══════════════════════════════════════════════════════════════ */

// ── Weekly Test ────────────────────────────────────────────────
let weeklyTest     = null;
let weeklyQIdx     = 0;
let weeklyCorrect  = 0;
let weeklyAnswers  = [];
let weeklyAnswered = false;

async function loadWeeklyTest() {
  try {
    weeklyTest = await api("/api/weekly-test");
    const lbl = $("weekly-week-label");
    if (lbl) lbl.textContent = weeklyTest.week_label;
    await loadWeeklyLB();
  } catch(e) { console.warn("[weekly]", e); }
}

async function loadWeeklyLB() {
  const lb = $("weekly-lb-list");
  if (!lb) return;
  try {
    const data = await api("/api/weekly-test/leaderboard");
    if (!data.length) { lb.innerHTML = `<p class="loading">No attempts yet — be first!</p>`; return; }
    lb.innerHTML = data.slice(0,10).map((e,i) => `
      <div class="lb-entry">
        <div class="lb-rank ${i===0?'gold':i===1?'silver':i===2?'bronze':''}">${e.rank}</div>
        <div class="lb-name">Student ${e.user_id.slice(0,4).toUpperCase()}</div>
        <div class="lb-score">${e.score_pct}%</div>
      </div>`).join("");
  } catch { lb.innerHTML = `<p class="loading">—</p>`; }
}

function startWeeklyTest() {
  if (!weeklyTest?.questions?.length) return;
  weeklyQIdx = 0; weeklyCorrect = 0; weeklyAnswers = []; weeklyAnswered = false;
  $("weekly-intro").hidden      = true;
  $("weekly-quiz-wrap").hidden  = false;
  $("weekly-result-wrap").hidden= true;
  renderWeeklyQ();
}

function renderWeeklyQ() {
  const q = weeklyTest.questions[weeklyQIdx];
  weeklyAnswered = false;
  $("weekly-cat").textContent  = q.category || "General";
  $("weekly-prog").textContent = `${weeklyQIdx + 1} / ${weeklyTest.questions.length}`;
  $("weekly-bar").style.width  = `${((weeklyQIdx + 1) / weeklyTest.questions.length) * 100}%`;
  $("weekly-q-text").textContent = q.question;
  $("weekly-result").textContent = "";
  $("weekly-next").hidden = true;
  $("weekly-opts").innerHTML = (q.options || []).map(opt =>
    `<button class="option-button" data-ans="${opt}">${opt}</button>`
  ).join("");
}

function handleWeeklyAnswer(btn) {
  if (weeklyAnswered) return;
  weeklyAnswered = true;
  const q = weeklyTest.questions[weeklyQIdx];
  const chosen = btn.dataset.ans;
  const correct = chosen === q.answer;
  if (correct) weeklyCorrect++;
  weeklyAnswers.push({ q_index: weeklyQIdx, chosen });
  $("weekly-opts").querySelectorAll(".option-button").forEach(b => {
    b.disabled = true;
    if (b.dataset.ans === q.answer) b.classList.add("correct");
  });
  if (!correct) btn.classList.add("wrong");
  $("weekly-result").textContent = correct
    ? `✓ Correct. ${q.explanation || ""}` : `✗ ${q.explanation || ""} Answer: ${q.answer}`;
  $("weekly-next").hidden = false;
}

async function advanceWeeklyQ() {
  weeklyQIdx++;
  if (weeklyQIdx >= weeklyTest.questions.length) {
    await submitWeeklyTest();
  } else {
    renderWeeklyQ();
  }
}

async function submitWeeklyTest() {
  let result;
  try {
    result = await api("/api/weekly-test/submit", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, test_id: weeklyTest.id, answers: weeklyAnswers })
    });
  } catch {
    const total = weeklyTest.questions.length;
    result = { score_pct: Math.round(weeklyCorrect / total * 100), correct: weeklyCorrect,
               total, feedback: "Test complete!", weak_areas: [] };
  }
  $("weekly-quiz-wrap").hidden   = true;
  $("weekly-result-wrap").hidden = false;
  $("weekly-score-big").textContent     = `${result.score_pct}%`;
  $("weekly-feedback-text").textContent = result.feedback;
  $("weekly-stats-row").innerHTML = `
    <div class="result-stat-box"><strong>${result.correct}</strong><span>Correct</span></div>
    <div class="result-stat-box"><strong>${result.total - result.correct}</strong><span>Wrong</span></div>
    <div class="result-stat-box"><strong>${(result.weak_areas || []).join(", ") || "None"}</strong><span>Weak areas</span></div>`;
  await loadWeeklyLB();
}

// ── Mock Test ──────────────────────────────────────────────────
let mockTest      = null;
let mockQIdx      = 0;
let mockAnswers   = [];
let mockTimerSecs = 7200;
let mockTimerRef  = null;

async function loadMockTest() {
  const exam = $("mock-exam-select")?.value || "UPSC";
  try {
    mockTest = await api(`/api/mock-test?exam_type=${exam}`);
    const lbl = $("mock-month-label");
    if (lbl) lbl.textContent = mockTest.month_label;
    await loadMockLB();
  } catch(e) { console.warn("[mock]", e); }
}

async function loadMockLB() {
  const lb = $("mock-lb-list");
  if (!lb) return;
  try {
    const data = await api("/api/mock-test/leaderboard");
    if (!data.length) { lb.innerHTML = `<p class="loading">No attempts yet — be first!</p>`; return; }
    lb.innerHTML = data.slice(0,10).map((e,i) => `
      <div class="lb-entry">
        <div class="lb-rank ${i===0?'gold':i===1?'silver':i===2?'bronze':''}">${e.rank}</div>
        <div class="lb-name">${e.user_name}</div>
        <div class="lb-score">${e.score_pct}%</div>
      </div>`).join("");
  } catch { lb.innerHTML = `<p class="loading">—</p>`; }
}

function startMockTest() {
  if (!mockTest?.questions?.length) return;
  mockQIdx = 0;
  mockAnswers = mockTest.questions.map((_,i) => ({ q_index: i, chosen: "" }));
  mockTimerSecs = 7200;
  $("mock-intro").hidden      = true;
  $("mock-quiz-wrap").hidden  = false;
  $("mock-result-wrap").hidden= true;
  renderMockQ();
  startMockTimer();
}

function startMockTimer() {
  if (mockTimerRef) clearInterval(mockTimerRef);
  mockTimerRef = setInterval(() => {
    mockTimerSecs--;
    const h = Math.floor(mockTimerSecs / 3600);
    const m = Math.floor((mockTimerSecs % 3600) / 60);
    const s = mockTimerSecs % 60;
    const el = $("mock-timer");
    if (el) {
      el.textContent = `${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
      if (mockTimerSecs <= 300) el.classList.add("danger");
    }
    if (mockTimerSecs <= 0) { clearInterval(mockTimerRef); submitMockTest(); }
  }, 1000);
}

function renderMockQ() {
  if (!mockTest) return;
  const q = mockTest.questions[mockQIdx];
  $("mock-cat").textContent  = q.category || "General";
  $("mock-prog").textContent = `${mockQIdx + 1} / ${mockTest.questions.length}`;
  $("mock-bar").style.width  = `${((mockQIdx + 1) / mockTest.questions.length) * 100}%`;
  $("mock-q-text").textContent = `Q${mockQIdx + 1}. ${q.question}`;
  const prev = mockAnswers[mockQIdx]?.chosen || "";
  $("mock-opts").innerHTML = (q.options || []).map(opt =>
    `<button class="option-button ${prev === opt ? "selected" : ""}" data-ans="${opt}">${opt}</button>`
  ).join("");
}

function handleMockAnswer(btn) {
  mockAnswers[mockQIdx] = { q_index: mockQIdx, chosen: btn.dataset.ans };
  $("mock-opts").querySelectorAll(".option-button").forEach(b => b.classList.remove("selected"));
  btn.classList.add("selected");
  setTimeout(() => {
    if (mockQIdx < mockTest.questions.length - 1) { mockQIdx++; renderMockQ(); }
  }, 350);
}

async function submitMockTest() {
  if (mockTimerRef) clearInterval(mockTimerRef);
  const timeTaken = 7200 - mockTimerSecs;
  let result;
  try {
    result = await api("/api/mock-test/submit", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId, test_id: mockTest.id,
        answers: mockAnswers.filter(a => a.chosen), time_taken: timeTaken
      })
    });
  } catch {
    const correct = mockAnswers.filter((a,i) => a.chosen === mockTest.questions[i]?.answer).length;
    const total   = mockTest.questions.length;
    result = { score_pct: Math.round(correct/total*100), correct, wrong: mockAnswers.filter(a=>a.chosen).length - correct,
               unattempted: mockAnswers.filter(a=>!a.chosen).length, total, marks_scored: correct*2,
               max_marks: total*2, time_taken_secs: timeTaken, rank: 1, total_attempts: 1, feedback:"Test complete!" };
  }
  $("mock-quiz-wrap").hidden   = true;
  $("mock-result-wrap").hidden = false;
  $("mock-score-big").textContent     = `${result.score_pct}%`;
  $("mock-feedback-text").textContent = result.feedback;
  $("mock-stats-grid").innerHTML = [
    ["Correct",   result.correct],
    ["Wrong",     result.wrong],
    ["Skipped",   result.unattempted],
    ["Marks",     result.marks_scored ?? "—"],
    ["Max",       result.max_marks ?? "—"],
    ["Time",      `${Math.floor((result.time_taken_secs||0)/60)}m`],
  ].map(([l,v]) =>
    `<div class="result-stat-box"><strong>${v}</strong><span>${l}</span></div>`
  ).join("");
  $("mock-rank-badge").textContent =
    `🏆 All-India Rank: ${result.rank} out of ${result.total_attempts} students`;
  await loadMockLB();
}

// ── Full Leaderboard ───────────────────────────────────────────
async function loadLeaderboard(period = "weekly") {
  const tbody = $("lb-body");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6" class="loading">Loading...</td></tr>`;
  try {
    const data = await api(`/api/leaderboard?period=${period}&exam_type=${selectedExam || "UPSC"}`);
    if (!data.entries?.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="loading">No data yet — start reading and taking tests!</td></tr>`;
      return;
    }
    tbody.innerHTML = data.entries.map(e => `
      <tr class="${e.user_id === userId ? "me" : ""}">
        <td><strong>${e.rank <= 3 ? ["🥇","🥈","🥉"][e.rank-1] : e.rank}</strong></td>
        <td>${e.user_name}${e.user_id === userId ? " <em>(you)</em>" : ""}</td>
        <td>${e.exam_type}</td>
        <td><strong>${e.score}</strong></td>
        <td>🔥 ${e.streak_days}d</td>
        <td>${e.xp_points} XP</td>
      </tr>`).join("");
    // My rank card
    if (userId) {
      try {
        const me = await api(`/api/leaderboard/me/${userId}?period=${period}&exam_type=${selectedExam || "UPSC"}`);
        const card = $("my-rank-card");
        if (me.rank && card) {
          card.hidden = false;
          $("my-rank-content").innerHTML =
            `<strong>Rank #${me.rank}</strong> out of ${me.total_users} students
             &nbsp;·&nbsp; Score: ${me.score} XP &nbsp;·&nbsp; ${me.period_label}`;
        }
      } catch {}
    }
  } catch {
    tbody.innerHTML = `<tr><td colspan="6" class="error">Could not load leaderboard.</td></tr>`;
  }
}

// ── AI Doubt Solver ────────────────────────────────────────────
let currentArticleId = null;

async function askDoubt() {
  const input = $("doubt-input");
  const q = input?.value.trim();
  if (!q) return;
  const btn = $("doubt-ask-btn");
  btn.disabled = true;
  btn.innerHTML = `<i class="bx bx-loader-alt bx-spin"></i>`;
  const ansEl = $("doubt-answer");
  ansEl.hidden = true;
  try {
    const res = await api("/api/doubt", {
      method: "POST",
      body: JSON.stringify({ question: q, article_id: currentArticleId || "" })
    });
    ansEl.hidden = false;
    ansEl.innerHTML = `
      <p>${res.answer}</p>
      ${res.exam_tip ? `<p class="exam-tip">${res.exam_tip}</p>` : ""}
      <span class="source-tag">Answered by: ${res.source}</span>`;
  } catch {
    ansEl.hidden = false;
    ansEl.innerHTML = `<p class="error">Could not get answer. Check your connection or try again.</p>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="bx bx-send"></i>`;
    if (input) input.value = "";
  }
}

// ── PYQ Loader ─────────────────────────────────────────────────
async function loadPYQs(articleId) {
  const list = $("pyq-list");
  if (!list) return;
  list.innerHTML = `<p class="loading">Finding related past year questions...</p>`;
  try {
    const res  = await api(`/api/articles/${articleId}/pyqs`);
    const pyqs = res.pyqs || [];
    if (!pyqs.length) {
      list.innerHTML = `<p class="loading">No matching PYQs found for this topic yet.</p>`;
      return;
    }
    list.innerHTML = pyqs.map(p => `
      <div class="pyq-card">
        <span class="pyq-badge">${p.exam}</span>
        <span class="pyq-badge">${p.year}</span>
        <span class="pyq-badge">${p.paper}</span>
        <p class="pyq-q">${p.question}</p>
        <p class="pyq-ans">✓ ${p.answer}</p>
        <p class="pyq-exp">${p.explanation}</p>
        <small style="color:var(--muted);font-size:11px">${p.match_note}</small>
      </div>`).join("");
  } catch {
    list.innerHTML = `<p class="loading">PYQs unavailable in offline mode.</p>`;
  }
}

// ── PDF Download ───────────────────────────────────────────────
function downloadPDF() {
  const exam = (typeof selectedExam !== "undefined" ? selectedExam : null) || "UPSC";
  const url  = `${API_BASE}/api/pdf/monthly?exam_type=${exam}`;
  const a    = document.createElement("a");
  a.href = url; a.target = "_blank";
  a.download = `ExamMemory-CurrentAffairs-${exam}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ── Override openArticle to wire PYQs + doubt solver ──────────
// Store original openArticle defined in the base scripts.js
const _baseOpenArticle = typeof openArticle === "function" ? openArticle : null;

async function openArticle(id) {
  currentArticleId = id;

  // ── Replicate original open logic (base scripts.js may define its own) ──
  let article = (typeof articles !== "undefined" ? articles : []).find(a => String(a.id) === String(id));
  if (article) {
    try { article = await api(`/api/articles/${id}`); } catch {}
  }
  if (!article) return;

  const isDeep = ["UPSC","State PSC"].includes(typeof selectedExam !== "undefined" ? selectedExam : "UPSC");
  const block  = (isDeep ? article.deep : article.quick) || article.quick || article.deep || {};
  const mcq    = article.mcqs?.[0];

  const modalBody = $("modal-body");
  if (modalBody) {
    modalBody.innerHTML = `
      <p id="modal-title" style="color:var(--green);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">
        ${article.source_name} · ${article.category} · ${article.importance_score}/10
      </p>
      <h3 style="font-size:20px;margin-bottom:14px">${article.title}</h3>
      ${block.why_in_news ? `<p><strong>Why in News:</strong> ${block.why_in_news}</p>` : ""}
      ${block.key_facts?.length ? `<p style="margin-top:10px"><strong>Key Facts:</strong></p><ul>${block.key_facts.map(f=>`<li>${f}</li>`).join("")}</ul>` : ""}
      ${block.background ? `<p style="margin-top:10px"><strong>Background:</strong> ${block.background}</p>` : ""}
      ${block.exam_relevance ? `<p style="margin-top:10px"><strong>Exam Relevance:</strong> ${block.exam_relevance}</p>` : ""}
      ${block.keywords?.length ? `<p style="margin-top:10px"><strong>Keywords:</strong> ${block.keywords.join(", ")}</p>` : ""}
      ${block.revision_notes ? `<p style="margin-top:10px"><strong>2-Min Revision:</strong> ${block.revision_notes}</p>` : ""}
      ${mcq ? `<div class="mcq-box" style="margin-top:14px"><strong>MCQ</strong><p>${mcq.question}</p><span>Answer: ${mcq.answer}</span>${mcq.explanation?`<p style="margin-top:6px;font-size:12.5px;color:var(--muted)">${mcq.explanation}</p>`:""}</div>` : ""}
      ${article.source_url ? `<a href="${article.source_url}" target="_blank" rel="noopener" class="secondary-button" style="margin-top:14px;display:inline-flex">Original source →</a>` : ""}`;
  }

  // Open modal
  const modal = $("article-modal");
  if (modal) {
    modal.classList.add("open");
    modal.setAttribute("aria-hidden","false");
  }

  // Reset doubt + load PYQs
  const di = $("doubt-input");
  const da = $("doubt-answer");
  if (di) di.value = "";
  if (da) da.hidden = true;
  loadPYQs(id);
}

// ── Wire up all new event listeners on DOMContentLoaded ───────
document.addEventListener("DOMContentLoaded", () => {

  // Weekly Test
  $("start-weekly-btn")?.addEventListener("click", startWeeklyTest);
  $("weekly-next")?.addEventListener("click", advanceWeeklyQ);
  $("weekly-retry-btn")?.addEventListener("click", () => {
    $("weekly-result-wrap").hidden = true;
    $("weekly-intro").hidden = false;
  });
  $("weekly-opts")?.addEventListener("click", e => {
    const btn = e.target.closest(".option-button");
    if (btn && !weeklyAnswered) handleWeeklyAnswer(btn);
  });

  // Mock Test
  $("start-mock-btn")?.addEventListener("click", async () => {
    if (!mockTest) await loadMockTest();
    startMockTest();
  });
  $("mock-exam-select")?.addEventListener("change", loadMockTest);
  $("mock-opts")?.addEventListener("click", e => {
    const btn = e.target.closest(".option-button");
    if (btn) handleMockAnswer(btn);
  });
  $("mock-skip-btn")?.addEventListener("click", () => {
    if (mockQIdx < (mockTest?.questions?.length || 0) - 1) { mockQIdx++; renderMockQ(); }
  });
  $("mock-submit-btn")?.addEventListener("click", submitMockTest);

  // Leaderboard period chips
  $$("[data-period]").forEach(btn => {
    btn.addEventListener("click", () => {
      $$("[data-period]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadLeaderboard(btn.dataset.period);
    });
  });

  // AI Doubt Solver
  $("doubt-ask-btn")?.addEventListener("click", askDoubt);
  $("doubt-input")?.addEventListener("keydown", e => { if (e.key === "Enter") askDoubt(); });

  // PDF download button — inject into gamification section heading
  const gamSection = document.querySelector(".gamification-section .section-heading");
  if (gamSection) {
    const btn = document.createElement("a");
    btn.className = "pdf-download-btn";
    btn.href = "#";
    btn.innerHTML = `<i class="bx bx-file-pdf"></i> Download Monthly PDF`;
    btn.addEventListener("click", e => { e.preventDefault(); downloadPDF(); });
    gamSection.appendChild(btn);
  }

  // Escape closes article modal
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      const m = $("article-modal");
      if (m?.classList.contains("open")) {
        m.classList.remove("open");
        m.setAttribute("aria-hidden","true");
      }
    }
  });
});

// ── Load new features after base boot finishes ─────────────────
(function scheduleFeatureLoad() {
  const run = async () => {
    await loadWeeklyTest();
    await loadMockTest();
    await loadLeaderboard("weekly");
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(run, 2000));
  } else {
    setTimeout(run, 2000);
  }
})();
