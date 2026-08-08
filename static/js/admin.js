let categoryChart, priorityChart;
let metaCache = null;

async function loadMeta() {
  try {
    metaCache = await (await fetch("/api/meta")).json();
    const catSel = document.getElementById("filter-category");
    const prioSel = document.getElementById("filter-priority");
    const statusSel = document.getElementById("filter-status");
    metaCache.categories.forEach(c => catSel.append(new Option(c, c)));
    metaCache.priorities.forEach(p => prioSel.append(new Option(p, p)));
    metaCache.statuses.forEach(s => statusSel.append(new Option(s, s)));
  } catch (e) { /* non-fatal */ }
}

function buildQuery() {
  const params = new URLSearchParams();
  const search = document.getElementById("filter-search").value.trim();
  const category = document.getElementById("filter-category").value;
  const priority = document.getElementById("filter-priority").value;
  const status = document.getElementById("filter-status").value;
  const location = document.getElementById("filter-location").value.trim();
  if (search) params.set("search", search);
  if (category) params.set("category", category);
  if (priority) params.set("priority", priority);
  if (status) params.set("status", status);
  if (location) params.set("location", location);
  return params.toString();
}

async function loadComplaints() {
  const tbody = document.getElementById("complaint-tbody");
  tbody.innerHTML = `<tr><td colspan="11" class="empty-row">Loading complaints…</td></tr>`;
  try {
    const data = await apiRequest("/api/complaints?" + buildQuery());
    renderTable(data.complaints);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty-row">Could not load complaints: ${e.message}</td></tr>`;
  }
}

function renderTable(complaints) {
  const tbody = document.getElementById("complaint-tbody");
  if (!complaints.length) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty-row">No complaints match these filters.</td></tr>`;
    return;
  }
  tbody.innerHTML = complaints.map(c => `
    <tr>
      <td><span style="font-family:var(--font-mono);font-size:11.5px;color:var(--slate)">${c.complaint_id}</span></td>
      <td>${escapeHtml(c.citizen_name || "—")}</td>
      <td><span style="font-family:var(--font-mono);font-size:12px">${escapeHtml(c.citizen_phone || "—")}</span></td>
      <td class="desc-cell">${escapeHtml(c.description)}</td>
      <td>${c.category || "—"}</td>
      <td><span class="badge ${priorityClass(c.priority)}">${c.priority || "—"}</span></td>
      <td>${escapeHtml(c.location || "—")}</td>
      <td>${c.assigned_department || "—"}</td>
      <td>
        <select class="status-select" data-id="${c.complaint_id}">
          ${(metaCache?.statuses || ["Open","Assigned","In Progress","Resolved"]).map(s =>
            `<option value="${s}" ${s === c.status ? "selected" : ""}>${s}</option>`).join("")}
        </select>
      </td>
      <td>${formatDate(c.date)}</td>
      <td><span class="badge ${statusClass(c.status)}">${c.status}</span></td>
    </tr>
  `).join("");

  tbody.querySelectorAll(".status-select").forEach(sel => {
    sel.addEventListener("change", async (e) => {
      const id = e.target.dataset.id;
      const newStatus = e.target.value;
      try {
        await apiRequest(`/api/complaints/${id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: newStatus }),
        });
        loadComplaints();
        loadStats();
      } catch (err) {
        alert("Could not update status: " + err.message);
      }
    });
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

async function loadStats() {
  try {
    const data = await apiRequest("/api/statistics");
    const r = data.report;
    document.getElementById("stat-total").textContent = r.summary.total;
    document.getElementById("stat-open").textContent = r.summary.open;
    document.getElementById("stat-progress").textContent = r.summary.in_progress;
    document.getElementById("stat-resolved").textContent = r.summary.resolved;
    document.getElementById("stat-critical").textContent = r.summary.critical;
    document.getElementById("stat-rate").textContent = r.summary.resolution_rate + "%";

    renderChart("chart-category", r.category_distribution, "cat");
    renderChart("chart-priority", r.priority_distribution, "prio");
    renderResolutionStats(r.resolution_time);
  } catch (e) {
    console.error(e);
  }
}

function renderChart(canvasId, distribution, kind) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const labels = distribution.map(d => d.label);
  const counts = distribution.map(d => d.count);
  const colors = kind === "prio"
    ? labels.map(l => ({ Critical: "#D63447", High: "#F7C877", Medium: "#F0A202", Low: "#3A7D44" }[l] || "#55698A"))
    : ["#10233F","#55698A","#F0A202","#8A9AB5","#3A7D44","#D63447"];

  const existing = canvasId === "chart-category" ? categoryChart : priorityChart;
  if (existing) existing.destroy();

  const chart = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ data: counts, backgroundColor: colors, borderRadius: 3 }] },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { font: { family: "IBM Plex Mono", size: 10 } }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(16,35,63,0.08)" } },
      },
    },
  });

  if (canvasId === "chart-category") categoryChart = chart;
  else priorityChart = chart;
}

function renderResolutionStats(rt) {
  const grid = document.getElementById("stats-grid");
  if (!rt.count) {
    grid.innerHTML = `<p style="color:var(--slate);font-size:13px;grid-column:1/-1">No resolved complaints yet — statistics will populate once complaints are marked Resolved.</p>`;
    return;
  }
  const rows = [
    ["Mean", rt.mean], ["Median", rt.median], ["Mode", rt.mode ?? "—"],
    ["Min", rt.min], ["Max", rt.max], ["Range", rt.range],
    ["Variance", rt.variance], ["Std. dev", rt.std_dev],
    ["Q1", rt.q1], ["Q3", rt.q3], ["IQR", rt.iqr], ["Outliers", rt.outliers.length],
  ];
  grid.innerHTML = rows.map(([k, v]) => `
    <div><span class="sg-val">${v}</span><span class="sg-key">${k}</span></div>
  `).join("");
}

document.getElementById("refresh-btn").addEventListener("click", () => { loadComplaints(); loadStats(); });
document.getElementById("clear-filters").addEventListener("click", () => {
  document.getElementById("filter-search").value = "";
  document.getElementById("filter-category").value = "";
  document.getElementById("filter-priority").value = "";
  document.getElementById("filter-status").value = "";
  document.getElementById("filter-location").value = "";
  loadComplaints();
});
["filter-search","filter-category","filter-priority","filter-status","filter-location"].forEach(id => {
  document.getElementById(id).addEventListener("change", loadComplaints);
});
document.getElementById("filter-search").addEventListener("keyup", (e) => { if (e.key === "Enter") loadComplaints(); });

(async function init() {
  await loadMeta();
  await loadComplaints();
  await loadStats();
})();
