/* ============================================================
 * Leaderboard Page — ESM Module
 * ============================================================ */

// ---- DOM refs ----
const leaderboardContent = document.getElementById("leaderboard-content");
const leaderboardRefreshBtn = document.getElementById("leaderboard-refresh-btn");
const toast = document.getElementById("toast");
const toastMsg = document.getElementById("toast-message");
const toastClose = document.getElementById("toast-close");
const tooltip = document.getElementById("tooltip");
const tooltipContent = document.getElementById("tooltip-content");

// ---- Toast ----
function showToast(message) {
  toastMsg.textContent = message;
  toast.classList.add("visible");
}

function hideToast() {
  toast.classList.remove("visible");
}

toastClose.addEventListener("click", hideToast);

// ---- Escape HTML ----
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

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
        <tr data-product="${escapeHtml(entry.product_name)}">
          <td class="col-rank">${getMedal(i + 1)}</td>
          <td class="col-product">${escapeHtml(entry.product_name)}</td>
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
//  Tooltip — shows latest review on hover/tap
// ============================================================

let tooltipTimeout = null;
let activeTooltipProduct = null;

async function fetchLatestReview(productName) {
  const response = await fetch(
    `/api/v1/products/${encodeURIComponent(productName)}/reviews/latest`
  );
  if (!response.ok) {
    return null;
  }
  return response.json();
}

function showTooltip(target, data) {
  const review = data.review;
  if (!review) {
    tooltipContent.innerHTML = `
      <div class="tooltip-header">${escapeHtml(data.product_name)}</div>
      <div class="tooltip-body tooltip-empty">No reviews yet</div>
    `;
  } else {
    const moodEmoji = review.mood === "positive" ? "😊" :
                      review.mood === "negative" ? "😞" :
                      review.mood === "mixed" ? "😐" : "—";
    tooltipContent.innerHTML = `
      <div class="tooltip-header">${escapeHtml(data.product_name)}</div>
      <div class="tooltip-body">
        <p class="tooltip-review-text">"${escapeHtml(review.review_text)}"</p>
        <span class="tooltip-review-mood">${moodEmoji} ${escapeHtml(review.mood)}</span>
      </div>
    `;
  }

  // Position tooltip near the target row
  const rect = target.getBoundingClientRect();
  const scrollY = window.scrollY;
  const scrollX = window.scrollX;

  tooltip.style.left = `${rect.left + scrollX + rect.width / 2}px`;
  tooltip.style.top = `${rect.top + scrollY - 8}px`;

  tooltip.classList.add("visible");
  tooltip.setAttribute("aria-hidden", "false");
}

function hideTooltip() {
  tooltip.classList.remove("visible");
  tooltip.setAttribute("aria-hidden", "true");
  activeTooltipProduct = null;
}

// Event delegation on the leaderboard table body
leaderboardContent.addEventListener("mouseover", async (e) => {
  const row = e.target.closest("tr[data-product]");
  if (!row) return;

  const productName = row.dataset.product;
  if (activeTooltipProduct === productName) return;

  activeTooltipProduct = productName;

  // Debounce
  if (tooltipTimeout) clearTimeout(tooltipTimeout);
  tooltipTimeout = setTimeout(async () => {
    const data = await fetchLatestReview(productName);
    if (data && activeTooltipProduct === productName) {
      showTooltip(row, data);
    }
  }, 200);
});

leaderboardContent.addEventListener("mouseout", (e) => {
  const row = e.target.closest("tr[data-product]");
  if (!row) return;
  const related = e.relatedTarget;
  // Only hide if we've actually left the row
  if (related && row.contains(related)) return;
  if (tooltipTimeout) clearTimeout(tooltipTimeout);
  activeTooltipProduct = null;
  hideTooltip();
});

// Mobile: tap to toggle tooltip (only on touch devices)
if (window.matchMedia('(hover: none)').matches) {
  leaderboardContent.addEventListener("click", async (e) => {
    const row = e.target.closest("tr[data-product]");
    if (!row) {
      hideTooltip();
      return;
    }

    const productName = row.dataset.product;
    if (activeTooltipProduct === productName) {
      hideTooltip();
      return;
    }

    const data = await fetchLatestReview(productName);
    if (data) {
      showTooltip(row, data);
    }
  });
}

// Close tooltip on outside click (touch devices)
if (window.matchMedia('(hover: none)').matches) {
  document.addEventListener("click", (e) => {
    if (!e.target.closest("tr[data-product]") && !e.target.closest("#tooltip")) {
      hideTooltip();
    }
  });
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

console.log("Leaderboard loaded ✓");
