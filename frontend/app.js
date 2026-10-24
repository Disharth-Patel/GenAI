/**
 * Maharashtra OBC Education Voice AI Chatbot - Frontend Application Logic
 */

const API_BASE = (window.location.origin && window.location.origin !== "null" && !window.location.origin.startsWith("file:"))
  ? window.location.origin
  : "http://127.0.0.1:8000";

// State
let currentConversationId = null;
let authToken = localStorage.getItem("voice_chatbot_token") || null;
let currentUser = JSON.parse(localStorage.getItem("voice_chatbot_user") || "null");
let speechRecognition = null;
let isRecording = false;
let currentUtterance = null;
let activeSpeakerData = null; // { text, lang, btn, bubble, isPaused }

// DOM Elements
const sidebar = document.getElementById("sidebar");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const closeSidebarBtn = document.getElementById("closeSidebarBtn");
const newChatBtn = document.getElementById("newChatBtn");
const conversationsList = document.getElementById("conversationsList");
const languageSelect = document.getElementById("languageSelect");
const voiceAutoPlayToggle = document.getElementById("voiceAutoPlayToggle");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const themeIcon = document.getElementById("themeIcon");
const globalSpeakingBar = document.getElementById("globalSpeakingBar");
const speakingLangBadge = document.getElementById("speakingLangBadge");
const pauseResumeGlobalBtn = document.getElementById("pauseResumeGlobalBtn");
const stopSpeakingGlobalBtn = document.getElementById("stopSpeakingGlobalBtn");
const toastContainer = document.getElementById("toastContainer");
const messagesContainer = document.getElementById("messagesContainer");
const welcomeHero = document.getElementById("welcomeHero");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const recordingBar = document.getElementById("recordingBar");
const liveTranscript = document.getElementById("liveTranscript");
const stopRecordingBtn = document.getElementById("stopRecordingBtn");
const cancelRecordingBtn = document.getElementById("cancelRecordingBtn");

// Model & Runtime Elements
const modelRuntimeBadge = document.getElementById("modelRuntimeBadge");
const runtimeDot = document.getElementById("runtimeDot");
const runtimeLabel = document.getElementById("runtimeLabel");
const modelStatusModal = document.getElementById("modelStatusModal");
const closeModelStatusModalBtn = document.getElementById("closeModelStatusModalBtn");
const statusRuntimeVal = document.getElementById("statusRuntimeVal");
const statusActiveModelVal = document.getElementById("statusActiveModelVal");
const statusHealthVal = document.getElementById("statusHealthVal");
const hwRamVal = document.getElementById("hwRamVal");
const hwRamPct = document.getElementById("hwRamPct");
const hwCpuVal = document.getElementById("hwCpuVal");
const hwThreadsVal = document.getElementById("hwThreadsVal");
const installedModelsList = document.getElementById("installedModelsList");

// Auth Elements
const authTriggerBtn = document.getElementById("authTriggerBtn");
const authModal = document.getElementById("authModal");
const closeAuthModalBtn = document.getElementById("closeAuthModalBtn");
const authForm = document.getElementById("authForm");
const authTabLogin = document.getElementById("authTabLogin");
const authTabRegister = document.getElementById("authTabRegister");
const authModalTitle = document.getElementById("authModalTitle");
const authUsername = document.getElementById("authUsername");
const authEmail = document.getElementById("authEmail");
const emailGroup = document.getElementById("emailGroup");
const authPassword = document.getElementById("authPassword");
const authErrorMsg = document.getElementById("authErrorMsg");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const userNameDisplay = document.getElementById("userNameDisplay");
const userRoleDisplay = document.getElementById("userRoleDisplay");

// Admin Elements
const openAdminBtn = document.getElementById("openAdminBtn");
const adminModal = document.getElementById("adminModal");
const closeAdminModalBtn = document.getElementById("closeAdminModalBtn");
const kbSearchInput = document.getElementById("kbSearchInput");
const kbRecordTypeFilter = document.getElementById("kbRecordTypeFilter");
const kbRefreshBtn = document.getElementById("kbRefreshBtn");
const kbTableBody = document.getElementById("kbTableBody");
const addEntryForm = document.getElementById("addEntryForm");
const fileUploadInput = document.getElementById("fileUploadInput");
const uploadDropzone = document.getElementById("uploadDropzone");
const selectedFileName = document.getElementById("selectedFileName");
const startUploadBtn = document.getElementById("startUploadBtn");
const uploadProgressWrap = document.getElementById("uploadProgressWrap");
const uploadProgressBar = document.getElementById("uploadProgressBar");
const uploadStatusText = document.getElementById("uploadStatusText");
const reseedBtn = document.getElementById("reseedBtn");
const statTotalCount = document.getElementById("statTotalCount");

// LLM Evaluation Studio Elements
const openEvalBtn = document.getElementById("openEvalBtn");
const openEvalBtnTop = document.getElementById("openEvalBtnTop");
const evalModal = document.getElementById("evalModal");
const closeEvalModalBtn = document.getElementById("closeEvalModalBtn");
const runBenchmarkBtn = document.getElementById("runBenchmarkBtn");
const runSweepBtn = document.getElementById("runSweepBtn");
const runAblationBtn = document.getElementById("runAblationBtn");
const evalProgressWrap = document.getElementById("evalProgressWrap");
const evalProgressBar = document.getElementById("evalProgressBar");
const evalStatusText = document.getElementById("evalStatusText");
const evalLastRunLabel = document.getElementById("evalLastRunLabel");

let selectedFile = null;
let authMode = "login";
let activeEvalRun = null;
let currentEvaluatedResults = [];
let currentSelectedRating = 0;

// ============================================================================
// Toast Notification Utility
// ============================================================================
function showToast(message, type = "info", duration = 3500) {
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const iconMap = {
    info: "ℹ️",
    success: "✅",
    warning: "⚠️",
    error: "❌"
  };
  toast.innerHTML = `
    <span class="toast-icon">${iconMap[type] || "ℹ️"}</span>
    <div class="toast-content">${escapeHTML(message)}</div>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("toast-hide");
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

// ============================================================================
// Theme Management (Light / Dark)
// ============================================================================
function initTheme() {
  const savedTheme = localStorage.getItem("voice_chatbot_theme") || "dark";
  setTheme(savedTheme);
}

function setTheme(theme) {
  if (theme === "light") {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
    if (themeIcon) themeIcon.textContent = "🌙";
    localStorage.setItem("voice_chatbot_theme", "light");
  } else {
    document.body.classList.remove("light-theme");
    document.body.classList.add("dark-theme");
    if (themeIcon) themeIcon.textContent = "☀️";
    localStorage.setItem("voice_chatbot_theme", "dark");
  }
}

function toggleTheme() {
  const isLight = document.body.classList.contains("light-theme");
  setTheme(isLight ? "dark" : "light");
  showToast(`Switched to ${isLight ? "Dark" : "Light"} mode`, "info", 2000);
}

// ============================================================================
// Model & Runtime Probing
// ============================================================================
async function fetchModelRuntimeStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/llm/status`);
    if (!res.ok) return;
    const data = await res.json();
    const health = data.health || {};
    const hardware = data.hardware || {};

    if (modelRuntimeBadge) {
      modelRuntimeBadge.classList.remove("status-offline", "status-warning");
      if (health.available) {
        if (runtimeLabel) runtimeLabel.textContent = `🟢 ${health.active_model || 'Ollama Local'}`;
        modelRuntimeBadge.title = `Ollama Online: ${health.active_model} (100% Free Local Inference)`;
      } else if (health.status === "model_missing") {
        modelRuntimeBadge.classList.add("status-warning");
        if (runtimeLabel) runtimeLabel.textContent = `🟡 Model Not Pulled`;
        modelRuntimeBadge.title = health.instruction || "Ollama model missing";
      } else {
        modelRuntimeBadge.classList.add("status-offline");
        if (runtimeLabel) runtimeLabel.textContent = `🟡 Grounded RAG (Ollama Off)`;
        modelRuntimeBadge.title = "Ollama not running. Click to view setup guide.";
      }
    }

    if (statusRuntimeVal) statusRuntimeVal.textContent = data.provider === "ollama" ? "Ollama (Open-Weight)" : data.provider;
    if (statusActiveModelVal) statusActiveModelVal.textContent = data.active_model || "--";
    if (statusHealthVal) {
      statusHealthVal.textContent = health.available ? "Online / Ready" : (health.message || "Offline");
      statusHealthVal.style.color = health.available ? "#34d399" : "#fbbf24";
    }

    if (hwRamVal) hwRamVal.textContent = hardware.ram_used_mb ? `${hardware.ram_used_mb} / ${hardware.ram_total_mb} MB` : "--";
    if (hwRamPct) hwRamPct.textContent = hardware.ram_percent ? `${hardware.ram_percent}%` : "--%";
    if (hwCpuVal) hwCpuVal.textContent = hardware.cpu_percent !== undefined ? `${hardware.cpu_percent}%` : "--%";
    if (hwThreadsVal) hwThreadsVal.textContent = hardware.threads || "--";

    if (installedModelsList) {
      const models = health.installed_models || [];
      if (models.length > 0) {
        installedModelsList.innerHTML = models.map(m => `<span class="model-chip">${escapeHTML(m)}</span>`).join("");
      } else {
        installedModelsList.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted);">No models detected in Ollama tags.</span>`;
      }
    }
  } catch (e) {
    console.warn("Could not query LLM status:", e);
  }
}

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  updateUserUI();
  setupSpeechRecognition();
  loadConversations();
  setupEventListeners();
  checkServerHealth();
  fetchModelRuntimeStatus();
});

function setupEventListeners() {
  // Theme toggle
  themeToggleBtn?.addEventListener("click", toggleTheme);

  // Model Runtime Status modal
  modelRuntimeBadge?.addEventListener("click", () => {
    fetchModelRuntimeStatus();
    modelStatusModal?.classList.add("open");
  });
  closeModelStatusModalBtn?.addEventListener("click", () => {
    modelStatusModal?.classList.remove("open");
  });

  // Copy command buttons inside guide
  document.querySelectorAll(".copy-cmd-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cmd = btn.getAttribute("data-copy");
      if (cmd) {
        navigator.clipboard.writeText(cmd);
        btn.textContent = "Copied!";
        showToast(`Copied: ${cmd}`, "success", 2000);
        setTimeout(() => { btn.textContent = "Copy"; }, 2000);
      }
    });
  });

  // Global Audio Controls
  pauseResumeGlobalBtn?.addEventListener("click", togglePauseResumeGlobalSpeech);
  stopSpeakingGlobalBtn?.addEventListener("click", stopSpeaking);

  // Mobile sidebar toggle
  mobileMenuBtn?.addEventListener("click", () => sidebar.classList.add("open"));
  closeSidebarBtn?.addEventListener("click", () => sidebar.classList.remove("open"));

  // New Chat
  newChatBtn.addEventListener("click", startNewChat);

  // Chat Form submission
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  // Enter to send (Shift+Enter for newline)
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize chat textarea
  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
  });

  // Quick Prompts Chips
  document.querySelectorAll(".prompt-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      if (q) {
        chatInput.value = q;
        sendMessage();
      }
    });
  });

  // Microphone controls
  micBtn.addEventListener("click", toggleVoiceRecording);
  stopRecordingBtn.addEventListener("click", stopVoiceRecordingAndSend);
  cancelRecordingBtn.addEventListener("click", cancelVoiceRecording);

  // Auth Modal
  authTriggerBtn.addEventListener("click", openAuthModal);
  closeAuthModalBtn.addEventListener("click", () => authModal.classList.remove("open"));
  authTabLogin.addEventListener("click", () => setAuthMode("login"));
  authTabRegister.addEventListener("click", () => setAuthMode("register"));
  authForm.addEventListener("submit", handleAuthSubmit);

  // Admin Modal
  openAdminBtn.addEventListener("click", openAdminModal);
  closeAdminModalBtn.addEventListener("click", () => adminModal.classList.remove("open"));

  // Admin Modal Tabs
  document.querySelectorAll(".admin-modal-card .tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".admin-modal-card .tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".admin-modal-card .tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      const targetTab = document.getElementById(btn.getAttribute("data-tab"));
      if (targetTab) targetTab.classList.add("active");
      if (btn.getAttribute("data-tab") === "tabBrowse") loadKnowledgeEntries();
    });
  });

  kbRefreshBtn.addEventListener("click", loadKnowledgeEntries);
  kbSearchInput.addEventListener("input", debounce(loadKnowledgeEntries, 400));
  kbRecordTypeFilter.addEventListener("change", loadKnowledgeEntries);
  addEntryForm.addEventListener("submit", handleAddEntrySubmit);

  // File Upload
  fileUploadInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      selectedFile = e.target.files[0];
      selectedFileName.textContent = `${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
    }
  });

  // Drag and Drop
  uploadDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadDropzone.classList.add("dragover");
  });
  uploadDropzone.addEventListener("dragleave", () => uploadDropzone.classList.remove("dragover"));
  uploadDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadDropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      selectedFile = e.dataTransfer.files[0];
      selectedFileName.textContent = `${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
    }
  });

  startUploadBtn.addEventListener("click", handleDocumentUpload);
  reseedBtn.addEventListener("click", handleReseed);

  // LLM Evaluation Studio Events
  openEvalBtn?.addEventListener("click", openEvaluationModal);
  openEvalBtnTop?.addEventListener("click", openEvaluationModal);
  closeEvalModalBtn?.addEventListener("click", () => evalModal.classList.remove("open"));

  // Evaluation Studio Tabs
  document.querySelectorAll(".eval-modal-card .tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".eval-modal-card .tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".eval-modal-card .eval-tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      const targetTab = document.getElementById(btn.getAttribute("data-eval-tab"));
      if (targetTab) targetTab.classList.add("active");
      if (btn.getAttribute("data-eval-tab") === "tabEvalHistory") loadBenchmarkHistory();
    });
  });

  runBenchmarkBtn?.addEventListener("click", () => runLiveBenchmark());
  runSweepBtn?.addEventListener("click", () => runParameterSweep());
  runAblationBtn?.addEventListener("click", () => runRAGAblation());

  // Parameter Tuner Slider sync
  const paramTemp = document.getElementById("paramTemp");
  const valTemp = document.getElementById("valTemp");
  paramTemp?.addEventListener("input", (e) => valTemp.textContent = e.target.value);

  const paramTopP = document.getElementById("paramTopP");
  const valTopP = document.getElementById("valTopP");
  paramTopP?.addEventListener("input", (e) => valTopP.textContent = e.target.value);

  const paramMaxTokens = document.getElementById("paramMaxTokens");
  const valMaxTokens = document.getElementById("valMaxTokens");
  paramMaxTokens?.addEventListener("input", (e) => valMaxTokens.textContent = e.target.value);

  document.getElementById("paramTunerForm")?.addEventListener("submit", handleSingleParamTest);
  document.getElementById("resetParamBtn")?.addEventListener("click", resetParamDefaults);
  document.getElementById("evalTestCaseSelect")?.addEventListener("change", handleTestCaseSelect);
  document.getElementById("saveFeedbackBtn")?.addEventListener("click", handleSaveHumanFeedback);
  document.getElementById("refreshHistoryBtn")?.addEventListener("click", loadBenchmarkHistory);
  document.getElementById("historyFilterType")?.addEventListener("change", loadBenchmarkHistory);

  // Star Rating setup
  document.querySelectorAll("#starRatingGroup .star").forEach((star) => {
    star.addEventListener("click", () => {
      const val = parseInt(star.getAttribute("data-val") || "1", 10);
      setStarRating(val);
    });
  });
}

// ============================================================================
// Server Health Check
// ============================================================================
async function checkServerHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      if (statTotalCount) statTotalCount.textContent = data.indexed_knowledge_entries || "104";
    }
  } catch (err) {
    console.warn("Backend server connection check failed:", err);
  }
}

// ============================================================================
// Chat Messaging & RAG
// ============================================================================
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  // Clear input
  chatInput.value = "";
  chatInput.style.height = "auto";
  chatInput.disabled = true;
  sendBtn.disabled = true;

  // Hide hero if visible
  if (welcomeHero) welcomeHero.style.display = "none";

  // Append User message to UI
  appendMessage("user", text);

  // Append temporary loading placeholder for assistant
  const loadingBubble = appendMessage("assistant", "Searching Maharashtra OBC knowledge base...", true);

  const reqLanguage = languageSelect.value;
  const headers = { "Content-Type": "application/json" };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        message: text,
        conversation_id: currentConversationId,
        language: reqLanguage
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const data = await res.json();
    currentConversationId = data.conversation_id;

    // Replace loading bubble with generated response
    updateAssistantMessage(loadingBubble, data.answer, data.sources, data.language, data.metrics);

    // If Voice-to-Voice auto-play is enabled, synthesize aloud!
    if (voiceAutoPlayToggle && voiceAutoPlayToggle.checked) {
      speakText(data.answer, data.language, null, loadingBubble);
    }

    // Refresh conversation list to show new chat title
    loadConversations();
  } catch (err) {
    console.error("Chat error:", err);
    updateAssistantMessage(
      loadingBubble,
      `⚠️ An error occurred while communicating with the assistant: ${err.message}. Please verify the server connection.`,
      []
    );
  } finally {
    chatInput.disabled = false;
    sendBtn.disabled = false;
    chatInput.focus();
    scrollToBottom();
  }
}

function appendMessage(role, text, isLoading = false) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.innerHTML = role === "user" ? "👤" : "🏛️";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const content = document.createElement("div");
  content.className = "message-content";
  if (isLoading) {
    content.innerHTML = `<span style="opacity: 0.7; font-style: italic;">${escapeHTML(text)}</span>`;
  } else {
    content.innerHTML = formatMarkdown(text);
  }

  bubble.appendChild(content);
  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
  scrollToBottom();

  return bubble;
}

const LANG_DISPLAY_NAMES = {
  en: "English",
  hi: "हिन्दी (Hindi)",
  mr: "मराठी (Marathi)",
  gu: "ગુજરાતી (Gujarati)",
  ta: "தமிழ் (Tamil)",
  te: "తెలుగు (Telugu)",
  bn: "বাংলা (Bengali)",
  kn: "ಕನ್ನಡ (Kannada)",
  ml: "മലയാളം (Malayalam)",
  pa: "ਪੰਜਾਬੀ (Punjabi)",
  hinglish: "Hinglish (हिंग्लिश)",
  gujlish: "Gujlish (ગુજલિશ)",
  auto: "Auto-detect",
  unknown: "Clarification"
};

const SPEECH_LOCALE_MAP = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
  gu: "gu-IN",
  ta: "ta-IN",
  te: "te-IN",
  bn: "bn-IN",
  kn: "kn-IN",
  ml: "ml-IN",
  pa: "pa-IN",
  hinglish: "hi-IN",
  gujlish: "gu-IN",
  auto: "en-IN"
};

let availableSpeechVoices = [];
function updateAvailableVoices() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    availableSpeechVoices = window.speechSynthesis.getVoices();
  }
}
if (typeof window !== "undefined" && window.speechSynthesis) {
  updateAvailableVoices();
  window.speechSynthesis.onvoiceschanged = updateAvailableVoices;
}

function updateAssistantMessage(bubble, text, sources, language = "en", metrics = null) {
  const content = bubble.querySelector(".message-content");
  content.innerHTML = formatMarkdown(text);

  // Message Actions (TTS Controls, Copy, Badges)
  const actionsBar = document.createElement("div");
  actionsBar.className = "message-actions";

  // Audio Controls Container
  const audioGroup = document.createElement("div");
  audioGroup.className = "audio-controls-group";

  // Play / Pause Button
  const playBtn = document.createElement("button");
  playBtn.className = "action-btn voice-play-btn";
  playBtn.title = "Listen to response aloud";
  playBtn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </svg>
    <span>Listen</span>
  `;

  // Stop Button (hidden until playing)
  const stopBtn = document.createElement("button");
  stopBtn.className = "action-btn voice-stop-btn";
  stopBtn.style.display = "none";
  stopBtn.title = "Stop playback";
  stopBtn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <rect x="5" y="5" width="14" height="14" rx="2"></rect>
    </svg>
    <span>Stop</span>
  `;

  // Replay Button (hidden until message has been played)
  const replayBtn = document.createElement("button");
  replayBtn.className = "action-btn voice-replay-btn";
  replayBtn.style.display = "none";
  replayBtn.title = "Replay from beginning";
  replayBtn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M1 4v6h6"></path>
      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
    </svg>
    <span>Replay</span>
  `;

  // Equalizer Indicator
  const equalizer = document.createElement("div");
  equalizer.className = "bubble-speaking-equalizer";
  equalizer.style.display = "none";
  equalizer.innerHTML = `
    <span class="eq-bar"></span>
    <span class="eq-bar"></span>
    <span class="eq-bar"></span>
    <span class="eq-bar"></span>
  `;

  // Audio button handlers
  playBtn.addEventListener("click", () => {
    if (activeSpeakerData && activeSpeakerData.playBtn === playBtn && window.speechSynthesis.speaking) {
      if (window.speechSynthesis.paused) {
        resumeSpeaking();
      } else {
        pauseSpeaking();
      }
    } else {
      speakText(text, language, playBtn, bubble, stopBtn, replayBtn, equalizer);
    }
  });

  stopBtn.addEventListener("click", () => {
    stopSpeaking();
  });

  replayBtn.addEventListener("click", () => {
    stopSpeaking();
    speakText(text, language, playBtn, bubble, stopBtn, replayBtn, equalizer);
  });

  audioGroup.appendChild(playBtn);
  audioGroup.appendChild(stopBtn);
  audioGroup.appendChild(replayBtn);
  audioGroup.appendChild(equalizer);
  actionsBar.appendChild(audioGroup);

  // Copy button
  const copyBtn = document.createElement("button");
  copyBtn.className = "action-btn copy-btn";
  copyBtn.title = "Copy message text";
  copyBtn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
    <span>Copy</span>
  `;
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(text);
    copyBtn.querySelector("span").textContent = "Copied!";
    showToast("Copied response to clipboard", "success", 2000);
    setTimeout(() => {
      copyBtn.querySelector("span").textContent = "Copy";
    }, 2000);
  });
  actionsBar.appendChild(copyBtn);

  // Regenerate button
  const regenBtn = document.createElement("button");
  regenBtn.className = "action-btn regenerate-btn";
  regenBtn.title = "Regenerate response from local LLM";
  regenBtn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
    </svg>
    <span>Regenerate</span>
  `;
  regenBtn.addEventListener("click", () => {
    const row = bubble.closest(".message-row");
    const prevRow = row ? row.previousElementSibling : null;
    let userPrompt = "";
    if (prevRow && prevRow.classList.contains("user")) {
      const uContent = prevRow.querySelector(".message-content");
      if (uContent) userPrompt = uContent.textContent.trim();
    }
    if (userPrompt) {
      chatInput.value = userPrompt;
      sendMessage();
    } else {
      showToast("Cannot determine original question to regenerate.", "warning");
    }
  });
  actionsBar.appendChild(regenBtn);

  // Detected Language Badge
  const langBadge = document.createElement("span");
  langBadge.className = "lang-badge";
  const displayLang = LANG_DISPLAY_NAMES[language] || language;
  langBadge.title = `Language: ${displayLang}`;
  langBadge.innerHTML = `🌐 ${displayLang}`;
  actionsBar.appendChild(langBadge);

  // Evaluation / Performance Metrics Badge
  if (metrics) {
    const metricsBadge = document.createElement("span");
    metricsBadge.className = "metrics-badge";
    const costText = metrics.cost_est_usd ? `$${metrics.cost_est_usd.toFixed(5)}` : "Free (Local LLM)";
    const tpsText = metrics.tokens_per_second ? ` · ${metrics.tokens_per_second} tps` : "";
    const modelText = metrics.model || "Local Model";
    const providerText = metrics.provider || "ollama";
    metricsBadge.title = `Model: ${modelText} | Runtime: ${providerText} | Latency: ${metrics.latency_ms}ms | Input Tokens: ~${metrics.input_tokens_est} | Output Tokens: ~${metrics.output_tokens_est} | Cost: ${costText}`;
    metricsBadge.innerHTML = `⚡ ${metrics.latency_ms}ms · ${metrics.total_tokens_est} tok${tpsText}`;
    actionsBar.appendChild(metricsBadge);
  }

  bubble.appendChild(actionsBar);

  // Grounded Sources Section
  if (sources && sources.length > 0) {
    const sourcesSec = document.createElement("div");
    sourcesSec.className = "sources-section";

    const header = document.createElement("div");
    header.className = "sources-header";
    header.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
      </svg>
      <span>Verified Scheme References & Sources</span>
    `;

    const chipsWrap = document.createElement("div");
    chipsWrap.className = "sources-chips";

    sources.forEach((src) => {
      const linkList = (src.links && src.links.length > 0) ? src.links : [{ title: src.title, url: src.url }];
      linkList.forEach((lk) => {
        const tag = document.createElement("a");
        tag.className = `source-tag ${src.source_quality === "provisional" ? "provisional" : ""}`;
        tag.href = lk.url || src.url || "https://mahadbt.maharashtra.gov.in/";
        tag.target = "_blank";
        tag.rel = "noopener noreferrer";
        tag.title = `${lk.title || src.title} - ${src.data_status || 'Verified'}`;
        tag.innerHTML = `
          <span>${escapeHTML(lk.title || src.title)}</span>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
        `;
        chipsWrap.appendChild(tag);
      });
    });

    sourcesSec.appendChild(header);
    sourcesSec.appendChild(chipsWrap);
    bubble.appendChild(sourcesSec);
  }
}

// ============================================================================
// Voice-to-Text (Speech Recognition)
// ============================================================================
function setupSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    console.info("Web Speech API not natively supported in this browser.");
    if (micBtn) micBtn.title = "Voice recognition not supported in this browser.";
    return;
  }

  speechRecognition = new SpeechRec();
  speechRecognition.continuous = true;
  speechRecognition.interimResults = true;

  speechRecognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add("recording");
    recordingBar.style.display = "flex";
    const selectedLang = languageSelect.value;
    const langLabel = LANG_DISPLAY_NAMES[selectedLang] || "your selected language";
    liveTranscript.textContent = `Listening... Speak in ${langLabel}`;
    showToast("Microphone active. Speak now...", "info", 2000);
  };

  speechRecognition.onresult = (event) => {
    let interim = "";
    let final = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        final += event.results[i][0].transcript;
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    const currentText = final || interim;
    if (currentText) {
      liveTranscript.textContent = currentText;
      chatInput.value = currentText;
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    }
  };

  speechRecognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
    if (event.error === "not-allowed") {
      showToast("Microphone permission denied. Please enable microphone access in your browser.", "error", 5000);
    } else if (event.error === "no-speech") {
      showToast("No speech detected. Please speak closer to the microphone.", "info", 3000);
    } else if (event.error === "network") {
      showToast("Speech recognition network error. Please verify your connection.", "warning", 4000);
    } else {
      showToast(`Speech recognition issue: ${event.error}`, "warning", 3000);
    }
    stopVoiceRecording();
  };

  speechRecognition.onend = () => {
    stopVoiceRecording();
  };
}

function toggleVoiceRecording() {
  if (isRecording) {
    stopVoiceRecordingAndSend();
  } else {
    startVoiceRecording();
  }
}

function startVoiceRecording() {
  if (!speechRecognition) {
    showToast("Speech recognition is not supported in this browser. You can type in any language.", "warning", 5000);
    return;
  }

  // Interruption: Cancel any ongoing speech output before starting to listen
  stopSpeaking();

  const lang = languageSelect.value;
  speechRecognition.lang = SPEECH_LOCALE_MAP[lang] || "en-IN";

  try {
    speechRecognition.start();
  } catch (e) {
    console.warn("Recognition already started or error:", e);
  }
}

function stopVoiceRecording() {
  isRecording = false;
  micBtn.classList.remove("recording");
  recordingBar.style.display = "none";
  if (speechRecognition) {
    try { speechRecognition.stop(); } catch (e) {}
  }
}

function stopVoiceRecordingAndSend() {
  stopVoiceRecording();
  if (chatInput.value.trim()) {
    sendMessage();
  }
}

function cancelVoiceRecording() {
  stopVoiceRecording();
  chatInput.value = "";
  chatInput.style.height = "auto";
}

// ============================================================================
// Text-to-Speech (TTS SpeechSynthesis)
// ============================================================================
function resetActiveAudioUI() {
  if (activeSpeakerData) {
    const { playBtn, stopBtn, replayBtn, equalizer, bubble } = activeSpeakerData;
    if (playBtn) {
      playBtn.classList.remove("active-speaker");
      playBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Listen</span>
      `;
    }
    if (stopBtn) stopBtn.style.display = "none";
    if (replayBtn) replayBtn.style.display = "inline-flex";
    if (equalizer) {
      equalizer.style.display = "none";
      equalizer.classList.remove("paused");
    }
    if (bubble) bubble.classList.remove("speaking-active");
  }

  if (globalSpeakingBar) globalSpeakingBar.style.display = "none";
  activeSpeakerData = null;
  currentUtterance = null;
}

function stopSpeaking() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  resetActiveAudioUI();
}

function pauseSpeaking() {
  if (window.speechSynthesis && window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
    window.speechSynthesis.pause();
    if (activeSpeakerData) {
      activeSpeakerData.isPaused = true;
      if (activeSpeakerData.playBtn) {
        activeSpeakerData.playBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          <span>Resume</span>
        `;
      }
      if (activeSpeakerData.equalizer) activeSpeakerData.equalizer.classList.add("paused");
    }
    if (pauseResumeGlobalBtn) {
      pauseResumeGlobalBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Resume</span>
      `;
    }
  }
}

function resumeSpeaking() {
  if (window.speechSynthesis && window.speechSynthesis.paused) {
    window.speechSynthesis.resume();
    if (activeSpeakerData) {
      activeSpeakerData.isPaused = false;
      if (activeSpeakerData.playBtn) {
        activeSpeakerData.playBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="4" width="4" height="16"></rect>
            <rect x="14" y="4" width="4" height="16"></rect>
          </svg>
          <span>Pause</span>
        `;
      }
      if (activeSpeakerData.equalizer) activeSpeakerData.equalizer.classList.remove("paused");
    }
    if (pauseResumeGlobalBtn) {
      pauseResumeGlobalBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <span>Pause</span>
      `;
    }
  }
}

function togglePauseResumeGlobalSpeech() {
  if (!window.speechSynthesis) return;
  if (window.speechSynthesis.paused) {
    resumeSpeaking();
  } else if (window.speechSynthesis.speaking) {
    pauseSpeaking();
  }
}

function speakText(text, lang = "en", triggerBtn = null, bubble = null, stopBtn = null, replayBtn = null, equalizer = null) {
  if (!window.speechSynthesis) {
    showToast("Audio synthesis is not supported in this browser.", "warning");
    return;
  }

  // Interruption: Stop any previous playback immediately
  stopSpeaking();

  // If called without element references (e.g. from auto-play), locate elements within bubble
  if (bubble) {
    if (!triggerBtn) triggerBtn = bubble.querySelector(".voice-play-btn");
    if (!stopBtn) stopBtn = bubble.querySelector(".voice-stop-btn");
    if (!replayBtn) replayBtn = bubble.querySelector(".voice-replay-btn");
    if (!equalizer) equalizer = bubble.querySelector(".bubble-speaking-equalizer");
  }

  // Strip markdown formatting, code, and raw URLs before synthesizing
  const cleanSpokenText = text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/```[\s\S]*?```/g, "Code example omitted from audio.")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[#*_\-\~>]/g, " ")
    .replace(/https?:\/\/\S+/g, "link")
    .replace(/\s+/g, " ")
    .trim();

  if (!cleanSpokenText) return;

  const targetLocale = SPEECH_LOCALE_MAP[lang] || "en-IN";
  if (availableSpeechVoices.length === 0) {
    availableSpeechVoices = window.speechSynthesis.getVoices();
  }

  // Find matching voice by exact locale or 2-letter language code
  const langPrefix = targetLocale.slice(0, 2).toLowerCase();
  const matchedVoice = availableSpeechVoices.find((v) => {
    const vLang = (v.lang || "").toLowerCase().replace("_", "-");
    return vLang === targetLocale.toLowerCase() || vLang.startsWith(langPrefix);
  });

  // Strict Language Consistency Protection:
  // Never let an English voice mispronounce Indian language text!
  if (lang !== "en" && lang !== "auto" && !matchedVoice) {
    const langName = LANG_DISPLAY_NAMES[lang] || lang;
    showToast(
      `Notice: Native voice for ${langName} (${targetLocale}) is not installed on your browser/system. Displaying complete text response.`,
      "info",
      6000
    );
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleanSpokenText);
  utterance.lang = targetLocale;
  if (matchedVoice) utterance.voice = matchedVoice;
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  activeSpeakerData = {
    text: cleanSpokenText,
    lang,
    playBtn: triggerBtn,
    stopBtn,
    replayBtn,
    equalizer,
    bubble,
    isPaused: false
  };
  currentUtterance = utterance;

  utterance.onstart = () => {
    if (triggerBtn) {
      triggerBtn.classList.add("active-speaker");
      triggerBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <span>Pause</span>
      `;
    }
    if (stopBtn) stopBtn.style.display = "inline-flex";
    if (replayBtn) replayBtn.style.display = "inline-flex";
    if (equalizer) {
      equalizer.style.display = "flex";
      equalizer.classList.remove("paused");
    }
    if (bubble) bubble.classList.add("speaking-active");

    // Global speaking bar
    if (globalSpeakingBar) {
      globalSpeakingBar.style.display = "flex";
      if (speakingLangBadge) speakingLangBadge.textContent = LANG_DISPLAY_NAMES[lang] || lang;
      if (pauseResumeGlobalBtn) {
        pauseResumeGlobalBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="4" width="4" height="16"></rect>
            <rect x="14" y="4" width="4" height="16"></rect>
          </svg>
          <span>Pause</span>
        `;
      }
    }
  };

  utterance.onend = () => {
    resetActiveAudioUI();
  };

  utterance.onerror = (e) => {
    console.warn("Speech synthesis error or interrupted:", e);
    resetActiveAudioUI();
  };

  utterance.onpause = () => {
    if (activeSpeakerData) activeSpeakerData.isPaused = true;
    if (triggerBtn) {
      triggerBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Resume</span>
      `;
    }
    if (equalizer) equalizer.classList.add("paused");
    if (pauseResumeGlobalBtn) {
      pauseResumeGlobalBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Resume</span>
      `;
    }
  };

  utterance.onresume = () => {
    if (activeSpeakerData) activeSpeakerData.isPaused = false;
    if (triggerBtn) {
      triggerBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <span>Pause</span>
      `;
    }
    if (equalizer) equalizer.classList.remove("paused");
    if (pauseResumeGlobalBtn) {
      pauseResumeGlobalBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <span>Pause</span>
      `;
    }
  };

  window.speechSynthesis.speak(utterance);
}

// ============================================================================
// Conversation Management
// ============================================================================
async function loadConversations() {
  if (!authToken) {
    conversationsList.innerHTML = `<div style="padding: 12px; font-size: 0.8rem; color: var(--text-muted); text-align: center;">Sign in to save and sync conversation history across devices.</div>`;
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/conversations`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (!res.ok) return;

    const convs = await res.json();
    conversationsList.innerHTML = "";

    if (convs.length === 0) {
      conversationsList.innerHTML = `<div style="padding: 12px; font-size: 0.8rem; color: var(--text-muted); text-align: center;">No prior chats yet.</div>`;
      return;
    }

    convs.forEach((c) => {
      const item = document.createElement("div");
      item.className = `conversation-item ${c.id === currentConversationId ? "active" : ""}`;
      item.innerHTML = `
        <span class="conversation-title" title="${escapeHTML(c.title)}">${escapeHTML(c.title)}</span>
        <button class="conv-delete-btn" title="Delete chat">✕</button>
      `;

      item.querySelector(".conversation-title").addEventListener("click", () => {
        loadConversationMessages(c.id);
      });

      item.querySelector(".conv-delete-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        deleteConversation(c.id);
      });

      conversationsList.appendChild(item);
    });
  } catch (err) {
    console.warn("Failed to load conversations:", err);
  }
}

async function loadConversationMessages(convId) {
  try {
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`${API_BASE}/api/conversations/${convId}`, { headers });
    if (!res.ok) throw new Error("Could not load conversation");

    const data = await res.json();
    currentConversationId = data.id;

    // Reset container and hide hero
    messagesContainer.innerHTML = "";
    if (welcomeHero) welcomeHero.style.display = "none";

    data.messages.forEach((m) => {
      if (m.role === "user") {
        appendMessage("user", m.text);
      } else {
        const bubble = appendMessage("assistant", m.text);
        updateAssistantMessage(bubble, m.text, m.sources, m.language);
      }
    });

    // Update active highlight in sidebar
    document.querySelectorAll(".conversation-item").forEach((el) => {
      el.classList.remove("active");
    });
    loadConversations();
  } catch (err) {
    showToast("Error loading conversation: " + err.message, "error");
  }
}

async function deleteConversation(convId) {
  if (!confirm("Are you sure you want to delete this conversation?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/conversations/${convId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      if (currentConversationId === convId) startNewChat();
      loadConversations();
    }
  } catch (err) {
    alert("Delete failed: " + err.message);
  }
}

function startNewChat() {
  currentConversationId = null;
  messagesContainer.innerHTML = "";
  if (welcomeHero) {
    messagesContainer.appendChild(welcomeHero);
    welcomeHero.style.display = "block";
  }
  document.querySelectorAll(".conversation-item").forEach((el) => el.classList.remove("active"));
  if (sidebar.classList.contains("open")) sidebar.classList.remove("open");
  chatInput.focus();
}

// ============================================================================
// Authentication
// ============================================================================
function updateUserUI() {
  if (currentUser) {
    userNameDisplay.textContent = currentUser.username;
    userRoleDisplay.textContent = currentUser.role === "admin" ? "Administrator" : "Student";
    authTriggerBtn.title = "Sign Out";
    authTriggerBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
        <polyline points="16 17 21 12 16 7"></polyline>
        <line x1="21" y1="12" x2="9" y2="12"></line>
      </svg>
    `;
    openAdminBtn.style.display = currentUser.role === "admin" ? "flex" : "none";
  } else {
    userNameDisplay.textContent = "Student Guest";
    userRoleDisplay.textContent = "Public Access";
    authTriggerBtn.title = "Sign In / Register";
    authTriggerBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
        <polyline points="10 17 15 12 10 7"></polyline>
        <line x1="15" y1="12" x2="3" y2="12"></line>
      </svg>
    `;
    openAdminBtn.style.display = "none";
  }
}

function openAuthModal() {
  if (currentUser) {
    // If signed in, trigger sign out confirmation
    if (confirm(`Signed in as ${currentUser.username} (${currentUser.role}). Sign out?`)) {
      localStorage.removeItem("voice_chatbot_token");
      localStorage.removeItem("voice_chatbot_user");
      authToken = null;
      currentUser = null;
      updateUserUI();
      loadConversations();
    }
  } else {
    setAuthMode("login");
    authModal.classList.add("open");
  }
}

function setAuthMode(mode) {
  authMode = mode;
  authErrorMsg.style.display = "none";
  if (mode === "login") {
    authTabLogin.classList.add("active");
    authTabRegister.classList.remove("active");
    authModalTitle.textContent = "Sign In";
    authSubmitBtn.textContent = "Sign In";
    emailGroup.style.display = "none";
  } else {
    authTabLogin.classList.remove("active");
    authTabRegister.classList.add("active");
    authModalTitle.textContent = "Register Student Account";
    authSubmitBtn.textContent = "Register Student";
    emailGroup.style.display = "block";
  }
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  authErrorMsg.style.display = "none";
  const username = authUsername.value.trim();
  const password = authPassword.value;
  const email = authEmail.value.trim();

  const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
  const payload = authMode === "login"
    ? { username_or_email: username, password }
    : { username, email, password };

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Authentication failed");

    authToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem("voice_chatbot_token", authToken);
    localStorage.setItem("voice_chatbot_user", JSON.stringify(currentUser));

    updateUserUI();
    loadConversations();
    authModal.classList.remove("open");
    authForm.reset();
  } catch (err) {
    authErrorMsg.textContent = err.message;
    authErrorMsg.style.display = "block";
  }
}

// ============================================================================
// Admin Knowledge Base Management
// ============================================================================
function openAdminModal() {
  if (!currentUser || currentUser.role !== "admin") {
    alert("Administrative role required to access Knowledge Management.");
    return;
  }
  adminModal.classList.add("open");
  loadKnowledgeEntries();
}

async function loadKnowledgeEntries() {
  if (!authToken) return;
  const q = kbSearchInput.value.trim();
  const recType = kbRecordTypeFilter.value;
  let url = `${API_BASE}/api/knowledge?limit=30`;
  if (q) url += `&q=${encodeURIComponent(q)}`;
  if (recType) url += `&record_type=${encodeURIComponent(recType)}`;

  try {
    const res = await fetch(url, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (!res.ok) throw new Error("Could not fetch knowledge entries.");

    const data = await res.json();
    if (statTotalCount) statTotalCount.textContent = data.total;

    kbTableBody.innerHTML = "";
    if (data.items.length === 0) {
      kbTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No entries match the filter.</td></tr>`;
      return;
    }

    data.items.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code style="color: var(--accent-emerald);">${escapeHTML(item.knowledge_id || item.id.slice(0, 8))}</code></td>
        <td style="max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHTML(item.title)}">
          <strong>${escapeHTML(item.title)}</strong>
        </td>
        <td><span class="badge" style="background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px;">${escapeHTML(item.record_type)}</span></td>
        <td><span style="color: #34d399; font-size: 0.78rem;">✓ ${escapeHTML(item.data_status || 'indexed')}</span></td>
        <td>
          <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; color: var(--accent-rose);" data-delete="${item.id}">Delete</button>
        </td>
      `;

      tr.querySelector("[data-delete]").addEventListener("click", () => {
        deleteKnowledgeEntry(item.id, item.title);
      });

      kbTableBody.appendChild(tr);
    });
  } catch (err) {
    console.error("Load knowledge error:", err);
  }
}

async function handleAddEntrySubmit(e) {
  e.preventDefault();
  if (!authToken) return;

  const payload = {
    title: document.getElementById("addTitle").value.trim(),
    record_type: document.getElementById("addRecordType").value,
    category: document.getElementById("addCategory").value.trim(),
    official_source: document.getElementById("addOfficialSource").value.trim(),
    content: document.getElementById("addContent").value.trim(),
    keywords: document.getElementById("addKeywords").value.trim(),
    multilingual_terms: document.getElementById("addMultilingualTerms").value.trim(),
  };

  try {
    const res = await fetch(`${API_BASE}/api/knowledge`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create knowledge entry.");
    }

    alert("Knowledge entry created and retrieval index synchronized successfully!");
    addEntryForm.reset();
    document.querySelector("[data-tab='tabBrowse']").click();
  } catch (err) {
    alert("Error saving entry: " + err.message);
  }
}

async function deleteKnowledgeEntry(id, title) {
  if (!confirm(`Delete entry "${title}"? This will invalidate its search index.`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/knowledge/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (res.ok) {
      loadKnowledgeEntries();
    } else {
      alert("Failed to delete entry.");
    }
  } catch (err) {
    alert("Delete error: " + err.message);
  }
}

async function handleDocumentUpload() {
  if (!selectedFile) {
    alert("Please select or drop a valid file (PDF, DOCX, TXT, CSV, XLSX) first.");
    return;
  }
  if (!authToken) {
    alert("Sign in as admin to upload documents.");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  const title = document.getElementById("uploadTitle").value.trim();
  const category = document.getElementById("uploadCategory").value.trim();
  if (title) formData.append("title", title);
  if (category) formData.append("category", category);

  uploadProgressWrap.style.display = "block";
  uploadProgressBar.style.width = "40%";
  uploadStatusText.textContent = "Uploading and parsing document...";

  try {
    const res = await fetch(`${API_BASE}/api/knowledge/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${authToken}` },
      body: formData
    });

    uploadProgressBar.style.width = "100%";
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Upload failed.");

    uploadStatusText.textContent = `Success! ${data.chunks_indexed} chunks indexed.`;
    alert(data.message || "Document parsed and indexed into vector search successfully!");
    selectedFile = null;
    selectedFileName.textContent = "No file chosen";
    fileUploadInput.value = "";
    document.getElementById("uploadTitle").value = "";
    loadKnowledgeEntries();
  } catch (err) {
    uploadProgressBar.style.width = "0%";
    uploadStatusText.textContent = "Error: " + err.message;
    alert("Document upload error: " + err.message);
  }
}

async function handleReseed() {
  if (!confirm("Re-seed the entire knowledge base from the bundled dataset CSV files?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/knowledge/seed?force=true`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Knowledge base re-seeded! Total entries: ${data.total_entries}`);
      loadKnowledgeEntries();
    }
  } catch (err) {
    alert("Re-seed failed: " + err.message);
  }
}

// ============================================================================
// Utilities
// ============================================================================
function escapeHTML(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, (tag) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  }[tag] || tag));
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHTML(text);

  // Headers: ### Header
  html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");

  // Bold: **bold**
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Italic: *italic*
  html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Markdown links: [text](url)
  html = html.replace(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // Bullet points
  html = html.replace(/^\s*[-*]\s+(.*)$/gim, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

  // Newlines into paragraphs
  html = html.split(/\n\n+/).map((para) => {
    if (para.startsWith("<h") || para.startsWith("<ul>")) return para;
    return `<p>${para.replace(/\n/g, "<br>")}</p>`;
  }).join("");

  return html;
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ============================================================================
// LLM Performance Evaluation & Benchmarking Studio Functions
// ============================================================================

async function openEvaluationModal() {
  evalModal.classList.add("open");
  await fetchModelInfo();
  await loadBenchmarkHistory();
}

async function fetchModelInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/evaluation/model-info`);
    if (!res.ok) return;
    const data = await res.json();
    const meta = data.model_metadata;
    const sys = data.system_resources;

    // Badges
    document.getElementById("evalModelBadge").textContent = meta.model_name || "gemini-2.5-flash";
    document.getElementById("evalProviderBadge").textContent = meta.model_provider || "google-genai";
    document.getElementById("evalContextBadge").textContent = meta.max_context_window >= 1000000 ? "1M Context" : `${meta.max_context_window} Tok`;

    // Telemetry Grid
    document.getElementById("infoProvider").textContent = meta.model_provider;
    document.getElementById("infoModel").textContent = `${meta.model_name} (${meta.model_version})`;
    document.getElementById("infoArchitecture").textContent = meta.model_architecture;
    document.getElementById("infoDeployment").textContent = meta.deployment_type;
    document.getElementById("infoQuantization").textContent = meta.quantization;
    document.getElementById("infoContextLimit").textContent = `${meta.max_context_window.toLocaleString()} tokens`;
    document.getElementById("infoMaxTokens").textContent = `${meta.max_output_tokens.toLocaleString()} tokens`;
    document.getElementById("infoEmbedding").textContent = meta.embedding_model;
    document.getElementById("infoVectorDB").textContent = meta.vector_database;
    if (sys) {
      document.getElementById("infoHardware").textContent = `CPU: ${sys.cpu_percent}% | RAM: ${sys.ram_used_mb} / ${sys.ram_total_mb} MB (${sys.ram_percent}%) | Threads: ${sys.threads}`;
    }
  } catch (err) {
    console.error("Failed to fetch model info:", err);
  }
}

async function runLiveBenchmark() {
  try {
    evalProgressWrap.style.display = "block";
    evalProgressBar.style.width = "25%";
    evalStatusText.textContent = "Initializing test dataset & measuring baseline latency...";

    const res = await fetch(`${API_BASE}/api/evaluation/run-benchmark`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { "Authorization": `Bearer ${authToken}` } : {})
      },
      body: JSON.stringify({
        name: `Live Benchmark - ${new Date().toLocaleTimeString()}`,
        warmup_requests: 1,
        repetitions: 1,
        enable_rag: true
      })
    });

    evalProgressBar.style.width = "85%";
    evalStatusText.textContent = "Calculating percentiles, token throughput, and groundedness metrics...";

    if (!res.ok) {
      throw new Error(`Benchmark failed with status ${res.status}`);
    }

    const data = await res.json();
    evalProgressBar.style.width = "100%";
    evalStatusText.textContent = "Benchmark completed successfully!";

    setTimeout(() => {
      evalProgressWrap.style.display = "none";
    }, 800);

    // Load full run details
    await loadRunDetail(data.run_id);
    await loadBenchmarkHistory();

    evalLastRunLabel.textContent = `Last run: ${new Date().toLocaleTimeString()} (${data.total_cases} cases)`;
  } catch (err) {
    evalStatusText.textContent = `Error: ${err.message}`;
    setTimeout(() => { evalProgressWrap.style.display = "none"; }, 3000);
    console.error("Benchmark run failed:", err);
  }
}

async function runParameterSweep() {
  try {
    evalProgressWrap.style.display = "block";
    evalProgressBar.style.width = "30%";
    evalStatusText.textContent = "Testing multiple parameter presets (Deterministic, Balanced, High Temp, Compact)...";

    const res = await fetch(`${API_BASE}/api/evaluation/run-experiment`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { "Authorization": `Bearer ${authToken}` } : {})
      },
      body: JSON.stringify({
        name: `Sweep - ${new Date().toLocaleTimeString()}`,
        subset_size: 4
      })
    });

    evalProgressBar.style.width = "90%";
    if (!res.ok) throw new Error("Sweep failed");

    const data = await res.json();
    evalProgressBar.style.width = "100%";
    setTimeout(() => { evalProgressWrap.style.display = "none"; }, 600);

    // Populate Sweep Table
    const tbody = document.getElementById("sweepTableBody");
    tbody.innerHTML = "";
    data.results.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${r.config_name}</strong></td>
        <td><code>${r.parameters.temperature}</code></td>
        <td>${r.avg_latency_ms.toFixed(1)} ms</td>
        <td>${r.avg_tps.toFixed(1)} TPS</td>
        <td>${r.total_tokens.toLocaleString()}</td>
        <td>${(r.avg_quality_score * 100).toFixed(1)}%</td>
        <td>${(r.avg_faithfulness * 100).toFixed(1)}%</td>
      `;
      tbody.appendChild(tr);
    });

    // Populate Recommendations
    document.getElementById("recommendationsGrid").style.display = "grid";
    document.getElementById("recomBalanced").textContent = data.recommendations.best_balanced;
    document.getElementById("recomLatency").textContent = data.recommendations.lowest_latency;
    document.getElementById("recomQuality").textContent = data.recommendations.highest_quality;
    document.getElementById("recomCost").textContent = data.recommendations.lowest_cost;

    // Switch to Parameter Experiments tab
    switchEvalTab("tabEvalParams");
  } catch (err) {
    evalStatusText.textContent = `Sweep error: ${err.message}`;
    setTimeout(() => { evalProgressWrap.style.display = "none"; }, 3000);
  }
}

async function runRAGAblation() {
  try {
    evalProgressWrap.style.display = "block";
    evalProgressBar.style.width = "35%";
    evalStatusText.textContent = "Running controlled ablation test: RAG enabled vs pure LLM zero-context...";

    const res = await fetch(`${API_BASE}/api/evaluation/run-ablation`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { "Authorization": `Bearer ${authToken}` } : {})
      },
      body: JSON.stringify({ subset_size: 5 })
    });

    evalProgressBar.style.width = "100%";
    if (!res.ok) throw new Error("Ablation test failed");

    const data = await res.json();
    setTimeout(() => { evalProgressWrap.style.display = "none"; }, 600);

    // Show ablation insights card
    const card = document.getElementById("ablationSummaryCard");
    card.style.display = "block";
    const ins = data.insights;
    document.getElementById("ablationInsights").innerHTML = `
      <p><strong>Ablation Conclusion:</strong> ${ins.conclusion}</p>
      <div style="display:flex; gap:20px; margin-top:10px;">
        <div>Factual Faithfulness Delta: <strong style="color:#34d399">+${(ins.faithfulness_delta * 100).toFixed(1)}%</strong></div>
        <div>Semantic Quality Delta: <strong style="color:#60a5fa">+${(ins.quality_delta * 100).toFixed(1)}%</strong></div>
        <div>Retrieval Latency Overhead: <strong style="color:#fcd34d">${ins.latency_overhead_ms} ms</strong></div>
      </div>
    `;

    switchEvalTab("tabEvalHistory");
    await loadBenchmarkHistory();
  } catch (err) {
    evalStatusText.textContent = `Ablation error: ${err.message}`;
    setTimeout(() => { evalProgressWrap.style.display = "none"; }, 3000);
  }
}

async function loadRunDetail(runId) {
  try {
    const res = await fetch(`${API_BASE}/api/evaluation/runs/${runId}`);
    if (!res.ok) return;
    const data = await res.json();
    const run = data.run;
    const results = data.results || [];
    currentEvaluatedResults = results;
    activeEvalRun = run;

    // Overview Tab
    document.getElementById("evalAvgLatency").textContent = `${run.avg_latency_ms.toFixed(1)} ms`;
    document.getElementById("evalP95Sub").textContent = `P95 Tail: ${run.p95_latency_ms.toFixed(1)} ms`;
    document.getElementById("evalTTFT").textContent = run.avg_ttft_ms ? `${run.avg_ttft_ms.toFixed(1)} ms` : "Available in live API";
    document.getElementById("evalTPS").textContent = run.avg_tps ? `${run.avg_tps.toFixed(1)} TPS` : "--";
    document.getElementById("evalTotalTokens").textContent = run.total_tokens.toLocaleString();
    document.getElementById("evalPromptTokensSub").textContent = `Prompt: ${run.total_prompt_tokens.toLocaleString()} | Compl: ${run.total_completion_tokens.toLocaleString()}`;
    document.getElementById("evalCostUSD").textContent = `$${run.estimated_cost_usd.toFixed(5)}`;
    document.getElementById("evalCompositeQuality").textContent = `${(run.avg_quality_score * 100).toFixed(1)}%`;
    document.getElementById("evalSuccessRate").textContent = run.total_cases > 0 ? `${((run.successful_cases / run.total_cases) * 100).toFixed(0)}%` : "100%";
    document.getElementById("evalCasesTestedSub").textContent = `${run.total_cases} test cases evaluated`;

    // Context utilization meter
    const utilPct = run.total_prompt_tokens > 0 ? Math.min(100, Math.max(0.5, ((run.total_prompt_tokens / 1048576) * 100))) : 0.05;
    document.getElementById("evalContextUtil").textContent = `${utilPct.toFixed(2)}%`;
    document.getElementById("evalContextMeter").style.width = `${utilPct}%`;

    // Performance Analytics Tab
    document.getElementById("pctMinLat").textContent = `${run.min_latency_ms.toFixed(1)} ms`;
    document.getElementById("pctP50Lat").textContent = `${run.p50_latency_ms.toFixed(1)} ms`;
    document.getElementById("pctP90Lat").textContent = `${run.p90_latency_ms.toFixed(1)} ms`;
    document.getElementById("pctP95Lat").textContent = `${run.p95_latency_ms.toFixed(1)} ms`;
    document.getElementById("pctMaxLat").textContent = `${run.max_latency_ms.toFixed(1)} ms`;

    const avgRetLat = results.length > 0 ? results.reduce((acc, r) => acc + (r.retrieval_latency_ms || 0), 0) / results.length : 0;
    const avgGenLat = results.length > 0 ? results.reduce((acc, r) => acc + (r.generation_latency_ms || 0), 0) / results.length : 0;
    document.getElementById("evalRetrievalLatVal").textContent = `${avgRetLat.toFixed(1)} ms`;
    document.getElementById("evalTTFTVal").textContent = run.avg_ttft_ms ? `${run.avg_ttft_ms.toFixed(1)} ms` : `${avgGenLat.toFixed(1)} ms`;
    document.getElementById("evalTotalGenVal").textContent = `${run.avg_latency_ms.toFixed(1)} ms`;

    // Tokens & Cost Tab
    const firstBreakdown = results.length > 0 && results[0].prompt_breakdown ? results[0].prompt_breakdown : {};
    document.getElementById("tokSystem").textContent = `${(firstBreakdown.system_tokens || 140).toLocaleString()} tokens`;
    document.getElementById("tokContext").textContent = `${(firstBreakdown.context_tokens || 850).toLocaleString()} tokens`;
    document.getElementById("tokUser").textContent = `${(firstBreakdown.user_tokens || 35).toLocaleString()} tokens`;
    document.getElementById("tokHistory").textContent = `${(firstBreakdown.history_tokens || 0).toLocaleString()} tokens`;
    document.getElementById("tokCompletion").textContent = `${run.total_completion_tokens.toLocaleString()} tokens`;
    document.getElementById("tokGaugeUsed").textContent = `${run.total_prompt_tokens.toLocaleString()} tokens`;
    document.getElementById("costTotalBench").textContent = `$${run.estimated_cost_usd.toFixed(5)}`;
    const costPer1k = run.total_cases > 0 ? (run.estimated_cost_usd / run.total_cases) * 1000 : 0.05;
    document.getElementById("costPer1k").textContent = `$${costPer1k.toFixed(4)}`;

    // Quality Scorecards Tab
    document.getElementById("qcExactMatch").textContent = `${(run.avg_exact_match * 100).toFixed(1)}%`;
    document.getElementById("qcTokenF1").textContent = `${(run.avg_f1 * 100).toFixed(1)}%`;
    document.getElementById("qcRougeL").textContent = `${(run.avg_rouge_l * 100).toFixed(1)}%`;
    document.getElementById("qcBleu").textContent = run.avg_bleu.toFixed(3);
    document.getElementById("qcSemantic").textContent = `${(run.avg_semantic_similarity * 100).toFixed(1)}%`;
    document.getElementById("qcFaithfulness").textContent = `${(run.avg_faithfulness * 100).toFixed(1)}%`;

    const hallucinatedCount = results.filter(r => r.hallucination_detected).length;
    const halluPct = results.length > 0 ? (hallucinatedCount / results.length) * 100 : 0;
    document.getElementById("qcHallucination").textContent = `${halluPct.toFixed(1)}%`;

    // Test Case Inspector Select
    const select = document.getElementById("evalTestCaseSelect");
    select.innerHTML = '<option value="">Select an evaluated test case...</option>';
    results.forEach((r, idx) => {
      const opt = document.createElement("option");
      opt.value = r.id;
      opt.textContent = `[${r.test_case_id || `Case ${idx+1}`}] ${r.prompt.slice(0, 50)}... (${r.category})`;
      select.appendChild(opt);
    });

    if (results.length > 0) {
      select.value = results[0].id;
      renderTestCaseInspector(results[0]);
    }
  } catch (err) {
    console.error("Failed to load run detail:", err);
  }
}

function handleTestCaseSelect(e) {
  const resultId = e.target.value;
  if (!resultId) {
    document.getElementById("inspectorBody").style.display = "none";
    return;
  }
  const result = currentEvaluatedResults.find(r => r.id === resultId);
  if (result) renderTestCaseInspector(result);
}

function renderTestCaseInspector(r) {
  document.getElementById("inspectorBody").style.display = "block";
  document.getElementById("inspectCategory").textContent = (r.category || "SCHOLARSHIP").toUpperCase();
  document.getElementById("inspectQuery").textContent = r.prompt;
  document.getElementById("inspectExpected").textContent = r.expected_output || "Grounded Maharashtra OBC scheme guidance matching official portal.";
  document.getElementById("inspectGenerated").innerHTML = renderMarkdown(r.generated_response);
  document.getElementById("humanFeedbackInput").value = r.human_feedback || "";
  setStarRating(r.human_rating || 0);
}

function setStarRating(val) {
  currentSelectedRating = val;
  document.querySelectorAll("#starRatingGroup .star").forEach(s => {
    const sVal = parseInt(s.getAttribute("data-val") || "1", 10);
    s.classList.toggle("active", sVal <= val);
  });
}

async function handleSaveHumanFeedback() {
  const select = document.getElementById("evalTestCaseSelect");
  const resultId = select.value;
  if (!resultId) {
    alert("Please select a test case first.");
    return;
  }
  const feedbackText = document.getElementById("humanFeedbackInput").value.trim();
  try {
    const res = await fetch(`${API_BASE}/api/evaluation/results/${resultId}/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { "Authorization": `Bearer ${authToken}` } : {})
      },
      body: JSON.stringify({
        rating: currentSelectedRating || 5,
        feedback: feedbackText
      })
    });
    if (res.ok) {
      alert("Human evaluation feedback saved successfully!");
      // Update cached result
      const cached = currentEvaluatedResults.find(r => r.id === resultId);
      if (cached) {
        cached.human_rating = currentSelectedRating;
        cached.human_feedback = feedbackText;
      }
    }
  } catch (err) {
    alert("Failed to save feedback: " + err.message);
  }
}

async function handleSingleParamTest(e) {
  e.preventDefault();
  const temp = parseFloat(document.getElementById("paramTemp").value);
  const topP = parseFloat(document.getElementById("paramTopP").value);
  const maxTok = parseInt(document.getElementById("paramMaxTokens").value, 10);
  const prompt = document.getElementById("paramPrompt").value.trim();
  const expected = document.getElementById("paramExpected").value.trim();

  if (!prompt) return;

  const outBox = document.getElementById("singleEvalOutput");
  outBox.style.display = "block";
  document.getElementById("singleRespPreview").textContent = "Executing request with current inference settings...";

  try {
    const res = await fetch(`${API_BASE}/api/evaluation/run-single`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt,
        expected_output: expected || null,
        parameters: { temperature: temp, top_p: topP, max_output_tokens: maxTok },
        enable_rag: true
      })
    });
    if (!res.ok) throw new Error("Single evaluation request failed");
    const data = await res.json();

    document.getElementById("singleLat").textContent = `${data.total_latency_ms.toFixed(1)} ms`;
    document.getElementById("singleTok").textContent = `${data.total_tokens} Tok`;
    document.getElementById("singleTPS").textContent = `${data.tokens_per_second.toFixed(1)} TPS`;
    document.getElementById("singleQuality").textContent = `${(data.semantic_similarity * 100).toFixed(1)}%`;
    document.getElementById("singleFaith").textContent = `${(data.faithfulness * 100).toFixed(1)}%`;
    document.getElementById("singleRespPreview").innerHTML = renderMarkdown(data.generated_response);
  } catch (err) {
    document.getElementById("singleRespPreview").textContent = `Error: ${err.message}`;
  }
}

function resetParamDefaults() {
  document.getElementById("paramTemp").value = "0.3";
  document.getElementById("valTemp").textContent = "0.3";
  document.getElementById("paramTopP").value = "0.95";
  document.getElementById("valTopP").textContent = "0.95";
  document.getElementById("paramMaxTokens").value = "1000";
  document.getElementById("valMaxTokens").textContent = "1000";
}

async function loadBenchmarkHistory() {
  try {
    const filter = document.getElementById("historyFilterType")?.value || "";
    const url = filter ? `${API_BASE}/api/evaluation/runs?limit=30&benchmark_type=${filter}` : `${API_BASE}/api/evaluation/runs?limit=30`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    const runs = data.items || [];

    const tbody = document.getElementById("historyTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (runs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No benchmark runs recorded yet. Click "Run Live Benchmark" above to generate your first benchmark.</td></tr>';
      return;
    }

    // If no active run loaded yet, load the latest
    if (!activeEvalRun && runs.length > 0) {
      loadRunDetail(runs[0].id);
    }

    runs.forEach(r => {
      const dateStr = r.created_at ? new Date(r.created_at).toLocaleString() : "--";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${r.name}</strong></td>
        <td><small class="text-muted">${dateStr}</small></td>
        <td><span class="badge" style="font-size:0.7rem">${r.benchmark_type}</span></td>
        <td>${r.total_cases}</td>
        <td>${r.avg_latency_ms.toFixed(1)} ms</td>
        <td>${r.p95_latency_ms.toFixed(1)} ms</td>
        <td>${r.avg_tps.toFixed(1)}</td>
        <td>${r.total_tokens.toLocaleString()}</td>
        <td>${(r.avg_quality_score * 100).toFixed(1)}%</td>
        <td>$${r.estimated_cost_usd.toFixed(4)}</td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-secondary btn-sm" onclick="loadRunDetail('${r.id}')" title="Load run into dashboard">View</button>
            <button class="btn btn-secondary btn-sm" onclick="exportRun('${r.id}', 'json')" title="Export JSON">JSON</button>
            <button class="btn btn-secondary btn-sm" onclick="exportRun('${r.id}', 'csv')" title="Export CSV">CSV</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load benchmark history:", err);
  }
}

function exportRun(runId, format) {
  window.open(`${API_BASE}/api/evaluation/runs/${runId}/export?format=${format}`, "_blank");
}

function switchEvalTab(targetTabId) {
  document.querySelectorAll(".eval-modal-card .tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".eval-modal-card .eval-tab-content").forEach(c => c.classList.remove("active"));
  const btn = document.querySelector(`.eval-modal-card .tab-btn[data-eval-tab="${targetTabId}"]`);
  const tab = document.getElementById(targetTabId);
  if (btn) btn.classList.add("active");
  if (tab) tab.classList.add("active");
}

