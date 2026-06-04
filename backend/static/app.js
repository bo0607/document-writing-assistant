const state = {
  task: null,
  busy: false,
};

const $ = (id) => document.getElementById(id);

const elements = {
  serviceState: $("serviceState"),
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
  outlineContent: $("outlineContent"),
  draftEditor: $("draftEditor"),
  saveDraftBtn: $("saveDraftBtn"),
  summaryBtn: $("summaryBtn"),
  revisionTypeSelect: $("revisionTypeSelect"),
  revisionInstruction: $("revisionInstruction"),
  reviseBtn: $("reviseBtn"),
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
  elements.reviseBtn.disabled = isBusy || !hasDraft;
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
    requirement.style,
  ]
    .filter(Boolean)
    .join(" / ") || "提纲和正文会显示在这里";

  renderOutline(outline);
  elements.draftEditor.value = draft.content || "";
  elements.draftEditor.disabled = !draft.content;
  elements.summaryContent.textContent = task.summary || "暂无摘要";
  elements.summaryContent.classList.toggle("empty-state", !task.summary);
  setBusy(false);
}

function renderOutline(outline) {
  if (!outline || !outline.sections) {
    elements.outlineContent.textContent = "暂无提纲";
    elements.outlineContent.classList.add("empty-state");
    return;
  }

  const article = document.createElement("article");
  const thesis = document.createElement("p");
  thesis.textContent = outline.thesis || "";
  article.appendChild(thesis);

  outline.sections.forEach((section) => {
    const block = document.createElement("section");
    const heading = document.createElement("h4");
    heading.textContent = section.heading || "段落";
    const list = document.createElement("ul");
    (section.points || []).forEach((point) => {
      const item = document.createElement("li");
      item.textContent = point;
      list.appendChild(item);
    });
    block.appendChild(heading);
    block.appendChild(list);
    article.appendChild(block);
  });

  elements.outlineContent.replaceChildren(article);
  elements.outlineContent.classList.remove("empty-state");
}

function clearWorkspace() {
  state.task = null;
  elements.taskBadge.textContent = "未创建";
  elements.versionBadge.textContent = "v0";
  elements.documentTitle.textContent = "等待生成";
  elements.documentMeta.textContent = "提纲和正文会显示在这里";
  elements.outlineContent.textContent = "暂无提纲";
  elements.outlineContent.classList.add("empty-state");
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

async function reviseDraft() {
  if (!state.task) return;
  await saveDraft();
  setBusy(true, "正在修订文本");
  try {
    const task = await api("/api/text/revise", {
      method: "POST",
      body: JSON.stringify({
        taskId: state.task.taskId,
        revisionType: elements.revisionTypeSelect.value,
        instruction: elements.revisionInstruction.value.trim(),
      }),
    });
    renderTask(task);
    showMessage("文本已修订");
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

function bindEvents() {
  elements.generateBtn.addEventListener("click", generateDocument);
  elements.saveDraftBtn.addEventListener("click", saveDraft);
  elements.reviseBtn.addEventListener("click", reviseDraft);
  elements.summaryBtn.addEventListener("click", summarizeDraft);
  elements.exportDocxBtn.addEventListener("click", () => exportDocument("docx"));
  elements.exportTxtBtn.addEventListener("click", () => exportDocument("txt"));
  elements.refreshTasksBtn.addEventListener("click", loadTasks);
  elements.newTaskBtn.addEventListener("click", clearWorkspace);
}

bindEvents();
checkHealth();
loadTasks();
