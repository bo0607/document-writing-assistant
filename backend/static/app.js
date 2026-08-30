const state = {
  task: null,
  busy: false,
  modelConfig: null,
  installPrompt: null,
};

const $ = (id) => document.getElementById(id);

const elements = {
  serviceState: $("serviceState"),
  installAppBtn: $("installAppBtn"),
  modelSettingsBtn: $("modelSettingsBtn"),
  modelDialog: $("modelDialog"),
  modelConfigForm: $("modelConfigForm"),
  closeModelDialogBtn: $("closeModelDialogBtn"),
  modelConfigState: $("modelConfigState"),
  modelBaseUrlInput: $("modelBaseUrlInput"),
  modelNameInput: $("modelNameInput"),
  modelApiKeyInput: $("modelApiKeyInput"),
  saveModelBtn: $("saveModelBtn"),
  testModelBtn: $("testModelBtn"),
  localModeBtn: $("localModeBtn"),
  taskBadge: $("taskBadge"),
  versionBadge: $("versionBadge"),
  topicInput: $("topicInput"),
  genreSelect: $("genreSelect"),
  wordCountInput: $("wordCountInput"),
  styleSelect: $("styleSelect"),
  extraInput: $("extraInput"),
  generateBtn: $("generateBtn"),
  refreshTasksBtn: $("refreshTasksBtn"),
  newTaskBtn: $("newTaskBtn"),
  taskList: $("taskList"),
  documentTitle: $("documentTitle"),
  documentMeta: $("documentMeta"),
  draftEditor: $("draftEditor"),
  saveDraftBtn: $("saveDraftBtn"),
  summaryBtn: $("summaryBtn"),
  exportDocxBtn: $("exportDocxBtn"),
  exportTxtBtn: $("exportTxtBtn"),
  summaryContent: $("summaryContent"),
  messageArea: $("messageArea"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || `请求失败：${response.status}`);
  }
  return payload.data ?? payload;
}

function setBusy(isBusy, message = "") {
  state.busy = isBusy;
  elements.generateBtn.disabled = isBusy;
  const hasDraft = Boolean(state.task?.draft?.content);
  elements.saveDraftBtn.disabled = isBusy || !hasDraft;
  elements.summaryBtn.disabled = isBusy || !hasDraft;
  elements.exportDocxBtn.disabled = isBusy || !hasDraft;
  elements.exportTxtBtn.disabled = isBusy || !hasDraft;
  if (message) {
    showMessage(message);
  }
}

function showMessage(message, isError = false) {
  elements.messageArea.textContent = message;
  elements.messageArea.classList.toggle("error", isError);
}

function writingPayload() {
  return {
    topic: elements.topicInput.value.trim(),
    genre: elements.genreSelect.value,
    wordCount: Number(elements.wordCountInput.value || 800),
    style: elements.styleSelect.value,
    extraInstruction: elements.extraInput.value.trim(),
  };
}

function renderTask(task) {
  state.task = task;
  const requirement = task.requirement || {};
  const outline = task.outline || {};
  const draft = task.draft || {};
  const title = outline.title || requirement.topic || "等待生成";
  const status = task.status || "未创建";

  elements.taskBadge.textContent = status;
  elements.versionBadge.textContent = `v${draft.version || 0}`;
  elements.documentTitle.textContent = title;
  elements.documentMeta.textContent = [
    requirement.genre,
    requirement.wordCount ? `${requirement.wordCount}字` : "",
    draft.wordCount ? `实际约${draft.wordCount}字` : "",
    requirement.style,
  ]
    .filter(Boolean)
    .join(" / ") || "提纲和正文会显示在这里";

  elements.draftEditor.value = draft.content || "";
  elements.draftEditor.disabled = !draft.content;
  elements.summaryContent.textContent = task.summary || "暂无摘要";
  elements.summaryContent.classList.toggle("empty-state", !task.summary);
  setBusy(false);
}

function clearWorkspace() {
  state.task = null;
  elements.taskBadge.textContent = "未创建";
  elements.versionBadge.textContent = "v0";
  elements.documentTitle.textContent = "等待生成";
  elements.documentMeta.textContent = "生成的正文会显示在这里";
  elements.draftEditor.value = "";
  elements.draftEditor.disabled = true;
  elements.summaryContent.textContent = "暂无摘要";
  elements.summaryContent.classList.add("empty-state");
  setBusy(false);
  showMessage("");
}

async function generateDocument() {
  const payload = writingPayload();
  if (!payload.topic) {
    showMessage("请填写主题", true);
    return;
  }
  setBusy(true, "正在生成文档");
  try {
    const task = await api("/api/task/run-full", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderTask(task);
    showMessage("文档已生成");
    loadTasks();
  } catch (error) {
    setBusy(false);
    showMessage(error.message, true);
  }
}

async function saveDraft() {
  if (!state.task) return;
  setBusy(true, "正在保存正文");
  try {
    const task = await api("/api/draft/update", {
      method: "POST",
      body: JSON.stringify({
        taskId: state.task.taskId,
        content: elements.draftEditor.value,
      }),
    });
    renderTask(task);
    showMessage("正文已保存");
  } catch (error) {
    setBusy(false);
    showMessage(error.message, true);
  }
}

async function summarizeDraft() {
  if (!state.task) return;
  await saveDraft();
  setBusy(true, "正在生成摘要");
  try {
    const task = await api("/api/text/summary", {
      method: "POST",
      body: JSON.stringify({ taskId: state.task.taskId }),
    });
    renderTask(task);
    showMessage("摘要已生成");
  } catch (error) {
    setBusy(false);
    showMessage(error.message, true);
  }
}

async function exportDocument(format) {
  if (!state.task) return;
  await saveDraft();
  setBusy(true, "正在导出文档");
  try {
    const result = await api("/api/document/export", {
      method: "POST",
      body: JSON.stringify({
        taskId: state.task.taskId,
        format,
      }),
    });
    renderTask(result.task);
    const fileName = result.file.fileName;
    const link = document.createElement("a");
    link.href = `/exports/${encodeURIComponent(fileName)}`;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    showMessage("文档已导出");
  } catch (error) {
    setBusy(false);
    showMessage(error.message, true);
  }
}

async function loadTasks() {
  try {
    const tasks = await api("/api/tasks");
    if (!tasks.length) {
      elements.taskList.textContent = "暂无任务";
      return;
    }
    const fragment = document.createDocumentFragment();
    tasks.slice(0, 6).forEach((task) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "task-item";
      button.innerHTML = `<strong></strong><span></span>`;
      button.querySelector("strong").textContent = task.topic || task.taskId;
      button.querySelector("span").textContent = `${task.status || ""} ${task.updatedAt || ""}`.trim();
      button.addEventListener("click", () => loadTaskDetail(task.taskId));
      fragment.appendChild(button);
    });
    elements.taskList.replaceChildren(fragment);
  } catch (error) {
    elements.taskList.textContent = "任务加载失败";
  }
}

async function loadTaskDetail(taskId) {
  if (!taskId) return;
  setBusy(true, "正在载入任务");
  try {
    const task = await api(`/api/task/detail?taskId=${encodeURIComponent(taskId)}`);
    renderTask(task);
    showMessage("任务已载入");
  } catch (error) {
    setBusy(false);
    showMessage(error.message, true);
  }
}

async function checkHealth() {
  try {
    const health = await api("/api/health");
    elements.serviceState.textContent = health.modelRemoteEnabled
      ? "后端已连接 / 远程模型已配置"
      : "后端已连接 / 本地演示模式";
  } catch (error) {
    elements.serviceState.textContent = "后端未连接";
  }
}

function setupInstallableApp() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    state.installPrompt = event;
    elements.installAppBtn.hidden = false;
  });

  window.addEventListener("appinstalled", () => {
    state.installPrompt = null;
    elements.installAppBtn.hidden = true;
    showMessage("应用已安装");
  });
}

async function installApp() {
  if (!state.installPrompt) {
    showMessage("请在浏览器菜单中选择“安装应用”", true);
    return;
  }
  state.installPrompt.prompt();
  await state.installPrompt.userChoice;
  state.installPrompt = null;
  elements.installAppBtn.hidden = true;
}

function renderModelConfig(config) {
  state.modelConfig = config;
  elements.modelBaseUrlInput.value = config.baseUrl || "";
  elements.modelNameInput.value = config.model || "";
  elements.modelApiKeyInput.value = "";
  const modeText = config.remoteEnabled
    ? "远程模型已启用"
    : config.mode === "local"
      ? "本地演示模式"
      : "远程模型未配置";
  elements.modelConfigState.textContent = config.apiKeyConfigured
    ? `${modeText} / API Key 已保存`
    : modeText;
}

function setModelBusy(isBusy, text = "") {
  elements.saveModelBtn.disabled = isBusy;
  elements.testModelBtn.disabled = isBusy;
  elements.localModeBtn.disabled = isBusy;
  if (text) {
    elements.modelConfigState.textContent = text;
  }
}

async function loadModelConfig() {
  const config = await api("/api/model/config");
  renderModelConfig(config);
  return config;
}

async function openModelDialog() {
  try {
    await loadModelConfig();
    elements.modelDialog.showModal();
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function saveModelConfig(event) {
  event.preventDefault();
  setModelBusy(true, "正在保存模型配置");
  try {
    const config = await api("/api/model/config", {
      method: "POST",
      body: JSON.stringify({
        baseUrl: elements.modelBaseUrlInput.value.trim(),
        model: elements.modelNameInput.value.trim(),
        apiKey: elements.modelApiKeyInput.value.trim(),
      }),
    });
    renderModelConfig(config);
    setModelBusy(false);
    await checkHealth();
    showMessage("远程模型已保存并启用");
  } catch (error) {
    setModelBusy(false);
    elements.modelConfigState.textContent = error.message;
  }
}

async function testModelConnection() {
  setModelBusy(true, "正在测试连接");
  try {
    const result = await api("/api/model/test", { method: "POST", body: "{}" });
    setModelBusy(false, `${result.message}：${result.preview || result.model}`);
  } catch (error) {
    setModelBusy(false, error.message);
  }
}

async function useLocalMode() {
  setModelBusy(true, "正在切换为本地模式");
  try {
    const config = await api("/api/model/local-mode", { method: "POST", body: "{}" });
    renderModelConfig(config);
    setModelBusy(false);
    await checkHealth();
    showMessage("已切换为本地演示模式");
  } catch (error) {
    setModelBusy(false);
    elements.modelConfigState.textContent = error.message;
  }
}

function bindEvents() {
  elements.installAppBtn.addEventListener("click", installApp);
  elements.modelSettingsBtn.addEventListener("click", openModelDialog);
  elements.closeModelDialogBtn.addEventListener("click", () => elements.modelDialog.close());
  elements.modelConfigForm.addEventListener("submit", saveModelConfig);
  elements.testModelBtn.addEventListener("click", testModelConnection);
  elements.localModeBtn.addEventListener("click", useLocalMode);
  elements.generateBtn.addEventListener("click", generateDocument);
  elements.saveDraftBtn.addEventListener("click", saveDraft);
  elements.summaryBtn.addEventListener("click", summarizeDraft);
  elements.exportDocxBtn.addEventListener("click", () => exportDocument("docx"));
  elements.exportTxtBtn.addEventListener("click", () => exportDocument("txt"));
  elements.refreshTasksBtn.addEventListener("click", loadTasks);
  elements.newTaskBtn.addEventListener("click", clearWorkspace);
}

bindEvents();
setupInstallableApp();
checkHealth();
loadTasks();
