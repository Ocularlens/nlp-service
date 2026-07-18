/* ============================================================
 * Review Analyzer — ESM Module
 * ============================================================ */

// ---- DOM refs ----
const form = document.getElementById("review-form");
const textInput = document.getElementById("review-text");
const productInput = document.getElementById("product-name");
const toggleCheckbox = document.getElementById("translation-toggle");
const translationOpts = document.getElementById("translation-options");
const langInput = document.getElementById("source-language");
const submitBtn = document.getElementById("submit-btn");
const resultSection = document.getElementById("result-section");
const resultContent = document.getElementById("result-content");
const toast = document.getElementById("toast");
const toastMsg = document.getElementById("toast-message");
const toastClose = document.getElementById("toast-close");
const leaderboardContent = document.getElementById("leaderboard-content");
const leaderboardRefreshBtn = document.getElementById("leaderboard-refresh-btn");

// ---- State helpers ----
function setLoading(loading) {
  submitBtn.disabled = loading;
  submitBtn.innerHTML = loading
    ? '<span class="spinner"></span> Analyzing…'
    : "Analyze Review";
}

// ---- Toast ----
function showToast(message) {
  toastMsg.textContent = message;
  toast.classList.add("visible");
}

function hideToast() {
  toast.classList.remove("visible");
}

toastClose.addEventListener("click", hideToast);

// Auto-hide toast after 5 s
function autoHideToast() {
  setTimeout(hideToast, 5000);
}

// ---- Translation toggle ----
toggleCheckbox.addEventListener("change", () => {
  translationOpts.classList.toggle("visible", toggleCheckbox.checked);
  if (!toggleCheckbox.checked) {
    langInput.value = "";
    langInput.removeAttribute("required");
  } else {
    langInput.setAttribute("required", "required");
  }
});

// ---- Render result ----
function renderResult(data) {
  const { message, analysis_result, review_id } = data;
  const {
    mood,
    sentiment_score,
    positive_count,
    negative_count,
    signals,
  } = analysis_result;

  // Mood badge class
  const moodClass = mood.toLowerCase();

  // Signals HTML
  const signalsHtml =
    signals && signals.length > 0
      ? `<div class="signals-list">
          <h3>Signals (${signals.length})</h3>
          <ul>${signals.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
        </div>`
      : "";

  resultContent.innerHTML = `
      <div class="result-message success">
        <span>✅</span> ${escapeHtml(message)}
      </div>

      <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:0.5rem;">
        <span>Mood:</span>
        <span class="result-mood ${moodClass}">${escapeHtml(mood)}</span>
      </div>

      <div class="result-grid">
        <div class="result-stat">
          <div class="value ${moodClass}-val">${sentiment_score}</div>
          <div class="label">Sentiment Score</div>
        </div>
        <div class="result-stat">
          <div class="value positive-val">${positive_count}</div>
          <div class="label">Positive Words</div>
        </div>
        <div class="result-stat">
          <div class="value negative-val">${negative_count}</div>
          <div class="label">Negative Words</div>
        </div>
      </div>

      ${signalsHtml}

      <div class="result-footer">
        <span>Review ID:</span>
        <code>${escapeHtml(review_id)}</code>
      </div>
    `;

  resultSection.classList.add("visible");
  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---- Escape HTML ----
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---- Submit review ----
async function submitReview(text, productName, translation) {
  const body = { text, productName };
  if (translation) {
    body.translation = { source_language: translation };
  }

  const response = await fetch("/api/v1/reviews/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = `Server error (${response.status})`;
    try {
      const err = await response.json();
      if (err.detail) detail = err.detail;
      else if (err.message) detail = err.message;
    } catch (_) {
      /* use default */
    }
    throw new Error(detail);
  }

  return response.json();
}

// ---- Form submit handler ----
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideToast();

  const text = textInput.value.trim();
  const productName = productInput.value.trim();
  const translation = toggleCheckbox.checked
    ? langInput.value.trim()
    : null;

  // Client-side validation
  if (text.length < 3 || text.length > 120) {
    showToast("Review text must be between 3 and 120 characters.");
    autoHideToast();
    textInput.focus();
    return;
  }
  if (!productName || productName.length > 64) {
    showToast("Product name is required (max 64 characters).");
    autoHideToast();
    productInput.focus();
    return;
  }
  if (
    translation &&
    (!langInput.value.trim() || langInput.value.trim().length < 2)
  ) {
    showToast("Please enter a valid language code (e.g. es, fr, auto).");
    autoHideToast();
    langInput.focus();
    return;
  }

  setLoading(true);

  try {
    const data = await submitReview(
      text,
      productName,
      translation || undefined,
    );
    renderResult(data);
    // Refresh leaderboard after a successful review submission
    loadLeaderboard();
  } catch (err) {
    showToast(err.message || "An unexpected error occurred.");
    autoHideToast();
  } finally {
    setLoading(false);
  }
});

// ---- Reset result when form changes (optional UX) ----
// If user starts editing, hide the old result to avoid confusion
function onFormChange() {
  resultSection.classList.remove("visible");
}
textInput.addEventListener("input", onFormChange);
productInput.addEventListener("input", onFormChange);

// ============================================================
//  Leaderboard
// ============================================================

// ---- Fetch leaderboard ----
async function fetchLeaderboard(limit = 10) {
  const response = await fetch(`/api/v1/leaderboard/?limit=${limit}`);
  if (!response.ok) {
    let detail = `Server error (${response.status})`;
    try {
      const err = await response.json();
      if (err.detail) detail = err.detail;
    } catch (_) { /* use default */ }
    throw new Error(detail);
  }
  return response.json();
}

// ---- Render leaderboard ----
function getMedal(rank) {
  if (rank === 1) return '<span class="rank-medal">🥇</span>';
  if (rank === 2) return '<span class="rank-medal">🥈</span>';
  if (rank === 3) return '<span class="rank-medal">🥉</span>';
  return rank;
}

function getScoreClass(score) {
  if (score > 0) return "score-positive";
  if (score < 0) return "score-negative";
  return "score-zero";
}

function getScorePrefix(score) {
  return score > 0 ? "+" : "";
}

function renderLeaderboard(data) {
  const { leaderboard } = data;

  if (!leaderboard || leaderboard.length === 0) {
    leaderboardContent.innerHTML = `
      <div class="leaderboard-empty">
        <div class="icon">📭</div>
        <p>No reviews yet. Be the first to submit one!</p>
      </div>
    `;
    return;
  }

  const rowsHtml = leaderboard
    .map(
      (entry, i) => `
        <tr>
          <td class="col-rank">${getMedal(i + 1)}</td>
          <td>${escapeHtml(entry.product_name)}</td>
          <td class="col-score ${getScoreClass(entry.total_score)}">
            ${getScorePrefix(entry.total_score)}${entry.total_score}
          </td>
        </tr>
      `,
    )
    .join("");

  leaderboardContent.innerHTML = `
    <table class="leaderboard-table">
      <thead>
        <tr>
          <th class="col-rank">#</th>
          <th>Product</th>
          <th class="col-score">Score</th>
        </tr>
      </thead>
      <tbody>
        ${rowsHtml}
      </tbody>
    </table>
  `;
}

function renderLeaderboardError(message) {
  leaderboardContent.innerHTML = `
    <div class="leaderboard-error">
      ⚠️ ${escapeHtml(message)}
    </div>
  `;
}

function renderLeaderboardLoading() {
  leaderboardContent.innerHTML = `
    <div class="leaderboard-loading">
      <span class="spinner spinner-dark"></span>
      Loading leaderboard…
    </div>
  `;
}

// ---- Load leaderboard ----
async function loadLeaderboard(silent = false) {
  if (!silent) {
    renderLeaderboardLoading();
  }
  try {
    const data = await fetchLeaderboard(10);
    renderLeaderboard(data);
  } catch (err) {
    if (!silent) {
      renderLeaderboardError(err.message || "Failed to load leaderboard.");
    }
  }
}

// ============================================================
//  Polling
// ============================================================

const POLL_INTERVAL = 30_000;
let pollingTimerId = null;

function startPolling() {
  stopPolling();
  pollingTimerId = setInterval(() => {
    loadLeaderboard(true);
  }, POLL_INTERVAL);
}

function stopPolling() {
  if (pollingTimerId !== null) {
    clearInterval(pollingTimerId);
    pollingTimerId = null;
  }
}

// ---- Refresh button ----
leaderboardRefreshBtn.addEventListener("click", () => {
  loadLeaderboard();
  startPolling();
});

// ---- Clean up on page unload ----
window.addEventListener("beforeunload", stopPolling);

// ---- Initial load and start polling ----
loadLeaderboard();
startPolling();

console.log("Review Analyzer loaded ✓");
