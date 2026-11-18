// Configuration Constants
const CONFIG = {
  PICKER_POPUP_WIDTH: 850,
  PICKER_POPUP_HEIGHT: 750,
  PICKER_POLL_INTERVAL_MS: 3000,
  PICKER_POLL_MAX_ATTEMPTS: 120, // 6 minutes
  DEFAULT_MAX_DISTANCE: 10,
  FALLBACK_REDIRECT_PATH: "/api/auth/callback",
  GOOGLE_CONSOLE_PICKER_BASE: "https://console.developers.google.com/apis/api/photospicker.googleapis.com/overview",
};

// API Endpoints Registry
const API = {
  STATUS: "/api/status",
  SETTINGS_CREDENTIALS: "/api/settings/credentials",
  AUTH_URL: (accId) => `/api/auth/url?account=${accId}`,
  AUTH_DISCONNECT: (accId) => `/api/auth/disconnect?account=${accId}`,
  PHOTOS: (accId, startDate, endDate) => {
    let url = `/api/photos?account=${accId}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return url;
  },
  PHOTOS_DATE_BOUNDS: "/api/photos/date-bounds",
  PHOTOS_PICKER_START: (accId) => `/api/photos/picker/start?account=${accId}`,
  PHOTOS_PICKER_POLL: (accId, sessionId) => `/api/photos/picker/poll?account=${accId}&session_id=${sessionId}`,
  PHOTOS_UPLOAD: (accId) => `/api/photos/upload?account=${accId}`,
  PHOTOS_SYNC: (accId) => `/api/photos/sync?account=${accId}`,
  PHOTOS_DEMO_SYNC: "/api/photos/demo-sync",
  PHOTOS_THUMBNAIL: (filename) => `/api/photos/thumbnail/${filename}`,
  MATCHER_RUN: (maxDist, startDate, endDate) => {
    let url = `/api/matcher/run?max_distance=${maxDist}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return url;
  },
  MATCHER_MATCHES: (startDate, endDate) => {
    let url = "/api/matcher/matches";
    const params = [];
    if (startDate) params.push(`start_date=${encodeURIComponent(startDate)}`);
    if (endDate) params.push(`end_date=${encodeURIComponent(endDate)}`;
    if (params.length) url += `?${params.join("&")}`;
    return url;
  },
  MATCHER_UNMATCHED: (accId, startDate, endDate) => {
    let url = `/api/matcher/unmatched?account=${accId}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return url;
  },
};

// State
let appState = {
  accounts: {
    account_1: { connected: false, email: null, photo_count: 0 },
    account_2: { connected: false, email: null, photo_count: 0 }
  },
  matches: [],
  photosAcc1: [],
  photosAcc2: [],
  selectedAcc1: null,
  selectedAcc2: null,
  uniqueAccount: 1,
  uniquePhotos: [],
  startDate: null,
  endDate: null,
  dateBounds: { min_date: null, max_date: null, total_photos: 0 }
};

// DOM ready
document.addEventListener("DOMContentLoaded", () => {
  updateRedirectUris();
  initTabs();
  initSlider();
  initEventHandlers();
  fetchStatus();
  fetchDateBounds();
  checkUrlParams();
  lucide.createIcons();
});

function updateRedirectUris(redirectUri) {
  const uri = redirectUri || (window.location.origin + CONFIG.FALLBACK_REDIRECT_PATH);
  const inputSetup = document.getElementById("uri-copy-input");
  const inputModal = document.getElementById("modal-input-redirect-uri");
  if (inputSetup) inputSetup.value = uri;
  if (inputModal) inputModal.value = uri;
}

function updateGoogleConsoleLink(clientId) {
  const link = document.getElementById("link-enable-picker");
  if (!link) return;
  if (clientId && clientId.includes("-")) {
    const projectNum = clientId.split("-")[0];
    link.href = `${CONFIG.GOOGLE_CONSOLE_PICKER_BASE}?project=${projectNum}`;
  } else {
    link.href = CONFIG.GOOGLE_CONSOLE_PICKER_BASE;
  }
}

function checkUrlParams() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("auth_success") === "true") {
    const acc = urlParams.get("account") || "1";
    // Clean URL
    window.history.replaceState({}, document.title, window.location.pathname);
    setTimeout(() => {
      alert(`Account ${acc} connected! Click the "Pick Photos" button on Account ${acc} to select the photos you want to compare.`);
    }, 400);
  } else if (urlParams.get("auth_error")) {
    const err = urlParams.get("auth_error");
    window.history.replaceState({}, document.title, window.location.pathname);
    alert(`Authentication Error: ${err}`);
  }
}

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      tabs.forEach(t => {
        t.classList.remove("active", "border-indigo-500", "text-indigo-400");
        t.classList.add("border-transparent", "text-slate-400");
      });
      btn.classList.add("active", "border-indigo-500", "text-indigo-400");
      btn.classList.remove("border-transparent", "text-slate-400");

      document.querySelectorAll(".tab-content").forEach(c => c.classList.add("hidden"));
      const target = document.getElementById(targetId);
      if (target) target.classList.remove("hidden");

      if (targetId === "tab-gallery") {
        fetchGallery();
      } else if (targetId === "tab-unmatched") {
        fetchUniquePhotos(appState.uniqueAccount);
      }
    });
  });
}

// Event Handlers
function initEventHandlers() {
  document.getElementById("btn-demo-data").addEventListener("click", loadDemoData);
  document.getElementById("btn-run-match").addEventListener("click", runMatcher);
  document.getElementById("btn-setup-guide").addEventListener("click", () => {
    document.querySelector('[data-tab="tab-setup"]').click();
  });

  document.getElementById("btn-open-settings").addEventListener("click", openSettingsModal);
  const bannerConfigure = document.getElementById("btn-banner-configure");
  if (bannerConfigure) {
    bannerConfigure.addEventListener("click", openSettingsModal);
  }
  document.getElementById("btn-close-settings").addEventListener("click", closeSettingsModal);
  document.getElementById("btn-cancel-settings").addEventListener("click", closeSettingsModal);
  document.getElementById("settings-modal").addEventListener("click", (e) => {
    if (e.target.id === "settings-modal") closeSettingsModal();
  });

  document.getElementById("btn-save-settings").addEventListener("click", () => {
    const cid = document.getElementById("modal-input-client-id").value;
    const csec = document.getElementById("modal-input-client-secret").value;
    saveCredentials(cid, csec, "modal");
  });

  document.getElementById("btn-save-credentials-setup").addEventListener("click", () => {
    const cid = document.getElementById("setup-input-client-id").value;
    const csec = document.getElementById("setup-input-client-secret").value;
    saveCredentials(cid, csec, "setup");
  });

  document.getElementById("btn-copy-modal-uri").addEventListener("click", () => {
    const input = document.getElementById("modal-input-redirect-uri");
    navigator.clipboard.writeText(input.value);
    const btn = document.getElementById("btn-copy-modal-uri");
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy"; }, 2000);
  });

  document.getElementById("btn-toggle-secret-modal").addEventListener("click", () => {
    toggleSecretVisibility("modal-input-client-secret");
  });

  document.getElementById("btn-toggle-secret-setup").addEventListener("click", () => {
    toggleSecretVisibility("setup-input-client-secret");
  });

  document.getElementById("btn-acc1-connect").addEventListener("click", () => connectAccount(1));
  document.getElementById("btn-acc2-connect").addEventListener("click", () => connectAccount(2));

  const btnPicker1 = document.getElementById("btn-acc1-picker");
  if (btnPicker1) btnPicker1.addEventListener("click", () => startPicker(1));
  const btnPicker2 = document.getElementById("btn-acc2-picker");
  if (btnPicker2) btnPicker2.addEventListener("click", () => startPicker(2));

  const btnUpload1 = document.getElementById("btn-acc1-upload");
  const inputUpload1 = document.getElementById("input-acc1-upload");
  if (btnUpload1 && inputUpload1) {
    btnUpload1.addEventListener("click", () => inputUpload1.click());
    inputUpload1.addEventListener("change", (e) => uploadLocalPhotos(1, e.target.files));
  }

  const btnUpload2 = document.getElementById("btn-acc2-upload");
  const inputUpload2 = document.getElementById("input-acc2-upload");
  if (btnUpload2 && inputUpload2) {
    btnUpload2.addEventListener("click", () => inputUpload2.click());
    inputUpload2.addEventListener("change", (e) => uploadLocalPhotos(2, e.target.files));
  }

  document.getElementById("btn-acc1-sync").addEventListener("click", () => syncAccount(1));
  document.getElementById("btn-acc2-sync").addEventListener("click", () => syncAccount(2));

  document.getElementById("btn-acc1-disconnect").addEventListener("click", () => disconnectAccount(1));
  document.getElementById("btn-acc2-disconnect").addEventListener("click", () => disconnectAccount(2));

  document.getElementById("toggle-unique-acc1").addEventListener("click", () => {
    appState.uniqueAccount = 1;
    updateUniqueButtons();
    fetchUniquePhotos(1);
  });

  document.getElementById("toggle-unique-acc2").addEventListener("click", () => {
    appState.uniqueAccount = 2;
    updateUniqueButtons();
    fetchUniquePhotos(2);
  });

  document.getElementById("btn-copy-uri").addEventListener("click", () => {
    const input = document.getElementById("uri-copy-input");
    navigator.clipboard.writeText(input.value);
    const btn = document.getElementById("btn-copy-uri");
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy"; }, 2000);
  });

  document.getElementById("btn-close-modal").addEventListener("click", closeModal);
  document.getElementById("compare-modal").addEventListener("click", (e) => {
    if (e.target.id === "compare-modal") closeModal();
  });

  document.getElementById("filter-match-type").addEventListener("change", (e) => {
    filterMatches(e.target.value);
  });

  // Date Range Toolbar Handlers
  const inputStart = document.getElementById("filter-start-date");
  const inputEnd = document.getElementById("filter-end-date");
  if (inputStart) inputStart.addEventListener("change", onDateFilterChange);
  if (inputEnd) inputEnd.addEventListener("change", onDateFilterChange);

  const btn7d = document.getElementById("btn-preset-7d");
  if (btn7d) btn7d.addEventListener("click", () => applyDatePreset(7));

  const btn30d = document.getElementById("btn-preset-30d");
  if (btn30d) btn30d.addEventListener("click", () => applyDatePreset(30));

  const btnYear = document.getElementById("btn-preset-year");
  if (btnYear) btnYear.addEventListener("click", applyYearPreset);

  const btnAll = document.getElementById("btn-preset-all");
  if (btnAll) btnAll.addEventListener("click", clearDateFilter);

  const btnAutofit = document.getElementById("btn-preset-autofit");
  if (btnAutofit) btnAutofit.addEventListener("click", applyAutoFitPreset);

  const btnClearDate = document.getElementById("btn-clear-date");
  if (btnClearDate) btnClearDate.addEventListener("click", clearDateFilter);

  const btnResetMatches = document.getElementById("btn-reset-matches-date");
  if (btnResetMatches) btnResetMatches.addEventListener("click", clearDateFilter);

  const btnActionDual = document.getElementById("btn-action-dual-view");
  if (btnActionDual) {
    btnActionDual.addEventListener("click", () => {
      document.querySelector('[data-tab="tab-gallery"]').click();
    });
  }

  const btnActionCompare = document.getElementById("btn-action-compare");
  if (btnActionCompare) {
    btnActionCompare.addEventListener("click", () => {
      runMatcher();
    });
  }

  const btnGalleryCompare = document.getElementById("btn-gallery-compare");
  if (btnGalleryCompare) {
    btnGalleryCompare.addEventListener("click", () => {
      runMatcher();
    });
  }
}

// Date Range Filtering Functions
function onDateFilterChange() {
  const startVal = document.getElementById("filter-start-date").value;
  const endVal = document.getElementById("filter-end-date").value;
  appState.startDate = startVal || null;
  appState.endDate = endVal || null;

  updateDateToolbarUI();
  fetchGallery();
  fetchMatches();
  if (appState.uniqueAccount) fetchUniquePhotos(appState.uniqueAccount);
}

function updateDateToolbarUI() {
  const badge = document.getElementById("date-range-badge");
  const clearBtn = document.getElementById("btn-clear-date");
  const dualViewBadge = document.getElementById("dual-view-date-badge");
  const matchesBanner = document.getElementById("matches-date-banner");
  const matchesDateText = document.getElementById("matches-date-range-text");

  if (appState.startDate || appState.endDate) {
    const startStr = appState.startDate || "Start";
    const endStr = appState.endDate || "Present";
    const label = `${startStr} → ${endStr}`;

    if (badge) {
      badge.textContent = label;
      badge.classList.remove("hidden");
    }
    if (clearBtn) clearBtn.classList.remove("hidden");
    if (dualViewBadge) dualViewBadge.textContent = label;
    if (matchesBanner) {
      matchesBanner.classList.remove("hidden");
      if (matchesDateText) matchesDateText.textContent = label;
    }
  } else {
    if (badge) badge.classList.add("hidden");
    if (clearBtn) clearBtn.classList.add("hidden");
    if (dualViewBadge) dualViewBadge.textContent = "All Dates";
    if (matchesBanner) matchesBanner.classList.add("hidden");
  }
}

function applyDatePreset(days) {
  const now = new Date();
  const past = new Date();
  past.setDate(now.getDate() - days);

  const startStr = past.toISOString().slice(0, 10);
  const endStr = now.toISOString().slice(0, 10);

  document.getElementById("filter-start-date").value = startStr;
  document.getElementById("filter-end-date").value = endStr;
  onDateFilterChange();
}

function applyYearPreset() {
  const now = new Date();
  const year = now.getFullYear();
  const startStr = `${year}-01-01`;
  const endStr = `${year}-12-31`;

  document.getElementById("filter-start-date").value = startStr;
  document.getElementById("filter-end-date").value = endStr;
  onDateFilterChange();
}

function clearDateFilter() {
  document.getElementById("filter-start-date").value = "";
  document.getElementById("filter-end-date").value = "";
  onDateFilterChange();
}

async function applyAutoFitPreset() {
  await fetchDateBounds();
  if (appState.dateBounds.min_date && appState.dateBounds.max_date) {
    document.getElementById("filter-start-date").value = appState.dateBounds.min_date;
    document.getElementById("filter-end-date").value = appState.dateBounds.max_date;
    onDateFilterChange();
  } else {
    alert("No photos found in database to fit date range.");
  }
}

async function fetchDateBounds() {
  try {
    const res = await fetch(API.PHOTOS_DATE_BOUNDS);
    const data = await res.json();
    appState.dateBounds = data;
    if (data.min_date) {
      document.getElementById("filter-start-date").min = data.min_date;
      document.getElementById("filter-end-date").min = data.min_date;
    }
    if (data.max_date) {
      document.getElementById("filter-start-date").max = data.max_date;
      document.getElementById("filter-end-date").max = data.max_date;
    }
  } catch (err) {
    console.error("Error fetching date bounds:", err);
  }
}

function formatPhotoDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr.slice(0, 10);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    }) + " · " + d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch (e) {
    return isoStr.slice(0, 10);
  }
}

// Fetch Status & Accounts
async function fetchStatus() {
  try {
    const res = await fetch(API.STATUS);
    const data = await res.json();

    const isConfigured = data.google_credentials_configured;
    const banner = document.getElementById("credentials-banner");
    if (!isConfigured) {
      banner.classList.remove("hidden");
    } else {
      banner.classList.add("hidden");
    }

    // Dynamic Redirect URIs
    updateRedirectUris(data.redirect_uri);

    // Update Header Pill
    const headerPill = document.getElementById("header-oauth-pill");
    if (headerPill) {
      headerPill.className = isConfigured 
        ? "w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" 
        : "w-2 h-2 rounded-full bg-amber-400";
    }

    // Update Setup Form Badge
    const setupBadge = document.getElementById("setup-form-status-badge");
    if (setupBadge) {
      if (isConfigured) {
        setupBadge.textContent = "Configured (Ready)";
        setupBadge.className = "px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400";
      } else {
        setupBadge.textContent = "Not Configured";
        setupBadge.className = "px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300";
      }
    }

    appState.accounts = data.accounts;
    updateAccountCard(1, data.accounts.account_1);
    updateAccountCard(2, data.accounts.account_2);

    fetchMatches();
    fetchCredentialsDetails();
  } catch (err) {
    console.error("Failed to fetch status:", err);
  }
}

async function fetchCredentialsDetails() {
  try {
    const res = await fetch(API.SETTINGS_CREDENTIALS);
    const data = await res.json();
    if (data.client_id) {
      document.getElementById("modal-input-client-id").value = data.client_id;
      document.getElementById("setup-input-client-id").value = data.client_id;
      updateGoogleConsoleLink(data.client_id);
    }
    if (data.redirect_uri) {
      updateRedirectUris(data.redirect_uri);
    }
    if (data.has_secret) {
      document.getElementById("modal-input-client-secret").placeholder = "•••••••••••••••••••••••• (Configured)";
      document.getElementById("setup-input-client-secret").placeholder = "•••••••••••••••••••••••• (Configured)";
    }
  } catch (e) {
    console.error("Error fetching credentials:", e);
  }
}

function openSettingsModal() {
  document.getElementById("settings-modal").classList.remove("hidden");
  document.getElementById("settings-status-box").classList.add("hidden");
  lucide.createIcons();
}

function closeSettingsModal() {
  document.getElementById("settings-modal").classList.add("hidden");
}

function toggleSecretVisibility(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === "password" ? "text" : "password";
}

async function saveCredentials(clientId, clientSecret, source) {
  const trimmedId = clientId ? clientId.trim() : "";
  const trimmedSec = clientSecret ? clientSecret.trim() : "";

  if (!trimmedId || !trimmedSec) {
    alert("Please enter both Google Client ID and Client Secret.");
    return;
  }

  const saveBtn = source === "modal" 
    ? document.getElementById("btn-save-settings")
    : document.getElementById("btn-save-credentials-setup");
  const origText = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = `<span class="animate-pulse">Saving...</span>`;

  try {
    const res = await fetch(API.SETTINGS_CREDENTIALS, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: trimmedId, client_secret: trimmedSec })
    });

    const data = await res.json();
    if (!res.ok) {
      alert(`Error saving credentials: ${data.detail || "Invalid input"}`);
      return;
    }

    // Success feedback
    if (source === "modal") {
      const box = document.getElementById("settings-status-box");
      box.className = "p-3 rounded-xl border text-xs bg-emerald-500/10 border-emerald-500/30 text-emerald-300";
      box.innerHTML = `<div class="flex items-center space-x-2"><i data-lucide="check-circle" class="w-4 h-4"></i><span>Credentials saved and applied! You can now connect both accounts.</span></div>`;
      box.classList.remove("hidden");
      lucide.createIcons();
      setTimeout(() => {
        closeSettingsModal();
      }, 1500);
    } else {
      const msg = document.getElementById("setup-form-msg");
      msg.textContent = "Credentials saved and active!";
      msg.className = "text-[11px] font-semibold text-emerald-400";
      setTimeout(() => { msg.textContent = ""; }, 3000);
    }

    await fetchStatus();
  } catch (err) {
    alert("Network error saving credentials.");
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = origText;
    lucide.createIcons();
  }
}

function updateAccountCard(accId, acc) {
  const isConnected = acc && acc.connected;
  const badge = document.getElementById(`acc${accId}-badge`);
  const name = document.getElementById(`acc${accId}-name`);
  const meta = document.getElementById(`acc${accId}-meta`);
  const avatar = document.getElementById(`acc${accId}-avatar`);
  const dot = document.getElementById(`acc${accId}-dot`);
  const btnConnect = document.getElementById(`btn-acc${accId}-connect`);
  const btnSync = document.getElementById(`btn-acc${accId}-sync`);
  const btnPicker = document.getElementById(`btn-acc${accId}-picker`);
  const btnUpload = document.getElementById(`btn-acc${accId}-upload`);
  const btnDisconnect = document.getElementById(`btn-acc${accId}-disconnect`);

  if (isConnected) {
    badge.textContent = "Connected";
    badge.className = "px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/20 text-emerald-400";
    name.textContent = acc.name || acc.email;
    meta.textContent = `${acc.email || ""} • ${acc.photo_count} photos`;
    dot.className = "absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-slate-800 rounded-full";

    if (acc.picture) {
      avatar.innerHTML = `<img src="${acc.picture}" class="w-full h-full rounded-full object-cover" alt="avatar">`;
    }

    btnConnect.classList.add("hidden");
    if (btnPicker) btnPicker.classList.remove("hidden");
    if (btnUpload) btnUpload.classList.remove("hidden");
    btnSync.classList.remove("hidden");
    btnDisconnect.classList.remove("hidden");
  } else {
    badge.textContent = "Disconnected";
    badge.className = "px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-700 text-slate-400";
    name.textContent = "Not Connected";
    meta.textContent = "0 photos synced";
    dot.className = "absolute bottom-0 right-0 w-3 h-3 bg-slate-500 border-2 border-slate-800 rounded-full";
    avatar.textContent = accId;

    btnConnect.classList.remove("hidden");
    if (btnPicker) btnPicker.classList.add("hidden");
    if (btnUpload) btnUpload.classList.add("hidden");
    btnSync.classList.add("hidden");
    btnDisconnect.classList.add("hidden");
  }
}

// Google Photos Picker Flow
async function startPicker(accId) {
  const btn = document.getElementById(`btn-acc${accId}-picker`);
  const origHtml = btn.innerHTML;
  btn.innerHTML = `<span class="animate-pulse">Opening...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch(API.PHOTOS_PICKER_START(accId), { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      const detail = data.detail || "API error";
      const urlMatch = detail.match(/https?:\/\/[^\s]+/);
      if (urlMatch) {
        if (confirm(`Google Photos Picker API is disabled in your Google Cloud Project.\n\nClick OK to open the Google Cloud Console to enable it now (takes ~30s after enabling).`)) {
          window.open(urlMatch[0], "_blank");
        }
      } else {
        alert(`Could not start Google Photos Picker: ${detail}`);
      }
      btn.innerHTML = origHtml;
      btn.disabled = false;
      return;
    }

    const sessionId = data.session_id;
    const pickerUri = data.picker_uri;
    
    // Open Google Photos Picker in a popup window
    const width = CONFIG.PICKER_POPUP_WIDTH;
    const height = CONFIG.PICKER_POPUP_HEIGHT;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    const popup = window.open(
      pickerUri,
      `GooglePhotosPicker_${accId}`,
      `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes,status=yes`
    );

    btn.innerHTML = `<span class="animate-pulse">Picking photos...</span>`;

    // Poll for user completing selection
    let pollAttempts = 0;
    const pollInterval = setInterval(async () => {
      pollAttempts++;
      if (pollAttempts > CONFIG.PICKER_POLL_MAX_ATTEMPTS) {
        clearInterval(pollInterval);
        btn.innerHTML = origHtml;
        btn.disabled = false;
        return;
      }

      try {
        const pollRes = await fetch(API.PHOTOS_PICKER_POLL(accId, sessionId), { method: "POST" });
        const pollData = await pollRes.json();

        if (pollData.ready) {
          clearInterval(pollInterval);
          if (popup && !popup.closed) popup.close();
          btn.innerHTML = origHtml;
          btn.disabled = false;

          await fetchStatus();
          await fetchGallery();
          await runMatcher();
          alert(`Successfully imported ${pollData.photos_count} photos from Account ${accId}!`);
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, CONFIG.PICKER_POLL_INTERVAL_MS);

  } catch (err) {
    alert("Error launching Google Photos Picker.");
    btn.innerHTML = origHtml;
    btn.disabled = false;
  }
}

// Local Photos Upload Flow
async function uploadLocalPhotos(accId, fileList) {
  if (!fileList || fileList.length === 0) return;
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append("files", fileList[i]);
  }

  try {
    const res = await fetch(API.PHOTOS_UPLOAD(accId), {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) {
      alert(`Upload failed: ${data.detail || "Error"}`);
      return;
    }
    await fetchStatus();
    await fetchGallery();
    await runMatcher();
    alert(`Uploaded ${data.uploaded_count} photos to Account ${accId}!`);
  } catch (err) {
    alert("Network error uploading photos.");
  }
}

// Connect Account
async function connectAccount(accId) {
  try {
    const res = await fetch(API.AUTH_URL(accId));
    if (!res.ok) {
      const err = await res.json();
      alert(`Could not start Google OAuth: ${err.detail || "Check Google credentials in .env"}`);
      document.querySelector('[data-tab="tab-setup"]').click();
      return;
    }
    const data = await res.json();
    window.location.href = data.auth_url;
  } catch (err) {
    alert("Error initiating Google authentication. Make sure backend is running.");
  }
}

// Sync Account Photos
async function syncAccount(accId) {
  const btn = document.getElementById(`btn-acc${accId}-sync`);
  btn.classList.add("animate-spin");
  try {
    const res = await fetch(API.PHOTOS_SYNC(accId), { method: "POST" });
    if (!res.ok) {
      const err = await res.json();
      alert(`Failed to sync photos: ${err.detail || "API error"}`);
    } else {
      await fetchStatus();
      await fetchGallery();
      await runMatcher();
    }
  } catch (err) {
    alert("Error syncing photos.");
  } finally {
    btn.classList.remove("animate-spin");
  }
}

// Disconnect Account
async function disconnectAccount(accId) {
  if (!confirm(`Are you sure you want to disconnect Account ${accId}? This will remove its cached photos.`)) return;
  try {
    await fetch(API.AUTH_DISCONNECT(accId), { method: "POST" });
    await fetchStatus();
    await fetchGallery();
    await fetchMatches();
  } catch (err) {
    alert("Error disconnecting account.");
  }
}

// Load Synthetic Demo Data
async function loadDemoData() {
  const btn = document.getElementById("btn-demo-data");
  const origText = btn.innerHTML;
  btn.innerHTML = `<span class="animate-pulse">Loading demo...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch(API.PHOTOS_DEMO_SYNC, { method: "POST" });
    const data = await res.json();
    await fetchStatus();
    await fetchGallery();
    await fetchMatches();
    alert("Demo dataset loaded! 10 sample photos generated for both accounts with known exact duplicates, burst shots, and unique items.");
  } catch (err) {
    alert("Failed to load demo data.");
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
    lucide.createIcons();
  }
}

// Run Matcher
async function runMatcher() {
  const btn = document.getElementById("btn-action-compare");
  const btnTop = document.getElementById("btn-run-match");
  const origHtml = btn ? btn.innerHTML : "";
  if (btn) {
    btn.innerHTML = `<span class="animate-pulse">Scanning range...</span>`;
    btn.disabled = true;
  }
  if (btnTop) {
    btnTop.innerHTML = `<span class="animate-pulse">Scanning...</span>`;
    btnTop.disabled = true;
  }

  try {
    const res = await fetch(API.MATCHER_RUN(CONFIG.DEFAULT_MAX_DISTANCE, appState.startDate, appState.endDate), { method: "POST" });
    const data = await res.json();

    const res = await fetch(url, { method: "POST" });
    const data = await res.json();

    // Automatically switch to Duplicates & Matches tab
    const tabMatchesBtn = document.querySelector('[data-tab="tab-matches"]');
    if (tabMatchesBtn) tabMatchesBtn.click();

    if (data.status === "insufficient_data") {
      alert(`${data.message}\n\nAccount 1 photos in range: ${data.scanned_acc1 || 0}\nAccount 2 photos in range: ${data.scanned_acc2 || 0}`);
    } else {
      await fetchMatches();
      await fetchStatus();

      const summaryText = document.getElementById("matches-date-summary-text");
      if (summaryText) {
        summaryText.textContent = `(Scanned ${data.scanned_acc1} in Acc 1, ${data.scanned_acc2} in Acc 2 · Found ${data.total_matches} duplicate pairs)`;
      }

      if (data.total_matches > 0) {
        alert(`Comparison Complete! Found ${data.total_matches} duplicate photos side-by-side (${data.exact_matches} exact matches, ${data.duplicate_matches} near duplicates).`);
      }
    }
  } catch (err) {
    console.error("Error running matcher:", err);
    alert("Error executing comparison.");
  } finally {
    if (btn) {
      btn.innerHTML = origHtml;
      btn.disabled = false;
    }
    if (btnTop) {
      btnTop.innerHTML = `<i data-lucide="scan" class="w-3.5 h-3.5"></i><span>Compare All</span>`;
      btnTop.disabled = false;
    }
    lucide.createIcons();
  }
}

// Fetch and Render Matches
async function fetchMatches() {
  try {
    const res = await fetch(API.MATCHER_MATCHES(appState.startDate, appState.endDate));
    const data = await res.json();
    appState.matches = data.matches || [];

    document.getElementById("badge-matches-count").textContent = appState.matches.length;
    renderMatches(appState.matches);
  } catch (err) {
    console.error("Error fetching matches:", err);
  }
}

function filterMatches(filterType) {
  if (filterType === "all") {
    renderMatches(appState.matches);
  } else {
    const filtered = appState.matches.filter(m => m.match_type === filterType);
    renderMatches(filtered);
  }
}

function getThumbUrl(thumbnailPath, baseUrl) {
  if (thumbnailPath) {
    const filename = thumbnailPath.split("/").pop();
    return API.PHOTOS_THUMBNAIL(filename);
  }
  return baseUrl ? `${baseUrl}=w500-h500` : "";
}

function renderMatches(matches) {
  const container = document.getElementById("matches-grid");
  if (!matches || matches.length === 0) {
    const rangeText = (appState.startDate || appState.endDate)
      ? `between ${appState.startDate || 'beginning'} and ${appState.endDate || 'present'}`
      : "in library";
    container.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-500">
        <i data-lucide="search" class="w-10 h-10 mx-auto text-slate-600 mb-2"></i>
        <p class="text-sm font-semibold text-slate-300">No duplicates detected ${rangeText}</p>
        <p class="text-xs mt-1 text-slate-400">Try adjusting the date range above, picking more photos from Google Photos, or testing with demo data.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = matches.map(m => {
    let badgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    let badgeLabel = `${m.similarity_score}% Exact Match`;

    if (m.match_type === "duplicate") {
      badgeClass = "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      badgeLabel = `${m.similarity_score}% Duplicate`;
    } else if (m.match_type === "similar") {
      badgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";
      badgeLabel = `${m.similarity_score}% Similar / Burst`;
    }

    const t1Url = getThumbUrl(m.p1_thumbnail, m.p1_base_url);
    const t2Url = getThumbUrl(m.p2_thumbnail, m.p2_base_url);
    const d1Str = formatPhotoDate(m.p1_creation_time);
    const d2Str = formatPhotoDate(m.p2_creation_time);

    let timeDeltaText = "Capture time: Identical";
    if (m.time_diff_seconds !== null && m.time_diff_seconds > 0) {
      if (m.time_diff_seconds < 60) timeDeltaText = `Time delta: ${Math.round(m.time_diff_seconds)}s apart`;
      else if (m.time_diff_seconds < 3600) timeDeltaText = `Time delta: ${Math.round(m.time_diff_seconds / 60)}m apart`;
      else timeDeltaText = `Time delta: ${Math.round(m.time_diff_seconds / 3600)}h apart`;
    }

    return `
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between hover:border-slate-700 transition shadow-lg">
        <div>
          <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/60">
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${badgeClass}">
              ${badgeLabel}
            </span>
            <div class="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
              <span>pHash dist: ${m.phash_distance}</span>
              <span class="text-slate-600">·</span>
              <span class="text-slate-400 font-sans">${timeDeltaText}</span>
            </div>
          </div>

          <!-- Side-by-Side Photos Grid -->
          <div class="grid grid-cols-2 gap-4 mb-3">
            <!-- Left (Account 1 Photo) -->
            <div class="space-y-2 bg-slate-950/60 p-2.5 rounded-xl border border-indigo-900/30">
              <div class="relative aspect-video rounded-lg overflow-hidden bg-slate-950 border border-slate-800">
                <img src="${t1Url}" class="w-full h-full object-cover" alt="${m.p1_filename}">
                <span class="absolute top-1.5 left-1.5 px-2 py-0.5 bg-indigo-600 text-white rounded text-[10px] font-bold shadow">Account 1</span>
              </div>
              <div>
                <p class="text-xs font-semibold text-slate-200 truncate" title="${m.p1_filename}">${m.p1_filename || "Photo"}</p>
                <p class="text-[10px] text-indigo-400 font-medium">${d1Str || "Date unknown"}</p>
                <p class="text-[10px] text-slate-500">${m.p1_width || "?"} × ${m.p1_height || "?"}</p>
              </div>
            </div>

            <!-- Right (Account 2 Photo) -->
            <div class="space-y-2 bg-slate-950/60 p-2.5 rounded-xl border border-purple-900/30">
              <div class="relative aspect-video rounded-lg overflow-hidden bg-slate-950 border border-slate-800">
                <img src="${t2Url}" class="w-full h-full object-cover" alt="${m.p2_filename}">
                <span class="absolute top-1.5 right-1.5 px-2 py-0.5 bg-purple-600 text-white rounded text-[10px] font-bold shadow">Account 2</span>
              </div>
              <div>
                <p class="text-xs font-semibold text-slate-200 truncate" title="${m.p2_filename}">${m.p2_filename || "Photo"}</p>
                <p class="text-[10px] text-purple-400 font-medium">${d2Str || "Date unknown"}</p>
                <p class="text-[10px] text-slate-500">${m.p2_width || "?"} × ${m.p2_height || "?"}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between">
          <span class="text-[11px] text-slate-500">Side-by-side duplicate view</span>
          <button class="btn-compare-pair px-3.5 py-1.5 rounded-lg bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center space-x-1.5 transition"
                  data-p1='${JSON.stringify({url: t1Url, name: m.p1_filename, date: m.p1_creation_time, dim: `${m.p1_width}x${m.p1_height}`})}'
                  data-p2='${JSON.stringify({url: t2Url, name: m.p2_filename, date: m.p2_creation_time, dim: `${m.p2_width}x${m.p2_height}`})}'>
            <i data-lucide="sliders" class="w-3.5 h-3.5 text-indigo-400"></i>
            <span>Interactive Diff Slider</span>
          </button>
        </div>
      </div>
    `;
  }).join("");

  document.querySelectorAll(".btn-compare-pair").forEach(btn => {
    btn.addEventListener("click", () => {
      const p1 = JSON.parse(btn.dataset.p1);
      const p2 = JSON.parse(btn.dataset.p2);
      openCompareModal(p1, p2);
    });
  });

  lucide.createIcons();
}

// Dual Gallery
async function fetchGallery() {
  try {
    const [res1, res2] = await Promise.all([
      fetch(API.PHOTOS(1, appState.startDate, appState.endDate)),
      fetch(API.PHOTOS(2, appState.startDate, appState.endDate))
    ]);
    const d1 = await res1.json();
    const d2 = await res2.json();

    appState.photosAcc1 = d1.photos || [];
    appState.photosAcc2 = d2.photos || [];

    const rangeInfo = (appState.startDate || appState.endDate) ? "in range" : "synced";
    document.getElementById("acc1-gallery-count").textContent = `(${appState.photosAcc1.length} ${rangeInfo})`;
    document.getElementById("acc2-gallery-count").textContent = `(${appState.photosAcc2.length} ${rangeInfo})`;

    const statsElem = document.getElementById("dual-view-summary-stats");
    if (statsElem) {
      statsElem.textContent = `· Showing ${appState.photosAcc1.length} in Acc 1 and ${appState.photosAcc2.length} in Acc 2`;
    }

    renderGalleryCol(1, appState.photosAcc1, document.getElementById("gallery-acc1"));
    renderGalleryCol(2, appState.photosAcc2, document.getElementById("gallery-acc2"));
  } catch (err) {
    console.error("Error loading gallery:", err);
  }
}

function renderGalleryCol(accId, photos, container) {
  if (!photos || photos.length === 0) {
    const dateDesc = (appState.startDate || appState.endDate) 
      ? `between ${appState.startDate || 'beginning'} and ${appState.endDate || 'present'}`
      : "yet";
    container.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-500 text-xs px-4">
        <i data-lucide="image-off" class="w-8 h-8 mx-auto text-slate-600 mb-2"></i>
        <p class="font-medium text-slate-400">No photos in Account ${accId} ${dateDesc}.</p>
        <p class="text-[11px] text-slate-500 mt-1">Try adjusting the date range above or picking photos from Google Photos.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = photos.map(p => {
    const thumbUrl = getThumbUrl(p.thumbnail_path, p.base_url);
    const dateStr = formatPhotoDate(p.creation_time);
    return `
      <div class="photo-card relative aspect-square rounded-xl overflow-hidden bg-slate-900 border border-slate-800 cursor-pointer group hover:border-indigo-500/60 transition shadow"
           data-photo='${JSON.stringify({url: thumbUrl, name: p.filename, date: p.creation_time, dim: `${p.width}x${p.height}`, accId: accId})}'>
        <img src="${thumbUrl}" class="w-full h-full object-cover transition duration-300 group-hover:scale-105" alt="${p.filename}">
        
        <!-- Capture Date Badge -->
        ${dateStr ? `<span class="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-slate-950/80 backdrop-blur rounded text-[9px] font-medium text-slate-300 border border-slate-700/50">${dateStr}</span>` : ""}

        <!-- Hover info overlay -->
        <div class="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/20 to-transparent opacity-0 group-hover:opacity-100 transition p-2.5 flex flex-col justify-end">
          <p class="text-[11px] font-semibold text-slate-100 truncate">${p.filename || "Photo"}</p>
          <div class="flex items-center justify-between text-[10px] text-slate-400 mt-0.5">
            <span>${p.width || "?"} × ${p.height || "?"}</span>
            <span class="text-indigo-400 font-medium">Click to Compare</span>
          </div>
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".photo-card").forEach(card => {
    card.addEventListener("click", () => {
      const p = JSON.parse(card.dataset.photo);
      handleGallerySelection(p, card);
    });
  });

  lucide.createIcons();
}

function handleGallerySelection(photo, element) {
  if (photo.accId === 1) {
    document.querySelectorAll("#gallery-acc1 .photo-card").forEach(c => c.classList.remove("selected"));
    element.classList.add("selected");
    appState.selectedAcc1 = photo;
  } else {
    document.querySelectorAll("#gallery-acc2 .photo-card").forEach(c => c.classList.remove("selected"));
    element.classList.add("selected");
    appState.selectedAcc2 = photo;
  }

  if (appState.selectedAcc1 && appState.selectedAcc2) {
    openCompareModal(appState.selectedAcc1, appState.selectedAcc2);
  }
}

// Unique Photos (Reconciliation)
async function fetchUniquePhotos(accId) {
  try {
    const res = await fetch(API.MATCHER_UNMATCHED(accId, appState.startDate, appState.endDate));
    const data = await res.json();
    appState.uniquePhotos = data.photos || [];

    document.getElementById("badge-unmatched-count").textContent = appState.uniquePhotos.length;
    renderUniqueGrid(appState.uniquePhotos, accId);
  } catch (err) {
    console.error("Error fetching unique photos:", err);
  }
}

function updateUniqueButtons() {
  const b1 = document.getElementById("toggle-unique-acc1");
  const b2 = document.getElementById("toggle-unique-acc2");

  if (appState.uniqueAccount === 1) {
    b1.className = "px-3 py-1 rounded text-xs font-medium bg-indigo-600 text-white";
    b2.className = "px-3 py-1 rounded text-xs font-medium text-slate-400 hover:text-slate-200";
  } else {
    b2.className = "px-3 py-1 rounded text-xs font-medium bg-purple-600 text-white";
    b1.className = "px-3 py-1 rounded text-xs font-medium text-slate-400 hover:text-slate-200";
  }
}

function renderUniqueGrid(photos, accId) {
  const container = document.getElementById("unique-grid");
  if (!photos || photos.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-500 text-xs">
        No unique photos found for Account ${accId}. (All photos have matching counterparts in the other account!)
      </div>
    `;
    return;
  }

  container.innerHTML = photos.map(p => {
    const thumbUrl = getThumbUrl(p.thumbnail_path, p.base_url);
    return `
      <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden p-2 space-y-1.5">
        <div class="aspect-square rounded-lg overflow-hidden bg-slate-950">
          <img src="${thumbUrl}" class="w-full h-full object-cover" alt="${p.filename}">
        </div>
        <p class="text-[11px] font-medium text-slate-200 truncate" title="${p.filename}">${p.filename || "Photo"}</p>
        <p class="text-[10px] text-slate-500">${p.creation_time ? new Date(p.creation_time).toLocaleDateString() : "-"}</p>
      </div>
    `;
  }).join("");
}

// Side-by-Side Diff Slider Modal
function openCompareModal(p1, p2) {
  const modal = document.getElementById("compare-modal");
  const img1 = document.getElementById("modal-img-1");
  const img2 = document.getElementById("modal-img-2");

  img1.src = p1.url;
  img2.src = p2.url;

  document.getElementById("modal-meta-1-name").textContent = p1.name || "Photo 1";
  document.getElementById("modal-meta-1-date").textContent = `Date: ${p1.date || "Unknown"}`;
  document.getElementById("modal-meta-1-dim").textContent = `Resolution: ${p1.dim || "Unknown"}`;

  document.getElementById("modal-meta-2-name").textContent = p2.name || "Photo 2";
  document.getElementById("modal-meta-2-date").textContent = `Date: ${p2.date || "Unknown"}`;
  document.getElementById("modal-meta-2-dim").textContent = `Resolution: ${p2.dim || "Unknown"}`;

  // Reset slider to 50%
  setSliderPosition(50);
  modal.classList.remove("hidden");
  lucide.createIcons();
}

function closeModal() {
  document.getElementById("compare-modal").classList.add("hidden");
  appState.selectedAcc1 = null;
  appState.selectedAcc2 = null;
  document.querySelectorAll(".photo-card").forEach(c => c.classList.remove("selected"));
}

function setSliderPosition(percent) {
  const p = Math.max(0, Math.min(100, percent));
  document.getElementById("slider-clipper").style.width = `${p}%`;
  document.getElementById("slider-handle").style.left = `${p}%`;

  // Fix foreground image full width inside clipped div
  const wrapper = document.getElementById("slider-wrapper");
  const img1 = document.getElementById("modal-img-1");
  if (wrapper && img1) {
    img1.style.width = `${wrapper.clientWidth}px`;
  }
}

function initSlider() {
  const wrapper = document.getElementById("slider-wrapper");
  let isDragging = false;

  const onMove = (e) => {
    if (!isDragging) return;
    const rect = wrapper.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const x = clientX - rect.left;
    const percent = (x / rect.width) * 100;
    setSliderPosition(percent);
  };

  const onStart = () => { isDragging = true; };
  const onEnd = () => { isDragging = false; };

  wrapper.addEventListener("mousedown", (e) => {
    onStart();
    onMove(e);
  });
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onEnd);

  wrapper.addEventListener("touchstart", (e) => {
    onStart();
    onMove(e);
  });
  window.addEventListener("touchmove", onMove);
  window.addEventListener("touchend", onEnd);

  window.addEventListener("resize", () => {
    const p = parseFloat(document.getElementById("slider-handle").style.left) || 50;
    setSliderPosition(p);
  });
}

