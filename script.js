// The dashboard reads leads from the existing CRM API.
// No records are created, edited, or deleted from this page.
const API_URL = "https://n8n-workshop-crm.onrender.com/leads";

const tableBody = document.getElementById("leadsTableBody");
const message = document.getElementById("message");
const refreshButton = document.getElementById("refreshButton");
const searchInput = document.getElementById("searchInput");
const totalCount = document.getElementById("totalCount");
const highPriorityCount = document.getElementById("highPriorityCount");
const standardCount = document.getElementById("standardCount");
const lastUpdated = document.getElementById("lastUpdated");

let allLeads = [];

function showMessage(text, isError = false) {
  message.textContent = text;
  message.className = isError ? "message visible error" : "message visible";
}

function hideMessage() {
  message.textContent = "";
  message.className = "message";
}

function makeCell(value, className = "") {
  const cell = document.createElement("td");
  if (className) cell.className = className;
  cell.textContent = value === null || value === undefined || value === ""
    ? "—"
    : String(value);
  return cell;
}

function formatBudget(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number)
    ? new Intl.NumberFormat("en-AU", {
        style: "currency",
        currency: "AUD",
        maximumFractionDigits: 2
      }).format(number)
    : String(value);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function renderLeads() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = allLeads.filter((lead) => {
    const name = String(lead.name || "").toLowerCase();
    const email = String(lead.email || "").toLowerCase();
    return name.includes(query) || email.includes(query);
  });

  tableBody.replaceChildren();

  for (const lead of filtered) {
    const row = document.createElement("tr");
    row.append(
      makeCell(lead.id),
      makeCell(lead.name, "name"),
      makeCell(lead.email),
      makeCell(lead.phone),
      makeCell(formatBudget(lead.budget_amount))
    );

    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    const statusValue = String(lead.status || "new");
    status.className = `status ${statusValue}`;
    status.textContent = statusValue;
    statusCell.append(status);
    row.append(statusCell);

    row.append(
      makeCell(lead.enquiry, "enquiry"),
      makeCell(formatDate(lead.created_at))
    );
    tableBody.append(row);
  }

  if (filtered.length === 0) {
    showMessage(query ? "No leads match your search." : "No leads found yet.");
  } else {
    hideMessage();
  }
}

function updateStats() {
  totalCount.textContent = allLeads.length;
  highPriorityCount.textContent = allLeads.filter(
    (lead) => lead.status === "high_priority"
  ).length;
  standardCount.textContent = allLeads.filter(
    (lead) => lead.status === "standard"
  ).length;
}

async function loadLeads() {
  refreshButton.disabled = true;
  refreshButton.innerHTML = "<span aria-hidden=\"true\">↻</span> Loading…";

  try {
    const response = await fetch(API_URL);
    if (!response.ok) {
      throw new Error(`CRM API returned HTTP ${response.status}`);
    }

    const data = await response.json();
    if (!Array.isArray(data)) {
      throw new Error("The CRM API response was not a list of leads.");
    }

    allLeads = data;
    updateStats();
    renderLeads();
    lastUpdated.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    showMessage(
      `Couldn't load leads. ${error.message}. Check that the CRM API is running and allows this dashboard's origin through CORS.`,
      true
    );
  } finally {
    refreshButton.disabled = false;
    refreshButton.innerHTML = "<span aria-hidden=\"true\">↻</span> Refresh";
  }
}

refreshButton.addEventListener("click", loadLeads);
searchInput.addEventListener("input", renderLeads);

// Initial load, then refresh automatically every 10 seconds.
loadLeads();
setInterval(loadLeads, 10000);
