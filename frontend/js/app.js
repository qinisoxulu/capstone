
import { Auth } from "./auth.js";
const el = (sel) => document.querySelector(sel);
const els = (sel) => Array.from(document.querySelectorAll(sel));

const settings = {
  get apiBaseUrl() { return localStorage.getItem("apiBaseUrl") || ""; },
  set apiBaseUrl(v) { localStorage.setItem("apiBaseUrl", v || ""); },

  get jwtToken() { return localStorage.getItem("jwtToken") || ""; },
  set jwtToken(v) { localStorage.setItem("jwtToken", v || ""); },
};

const state = {
  currentView: "explore",
  selectedFacility: null,
  facilities: [],
  units: [],
  rentals: [],
};

function toast(type, title, body) {
  const wrap = el("#toasts");
  const node = document.createElement("div");
  node.className = `toast ${type || ""}`;
  node.innerHTML = `
    <div class="toast-title">${escapeHtml(title)}</div>
    ${body ? `<div class="toast-body">${escapeHtml(body)}</div>` : ""}
  `;
  wrap.appendChild(node);
  setTimeout(() => node.remove(), 3500);
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setView(view) {
  state.currentView = view;
  els(".tab").forEach(btn => btn.classList.toggle("is-active", btn.dataset.view === view));
  els(".view").forEach(v => v.hidden = true);
  el(`#view-${view}`).hidden = false;
}

/* ====== API client ====== */
async function apiFetch(path, { method = "GET", query, body } = {}) {
  const base = settings.apiBaseUrl?.trim();
  if (!base) throw new Error("API Base URL not set (open Settings).");

  const url = new URL(base.replace(/\/$/, "") + path);
  if (query && typeof query === "object") {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }

  const headers = { "Content-Type": "application/json" };
  const authHeader = Auth.getAuthHeader();
  if (authHeader) headers.Authorization = authHeader;
  const token = settings.jwtToken?.trim();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const contentType = res.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    const msg = (payload && payload.message) ? payload.message : (typeof payload === "string" ? payload : "Request failed");
    throw new Error(`${res.status} ${res.statusText} — ${msg}`);
  }
  return payload;
}

/* ====== UI rendering ====== */
function statusPill(status) {
  const s = String(status || "Unknown");
  const cls =
    s === "Available" ? "good" :
    s === "Problem" ? "bad" :
    s === "Unavailable" ? "warn" :
    s === "Reserved" ? "info" :
    s === "Cancelling" ? "warn" : "info";

  return `<span class="pill ${cls}"><span class="dot"></span>${escapeHtml(s)}</span>`;
}

function renderFacilities() {
  const grid = el("#facilitiesGrid");
  if (!state.facilities.length) {
    grid.innerHTML = `<div class="panel muted">No facilities loaded yet. Choose a town and click “Load Facilities”.</div>`;
    return;
  }

  grid.innerHTML = state.facilities.map(f => `
    <article class="card">
      <h3>${escapeHtml(f.name || "Facility")}</h3>
      <div class="meta">
        <span>${escapeHtml(f.town || "")}</span>
        <span>•</span>
        <span>${escapeHtml(f.address || "Address not provided")}</span>
      </div>
      <div class="row gap mt wrap">
        <span class="pill info"><span class="dot"></span>Facility ID: ${escapeHtml(f.facilityId || f.id || "")}</span>
        <button class="btn" data-action="select-facility" data-id="${escapeHtml(f.facilityId || f.id)}">View Units</button>
      </div>
    </article>
  `).join("");
}

function renderUnits() {
  const tbody = el("#unitsTbody");
  if (!state.units.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="muted">No units found for this facility/filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.units.map(u => {
    const canBook = u.status === "Available";
    return `
      <tr>
        <td>${escapeHtml(u.unitId || u.id)}</td>
        <td>${escapeHtml(u.type || "N/A")}</td>
        <td>${escapeHtml(u.size || "N/A")}</td>
        <td>${escapeHtml(u.pricePerDay ?? "—")}</td>
        <td>${statusPill(u.status)}</td>
        <td>
          <button class="btn ${canBook ? "" : "btn-ghost"}"
                  data-action="open-booking"
                  data-unit="${escapeHtml(u.unitId || u.id)}"
                  ${canBook ? "" : "disabled"}>
            Book
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function renderRentals() {
  const grid = el("#rentalsGrid");
  if (!state.rentals.length) {
    grid.innerHTML = `<div class="panel muted">No rentals found.</div>`;
    return;
  }

  grid.innerHTML = state.rentals.map(r => `
    <article class="card">
      <h3>Rental: ${escapeHtml(r.rentalId || r.id)}</h3>
      <div class="meta">
        <span>Facility: ${escapeHtml(r.facilityId)}</span>
        <span>•</span>
        <span>Unit: ${escapeHtml(r.unitId)}</span>
      </div>
      <div class="meta mt">
        <span>Billing: ${escapeHtml(r.billingOption || "—")}</span>
        <span>•</span>
        <span>Status: ${escapeHtml(r.status || "Active")}</span>
      </div>
      <div class="row gap mt wrap">
        <button class="btn btn-ghost" data-action="cancel-rental" data-rental="${escapeHtml(r.rentalId || r.id)}">
          Cancel rental
        </button>
      </div>
      <div class="help mt">Cancellation rules (notice periods) enforced by backend.</div>
    </article>
  `).join("");
}

function renderSecurityCards() {
  const grid = el("#securityGrid");
  if (!state.rentals.length) {
    grid.innerHTML = `<div class="panel muted">No rentals loaded.</div>`;
    return;
  }

  grid.innerHTML = state.rentals.map(r => `
    <article class="card">
      <h3>${escapeHtml(r.unitId)} <span class="muted">(${escapeHtml(r.facilityId)})</span></h3>
      <div class="meta">
        <span>Rental: ${escapeHtml(r.rentalId || r.id)}</span>
        <span>•</span>
        <span>Notify on open: ${escapeHtml(String(!!r.notifyOnOpen))}</span>
      </div>

      <div class="row gap mt wrap">
        <button class="btn" data-action="open-share" data-rental="${escapeHtml(r.rentalId || r.id)}">
          Share access
        </button>
        <button class="btn btn-ghost" data-action="toggle-notify" data-rental="${escapeHtml(r.rentalId || r.id)}">
          Toggle notifications
        </button>
      </div>
    </article>
  `).join("");
}

function renderSupportUnits(units) {
  const tbody = el("#supportTbody");
  if (!units?.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="muted">No units found.</td></tr>`;
    return;
  }

  tbody.innerHTML = units.map(u => `
    <tr>
      <td>${escapeHtml(u.unitId || u.id)}</td>
      <td>${escapeHtml(u.type || "—")}</td>
      <td>${escapeHtml(u.size || "—")}</td>
      <td>${statusPill(u.status)}</td>
      <td class="row gap wrap">
        <button class="btn btn-ghost" data-action="support-set-status" data-unit="${escapeHtml(u.unitId || u.id)}" data-status="Available">Available</button>
        <button class="btn btn-ghost" data-action="support-set-status" data-unit="${escapeHtml(u.unitId || u.id)}" data-status="Unavailable">Unavailable</button>
      </td>
    </tr>
  `).join("");
}

/* ====== API calls (map these to your backend) ====== */
async function loadFacilities() {
  const town = el("#townSelect").value;

  // Expected response example:
  // [{ facilityId, name, town, address }]
  const data = await apiFetch("/facilities", { query: { town } });
  state.facilities = Array.isArray(data) ? data : (data.items || []);
  renderFacilities();
}

async function selectFacility(facilityId) {
  state.selectedFacility = facilityId;
  el("#unitsPanel").hidden = false;
  el("#unitsTitle").textContent = `Units — Facility ${facilityId}`;
  await loadUnits();
}

async function loadUnits() {
  if (!state.selectedFacility) return;
  const status = el("#unitStatusFilter").value;

  // Expected response example:
  // [{ unitId, type, size, pricePerDay, status }]
  const data = await apiFetch(`/facilities/${encodeURIComponent(state.selectedFacility)}/units`, {
    query: { status }
  });
  state.units = Array.isArray(data) ? data : (data.items || []);
  renderUnits();
}

async function createBooking(payload) {
  // Expected request:
  // { facilityId, unitId, startDate, endDate?, billingOption, paymentMethod, discountCode? }
  // Expected response:
  // { rentalId, ... }
  const res = await apiFetch("/bookings", { method: "POST", body: payload });
  return res;
}

async function loadRentals() {
  // Expected response:
  // [{ rentalId, facilityId, unitId, billingOption, status, notifyOnOpen }]
  const data = await apiFetch("/me/rentals");
  state.rentals = Array.isArray(data) ? data : (data.items || []);
  renderRentals();
}

async function cancelRental(rentalId) {
  await apiFetch(`/rentals/${encodeURIComponent(rentalId)}/cancel`, { method: "POST" });
}

async function shareAccess(rentalId, payload) {
  // payload: { shareWith, from?, to? }
  await apiFetch(`/rentals/${encodeURIComponent(rentalId)}/share-access`, { method: "POST", body: payload });
}

async function toggleNotifications(rentalId) {
  // simplest: backend toggles. Alternatively send { enabled: true/false }
  await apiFetch(`/rentals/${encodeURIComponent(rentalId)}/notifications`, { method: "POST" });
}

async function supportListUnits(facilityId, status) {
  const data = await apiFetch(`/support/facilities/${encodeURIComponent(facilityId)}/units`, {
    query: { status }
  });
  return Array.isArray(data) ? data : (data.items || []);
}

async function supportSetUnitStatus(unitId, status) {
  await apiFetch(`/support/units/${encodeURIComponent(unitId)}/status`, {
    method: "PATCH",
    body: { status }
  });
}

/* ====== Modals ====== */
function openBookingModal(unitId) {
  const u = state.units.find(x => (x.unitId || x.id) === unitId);
  const facilityId = state.selectedFacility;

  el("#bookingFacilityId").value = facilityId;
  el("#bookingUnitId").value = unitId;

  el("#bookingMeta").textContent =
    `Facility: ${facilityId} • Unit: ${unitId} • ${u?.type || ""} ${u?.size ? `• ${u.size}` : ""}`;

  // default startDate = tomorrow (or today). Use today for simplicity.
  el("#startDate").valueAsDate = new Date();

  el("#endDate").value = "";
  el("#billingOption").value = "PREPAY";
  el("#paymentMethod").value = "CARD";
  el("#discountCode").value = "";

  el("#bookingDialog").showModal();
}

function openShareModal(rentalId) {
  el("#shareRentalId").value = rentalId;
  el("#shareMeta").textContent = `Rental: ${rentalId}`;
  el("#shareWith").value = "";
  el("#shareFrom").value = "";
  el("#shareTo").value = "";
  el("#shareDialog").showModal();
}

/* ====== Wiring ====== */
function bindTabs() {
  els(".tab").forEach(btn => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });
}

function bindSettings() {
  el("#btnOpenSettings").addEventListener("click", () => {
    el("#settingsPanel").scrollIntoView({ behavior: "smooth", block: "start" });
    el("#apiBaseUrl").focus();
  });

  el("#apiBaseUrl").value = settings.apiBaseUrl;
  el("#jwtToken").value = settings.jwtToken;

  el("#btnSaveSettings").addEventListener("click", () => {
    settings.apiBaseUrl = el("#apiBaseUrl").value.trim();
    settings.jwtToken = el("#jwtToken").value.trim();
    toast("good", "Saved", "API Base URL and token saved locally.");
  });

  el("#btnTestAuth").addEventListener("click", async () => {
    try {
      // Point this at any authenticated endpoint you have.
      // A good choice is: GET /me/rentals (even if empty)
      await apiFetch("/me/rentals");
      toast("good", "Auth OK", "Token accepted by API.");
    } catch (e) {
      toast("bad", "Auth failed", e.message);
    }
  });

  el("#btnLogout").addEventListener("click", () => {
    settings.jwtToken = "";
    el("#jwtToken").value = "";
    toast("good", "Logged out", "Token cleared.");
  });
}

function bindExplore() {
  el("#btnLoadFacilities").addEventListener("click", async () => {
    try {
      await loadFacilities();
      toast("good", "Loaded", "Facilities loaded.");
    } catch (e) {
      toast("bad", "Failed to load facilities", e.message);
    }
  });

  el("#btnLoadUnits").addEventListener("click", async () => {
    try {
      await loadUnits();
      toast("good", "Refreshed", "Units updated.");
    } catch (e) {
      toast("bad", "Failed to load units", e.message);
    }
  });

  el("#unitStatusFilter").addEventListener("change", () => loadUnits().catch(() => {}));

  el("#facilitiesGrid").addEventListener("click", (ev) => {
    const btn = ev.target.closest("button[data-action='select-facility']");
    if (!btn) return;
    selectFacility(btn.dataset.id).catch((e) => toast("bad", "Failed to select facility", e.message));
  });

  el("#unitsTbody").addEventListener("click", (ev) => {
    const btn = ev.target.closest("button[data-action='open-booking']");
    if (!btn) return;
    openBookingModal(btn.dataset.unit);
  });

  el("#bookingForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();

    const payload = {
      facilityId: el("#bookingFacilityId").value,
      unitId: el("#bookingUnitId").value,
      startDate: el("#startDate").value,
      endDate: el("#endDate").value || null,
      billingOption: el("#billingOption").value,
      paymentMethod: el("#paymentMethod").value,
      discountCode: el("#discountCode").value.trim() || null,
    };

    try {
      const res = await createBooking(payload);
      el("#bookingDialog").close();

      toast("good", "Booked", `Created rental ${res?.rentalId || "(see response)"}.`);
      // update units + rentals views
      await loadUnits();
    } catch (e) {
      toast("bad", "Booking failed", e.message);
    }
  });
}

function bindRentals() {
  el("#btnLoadRentals").addEventListener("click", async () => {
    try {
      await loadRentals();
      toast("good", "Loaded", "Rentals loaded.");
    } catch (e) {
      toast("bad", "Failed to load rentals", e.message);
    }
  });

  el("#rentalsGrid").addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-action='cancel-rental']");
    if (!btn) return;

    const rentalId = btn.dataset.rental;
    const ok = confirm(`Cancel rental ${rentalId}?`);
    if (!ok) return;

    try {
      await cancelRental(rentalId);
      toast("good", "Cancellation requested", "Rental moved into cancellation flow (if applicable).");
      await loadRentals();
    } catch (e) {
      toast("bad", "Cancel failed", e.message);
    }
  });
}

function bindSecurity() {
  el("#btnLoadSecurityRentals").addEventListener("click", async () => {
    try {
      await loadRentals();
      renderSecurityCards();
      toast("good", "Loaded", "Security units loaded.");
    } catch (e) {
      toast("bad", "Failed to load units", e.message);
    }
  });

  el("#securityGrid").addEventListener("click", async (ev) => {
    const shareBtn = ev.target.closest("button[data-action='open-share']");
    const toggleBtn = ev.target.closest("button[data-action='toggle-notify']");

    if (shareBtn) {
      openShareModal(shareBtn.dataset.rental);
      return;
    }

    if (toggleBtn) {
      try {
        await toggleNotifications(toggleBtn.dataset.rental);
        toast("good", "Updated", "Notification preference updated.");
        await loadRentals();
        renderSecurityCards();
      } catch (e) {
        toast("bad", "Failed", e.message);
      }
    }
  });

  el("#shareForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();

    const rentalId = el("#shareRentalId").value;
    const payload = {
      shareWith: el("#shareWith").value.trim(),
      from: el("#shareFrom").value || null,
      to: el("#shareTo").value || null,
    };

    try {
      await shareAccess(rentalId, payload);
      el("#shareDialog").close();
      toast("good", "Shared", "Access share created.");
    } catch (e) {
      toast("bad", "Share failed", e.message);
    }
  });
}

function bindSupport() {
  el("#btnSupportSearch").addEventListener("click", async () => {
    const facilityId = el("#supportFacilityId").value.trim();
    const status = el("#supportStatus").value;
    if (!facilityId) {
      toast("bad", "Missing facility", "Enter a Facility ID.");
      return;
    }

    try {
      const units = await supportListUnits(facilityId, status);
      renderSupportUnits(units);
      toast("good", "Loaded", `Found ${units.length} unit(s).`);
    } catch (e) {
      toast("bad", "Support search failed", e.message);
    }
  });

  el("#supportTbody").addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-action='support-set-status']");
    if (!btn) return;

    const unitId = btn.dataset.unit;
    const status = btn.dataset.status;

    try {
      await supportSetUnitStatus(unitId, status);
      toast("good", "Updated", `Unit ${unitId} set to ${status}.`);
      // re-run current search
      el("#btnSupportSearch").click();
    } catch (e) {
      toast("bad", "Update failed", e.message);
    }
  });
}

function bindAuthButtons() {
  document.querySelector("#btnSignIn").addEventListener("click", () => Auth.signInRedirect());
  document.querySelector("#btnSignUp").addEventListener("click", () => Auth.signUpRedirect());
  document.querySelector("#btnSignOut").addEventListener("click", () => Auth.signOutRedirect());
}

/* ====== Init ====== */
async function init() {
  bindTabs();
  bindAuthButtons();
  bindExplore();
  bindRentals();
  bindSecurity();
  bindSupport();

  setView("explore");

  // If returning from Cognito with ?code=...
  try {
    await Auth.handleRedirectCallback();
  } catch (e) {
    console.error(e);
    Auth.clearTokens();
    Auth.signInRedirect();
    return;
  }

  // If not logged in, go to Hosted UI
  if (!Auth.isAuthenticated()) {
    Auth.signInRedirect();
    return;
  }

  // Logged in → show storage options immediately
  await loadFacilities();
}

init();