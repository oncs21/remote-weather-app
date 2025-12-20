document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("imageInput");
  const drop = document.getElementById("dropZone");
  const browseBtn = document.getElementById("browseBtn");
  const chips = document.getElementById("fileChips");
  const count = document.getElementById("fileCount");

  const form = document.getElementById("analysisForm");
  const grid = document.getElementById("resultGrid");
  const empty = document.getElementById("emptyState");

  const status = document.getElementById("statusPill");
  const statusText = status?.querySelector(".status-text");

  const goodCount = document.getElementById("goodCount");
  const badCount = document.getElementById("badCount");
  const avgCloud = document.getElementById("avgCloud");
  const modelName = document.getElementById("modelName");
  const modelSelect = document.getElementById("modelSelect");

  const threshold = document.getElementById("threshold");
  const thresholdVal = document.getElementById("thresholdVal");

  const exportBtn = document.getElementById("exportBtn");
  const clearResultsBtn = document.getElementById("clearResultsBtn");
  const resetBtn = document.getElementById("resetBtn");
  const runBtn = document.getElementById("runBtn");

  let files = [];
  let lastResults = [];

  const getCsrfToken = () => {
    const el = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : "";
  };

  const syncInputFiles = () => {
    const dt = new DataTransfer();
    files.forEach(f => dt.items.add(f));
    input.files = dt.files;
  };

  const setStatus = (state, text) => {
    if (!status) return;
    status.dataset.state = state;
    if (statusText) statusText.textContent = text;
  };

  const fmtModel = () =>
    modelSelect
      ? (modelSelect.options[modelSelect.selectedIndex]?.textContent?.trim() || modelSelect.value)
      : "—";

  const setThresholdLabel = () => {
    if (!threshold || !thresholdVal) return;
    thresholdVal.textContent = `${threshold.value}%`;
  };

  const renderChips = () => {
    chips.innerHTML = "";
    files.forEach((f, idx) => {
      const chip = document.createElement("div");
      chip.className = "chip";

      const name = document.createElement("span");
      name.textContent = f.name;

      const x = document.createElement("button");
      x.type = "button";
      x.setAttribute("aria-label", "Remove");
      x.textContent = "×";
      x.addEventListener("click", () => {
        files = files.filter((_, i) => i !== idx);
        syncInputFiles();
        renderChips();
      });

      chip.appendChild(name);
      chip.appendChild(x);
      chips.appendChild(chip);
    });

    count.textContent = String(files.length);
  };

  const takeFiles = (incoming) => {
    const arr = [...incoming].filter(f => f.type && f.type.startsWith("image/")).slice(0, 50);
    files = arr;
    syncInputFiles();
    renderChips();
  };

  const resetUI = () => {
    grid.innerHTML = "";
    empty.style.display = "";
    goodCount.textContent = "0";
    badCount.textContent = "0";
    avgCloud.textContent = "—";
    modelName.textContent = "—";
    lastResults = [];
    setStatus("ready", "Ready");
    if (runBtn) runBtn.disabled = false;
  };

  const labelToUi = (label) => {
    if (typeof label === "string") {
      const l = label.toLowerCase();
      if (l.includes("good")) return { key: "good", text: "Good" };
      if (l.includes("bad")) return { key: "bad", text: "Bad" };
      return { key: "mid", text: label };
    }

    const n = Number(label);
    const isGood = n === 0;
    const isBad = n === 1;
    if (isGood) return { key: "good", text: "Good" };
    if (isBad) return { key: "bad", text: "Bad" };
    return { key: "mid", text: "Review" };
  };

  const renderServerResults = (labels) => {
    const n = Math.min(files.length, Array.isArray(labels) ? labels.length : 0);

    let good = 0;
    let bad = 0;

    grid.innerHTML = "";
    lastResults = [];

    for (let i = 0; i < n; i++) {
      const f = files[i];
      const ui = labelToUi(labels[i]);

      if (ui.key === "good") good++;
      if (ui.key === "bad") bad++;

      const card = document.createElement("div");
      card.className = `result ${ui.key === "good" ? "is-good" : ui.key === "bad" ? "is-bad" : "is-mid"}`;

      const media = document.createElement("div");
      media.className = "media";

      const img = document.createElement("img");
      img.src = URL.createObjectURL(f);
      img.alt = f.name;

      const ray = document.createElement("div");
      ray.className = "ray";

      media.appendChild(img);
      media.appendChild(ray);

      const meta = document.createElement("div");
      meta.className = "result-meta";

      const badge = document.createElement("span");
      badge.className = `badge ${ui.key === "good" ? "good" : ui.key === "bad" ? "bad" : "mid"}`;
      badge.textContent = ui.text;

      const metric = document.createElement("div");
      metric.className = "metric";
      metric.textContent = f.name.length > 22 ? `${f.name.slice(0, 19)}…` : f.name;

      meta.appendChild(badge);
      meta.appendChild(metric);

      card.appendChild(media);
      card.appendChild(meta);
      grid.appendChild(card);

      lastResults.push({ name: f.name, label: ui.key, raw: labels[i] });
    }

    goodCount.textContent = String(good);
    badCount.textContent = String(bad);
    avgCloud.textContent = "—";
    modelName.textContent = fmtModel();

    empty.style.display = n ? "none" : "";
  };

  const postToServer = async () => {
    const fd = new FormData();

    fd.append("model-type", modelSelect?.value ?? "");
    if (threshold) fd.append("threshold", threshold.value);
    files.forEach(f => fd.append("images", f));

    const csrf = getCsrfToken();

    const resp = await fetch("/analysis", {
      method: "POST",
      headers: { "X-CSRFToken": csrf },
      body: fd
    });

    const contentType = resp.headers.get("content-type") || "";

    if (!resp.ok) {
      const text = contentType.includes("application/json")
        ? JSON.stringify(await resp.json())
        : await resp.text();
      throw new Error(text || `Request failed: ${resp.status}`);
    }

    if (!contentType.includes("application/json")) {
      throw new Error("Expected JSON response from server.");
    }

    return await resp.json();
  };

  if (browseBtn) browseBtn.addEventListener("click", () => input.click());

  if (drop) {
    drop.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") input.click();
    });

    ["dragenter", "dragover"].forEach(evt =>
      drop.addEventListener(evt, e => {
        e.preventDefault();
        drop.classList.add("drag");
      })
    );

    ["dragleave", "drop"].forEach(evt =>
      drop.addEventListener(evt, e => {
        e.preventDefault();
        drop.classList.remove("drag");
      })
    );

    drop.addEventListener("drop", e => {
      takeFiles(e.dataTransfer.files);
    });
  }

  input.addEventListener("change", () => takeFiles(input.files));

  if (threshold) threshold.addEventListener("input", setThresholdLabel);

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      form.reset();
    });
  }

  if (clearResultsBtn) {
    clearResultsBtn.addEventListener("click", () => {
      grid.innerHTML = "";
      empty.style.display = "";
      goodCount.textContent = "0";
      badCount.textContent = "0";
      avgCloud.textContent = "—";
      modelName.textContent = fmtModel();
      lastResults = [];
      setStatus("ready", "Ready");
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      if (!lastResults.length) return;

      const payload = {
        model: fmtModel(),
        threshold: Number(threshold?.value ?? 50),
        total: lastResults.length,
        good: Number(goodCount.textContent || 0),
        bad: Number(badCount.textContent || 0),
        avg_cloud: avgCloud.textContent,
        results: lastResults
      };

      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "analysis_results.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }

  form.addEventListener("reset", () => {
    files = [];
    syncInputFiles();
    renderChips();
    resetUI();
    setThresholdLabel();
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!files.length) return;

    setStatus("processing", "Processing…");
    empty.style.display = "none";
    grid.innerHTML = "";
    goodCount.textContent = "—";
    badCount.textContent = "—";
    avgCloud.textContent = "—";
    modelName.textContent = fmtModel();
    if (runBtn) runBtn.disabled = true;

    try {
      const data = await postToServer();
      renderServerResults(data.labels || []);
      setStatus("done", "Completed");
    } catch (err) {
      setStatus("error", "Error");
      grid.innerHTML = `<div class="empty"><div class="empty-title">Server error</div><div class="empty-sub">${String(err.message || err)}</div></div>`;
      goodCount.textContent = "0";
      badCount.textContent = "0";
      avgCloud.textContent = "—";
      empty.style.display = "none";
    } finally {
      if (runBtn) runBtn.disabled = false;
    }
  });

  setThresholdLabel();
  resetUI();
});
