import {
  exportState,
  exportSQLiteDump,
  getDatabaseSettings,
  importState,
  saveDatabaseSettings
} from "./storage.js";

const databaseForm = document.querySelector("#databaseForm");
const databaseNameInput = document.querySelector("#databaseNameInput");
const databaseLoginInput = document.querySelector("#databaseLoginInput");
const databasePasswordInput = document.querySelector("#databasePasswordInput");
const exportButton = document.querySelector("#exportButton");
const sqliteDownloadButton = document.querySelector("#sqliteDownloadButton");
const exportOutput = document.querySelector("#exportOutput");
const importInput = document.querySelector("#importInput");
const importButton = document.querySelector("#importButton");
const statusMessage = document.querySelector("#statusMessage");

function showStatus(message) {
  statusMessage.textContent = message;
  statusMessage.classList.remove("hidden");
  window.clearTimeout(showStatus.timeoutId);
  showStatus.timeoutId = window.setTimeout(() => {
    statusMessage.classList.add("hidden");
  }, 2400);
}

function downloadTextFile(filename, contents) {
  const blob = new Blob([contents], { type: "application/sqlite3" });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

async function populateDatabaseSettings() {
  const settings = await getDatabaseSettings();
  databaseNameInput.value = settings.databaseName || "";
  databaseLoginInput.value = settings.login || "";
  databasePasswordInput.value = settings.password || "";
}

databaseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await saveDatabaseSettings(
    databaseNameInput.value,
    databaseLoginInput.value,
    databasePasswordInput.value
  );
  showStatus("Database settings saved locally.");
});

exportButton.addEventListener("click", async () => {
  const snapshot = await exportState();
  exportOutput.value = JSON.stringify(snapshot, null, 2);
  await navigator.clipboard.writeText(exportOutput.value);
  showStatus("Snapshot copied to clipboard.");
});

sqliteDownloadButton.addEventListener("click", async () => {
  const sqlDump = await exportSQLiteDump();
  exportOutput.value = sqlDump;
  downloadTextFile("novel_knowledge_export.sqlite.sql", sqlDump);
  showStatus("SQLite export downloaded.");
});

importButton.addEventListener("click", async () => {
  try {
    const parsed = JSON.parse(importInput.value);
    await importState(parsed);
    showStatus("Snapshot imported.");
  } catch (error) {
    showStatus(`Import failed: ${error.message}`);
  }
});

populateDatabaseSettings();
