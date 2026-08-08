const form = document.getElementById("complaint-form");
const descField = document.getElementById("description");
const charCount = document.getElementById("char-count");
const submitBtn = document.getElementById("submit-btn");
const formError = document.getElementById("form-error");
const resultPanel = document.getElementById("result-panel");

descField.addEventListener("input", () => {
  charCount.textContent = descField.value.length;
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  formError.textContent = "";

  const description = descField.value.trim();
  const location = document.getElementById("location").value.trim();
  const citizen_name = document.getElementById("citizen_name").value.trim();
  const citizen_phone = document.getElementById("citizen_phone").value.trim();
  const image_flag = document.getElementById("image_flag").checked;

  if (!description || !location || !citizen_name || !citizen_phone) {
    formError.textContent = "Please fill in your name, phone number, description and location.";
    return;
  }

  submitBtn.disabled = true;
  submitBtn.querySelector("span").textContent = "Analyzing…";

  try {
    const data = await apiRequest("/api/complaints", {
      method: "POST",
      body: JSON.stringify({ description, location, citizen_name, citizen_phone, image_flag }),
    });
    renderResult(data.complaint);
    form.reset();
    charCount.textContent = "0";
  } catch (err) {
    formError.textContent = err.message || "Something went wrong. Please try again.";
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector("span").textContent = "Submit & Analyze";
  }
});

function renderResult(complaint) {
  const ai = complaint.ai_output || {};
  document.getElementById("res-id").textContent = complaint.complaint_id;

  const chip = document.getElementById("res-priority");
  chip.textContent = complaint.priority;
  chip.className = "priority-chip " + priorityClass(complaint.priority);

  document.getElementById("res-category").textContent = complaint.category;
  document.getElementById("res-dept").textContent = complaint.assigned_department;
  document.getElementById("res-summary").textContent = ai.summary || "—";
  document.getElementById("res-confidence").textContent =
    ai.confidence !== undefined ? Math.round(ai.confidence * 100) + "%" : "—";
  document.getElementById("res-explanation").textContent = ai.explanation || "—";

  document.getElementById("ticket-card").style.borderLeftColor =
    { Critical: "#D63447", High: "#F7C877", Medium: "#F0A202", Low: "#3A7D44" }[complaint.priority] || "#F0A202";

  resultPanel.hidden = false;
  resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
