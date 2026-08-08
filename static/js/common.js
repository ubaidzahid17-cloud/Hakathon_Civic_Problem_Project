function priorityClass(priority) {
  const map = { Critical: "p-critical", High: "p-high", Medium: "p-medium", Low: "p-low" };
  return map[priority] || "p-medium";
}

function statusClass(status) {
  const map = {
    "Open": "s-open",
    "Assigned": "s-assigned",
    "In Progress": "s-in-progress",
    "Resolved": "s-resolved",
  };
  return map[status] || "s-open";
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}

async function apiRequest(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data;
  try {
    data = await res.json();
  } catch (e) {
    throw new Error("Server returned an invalid response.");
  }
  if (!res.ok || data.success === false) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}
