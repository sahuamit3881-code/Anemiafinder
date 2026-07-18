// ============================================================
// Multimodal Anemia Screening Portal — frontend logic
// ============================================================

const REGIONS = ["eyelid", "nail", "tongue"];
const REGION_META = {
  eyelid: { emoji: "👁️", label: "Lower Eyelid", color: "#0EA5B7" },
  nail:   { emoji: "💅", label: "Fingernail Beds", color: "#FF6B6B" },
  tongue: { emoji: "👅", label: "Tongue", color: "#FFB627" },
};

const GAUGE_RADIUS = 70;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;

const selectedFiles = { eyelid: null, nail: null, tongue: null };

// ------------------------------------------------------------
// Tabs
// ------------------------------------------------------------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));

    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

// ------------------------------------------------------------
// Upload dropzones
// ------------------------------------------------------------
function setupDropzone(region) {
  const input = document.getElementById(`file-${region}`);
  const dropzone = input.closest(".dropzone");
  const emptyState = dropzone.querySelector(".dropzone-empty");
  const previewImg = dropzone.querySelector(".dropzone-preview");

  function handleFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    selectedFiles[region] = file;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewImg.hidden = false;
      emptyState.hidden = true;
      dropzone.classList.add("has-image");
    };
    reader.readAsDataURL(file);
    updateReadyCount();
  }

  input.addEventListener("change", (e) => handleFile(e.target.files[0]));

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) {
      input.files = e.dataTransfer.files;
      handleFile(file);
    }
  });
}

function updateReadyCount() {
  const n = REGIONS.filter((r) => selectedFiles[r]).length;
  const el = document.getElementById("ready-count");
  if (el) el.textContent = `(${n}/3 images ready)`;
}

REGIONS.forEach(setupDropzone);

// ------------------------------------------------------------
// Analyze
// ------------------------------------------------------------
function tierOf(score) {
  if (score < 30) return "low";
  if (score < 70) return "moderate";
  return "high";
}

function showAlert(tier, message) {
  const alertBox = document.getElementById("alert-box");
  const icons = { low: "✅", moderate: "⚠️", warning: "⚠️", high: "🚨", error: "⚠️" };
  alertBox.className = `alert-box tier-${tier}`;
  alertBox.innerHTML = `<span class="alert-icon">${icons[tier] || "ℹ️"}</span><span>${message}</span>`;
  alertBox.hidden = false;
}

function renderResults(data) {
  const resultsBox = document.getElementById("results");
  resultsBox.hidden = false;

  const risk = data.risk_score;
  const tier = tierOf(risk);

  const gaugeFill = document.getElementById("gauge-fill");
  gaugeFill.classList.remove("tier-low", "tier-moderate", "tier-high");
  gaugeFill.classList.add(`tier-${tier}`);

  const offset = GAUGE_CIRCUMFERENCE - (GAUGE_CIRCUMFERENCE * risk) / 100;
  // Force layout before transition so the fill animates from empty.
  gaugeFill.style.strokeDashoffset = GAUGE_CIRCUMFERENCE;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      gaugeFill.style.strokeDashoffset = offset;
    });
  });

  document.getElementById("gauge-value").textContent = `${risk.toFixed(1)}%`;
  document.getElementById("stat-modalities").textContent = `${Object.keys(data.modality_scores).length}/3`;
  document.getElementById("stat-confidence").textContent = `${data.confidence.toFixed(0)}%`;

  const messages = {
    low: `Low Risk (${risk.toFixed(1)}%) — markers appear within a typical range. Keep up a balanced, iron-rich diet and routine checkups.`,
    moderate: `Moderate Risk (${risk.toFixed(1)}%) — some markers suggest possible mild anemia. A confirmatory lab hemoglobin test is recommended.`,
    high: `High Risk (${risk.toFixed(1)}%) — markers strongly suggest possible anemia. Please consult a healthcare professional for a confirmatory blood test.`,
  };
  showAlert(tier, messages[tier]);

  const breakdown = document.getElementById("breakdown");
  breakdown.innerHTML = "";
  REGIONS.forEach((r) => {
    if (!(r in data.modality_scores)) return;
    const meta = REGION_META[r];
    const score = data.modality_scores[r];
    const row = document.createElement("div");
    row.className = "breakdown-row";
    row.innerHTML = `
      <div class="breakdown-label">${meta.emoji} ${meta.label}</div>
      <div class="breakdown-bar-track">
        <div class="breakdown-bar-fill" style="width:${score}%; background:${meta.color};"></div>
      </div>
      <div class="breakdown-score">${score.toFixed(1)}%</div>
    `;
    breakdown.appendChild(row);
  });

  resultsBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

document.getElementById("analyze-btn").addEventListener("click", async () => {
  const btn = document.getElementById("analyze-btn");
  const alertBox = document.getElementById("alert-box");
  const resultsBox = document.getElementById("results");

  alertBox.hidden = true;

  const formData = new FormData();
  REGIONS.forEach((r) => {
    if (selectedFiles[r]) formData.append(r, selectedFiles[r]);
  });

  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = "Analyzing…";

  try {
    const res = await fetch("/analyze", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      resultsBox.hidden = true;
      showAlert("warning", data.message || "Please upload at least one image.");
      return;
    }

    renderResults(data);
  } catch (err) {
    resultsBox.hidden = true;
    showAlert("error", "Something went wrong reaching the analysis engine. Please try again.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHTML;
  }
});
