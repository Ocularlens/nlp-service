/* ============================================================
 * Review Analyzer — Review Page ESM Module
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

  const moodClass = mood.toLowerCase();

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

      <div class="result-mood-row">
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
  } catch (err) {
    showToast(err.message || "An unexpected error occurred.");
    autoHideToast();
  } finally {
    setLoading(false);
  }
});

// ---- Reset result when form changes ----
function onFormChange() {
  resultSection.classList.remove("visible");
}
textInput.addEventListener("input", onFormChange);
productInput.addEventListener("input", onFormChange);

console.log("Review Analyzer loaded ✓");
