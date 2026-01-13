import { CONFIG } from "./config.js";
import { getAccessToken, isSignedIn } from "./auth.js";

function qs(params = {}) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    u.set(k, v);
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}

async function request(path, { method="GET", query, body } = {}) {
  const url = CONFIG.apiBaseUrl + path + qs(query);

  const headers = { "Content-Type": "application/json" };
  if (isSignedIn()) headers.Authorization = `Bearer ${getAccessToken()}`;

  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  if (res.status === 204) return null;

  const contentType = res.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await res.json().catch(() => null)
    : await res.text().catch(() => "");

  if (!res.ok) {
    const msg = typeof payload === "string" ? payload : (payload?.message || JSON.stringify(payload));
    const err = new Error(`API ${method} ${path} failed (${res.status}): ${msg}`);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }

  return payload;
}

/* ---------------- Mock data (so UI works immediately) ---------------- */

const MOCK = {
  units: [
    { unit_id: "CPT-CT-001", town: "Cape Town", facility_id: "CPT-01", facility_name: "Cape Town Central", size: "LOCKER", status: "Available", price_per_day: 29 },
    { unit_id: "CPT-CT-101", town: "Cape Town", facility_id: "CPT-01", facility_name: "Cape Town Central", size: "MEDIUM", status: "Reserved", price_per_day: 119 },
    { unit_id: "JHB-SB-009", town: "Johannesburg", facility_id: "JHB-02", facility_name: "Sandton Secure", size: "SMALL", status: "Available", price_per_day: 69 },
    { unit_id: "JHB-SB-210", town: "Johannesburg", facility_id: "JHB-02", facility_name: "Sandton Secure", size: "GARAGE", status: "Unavailable", price_per_day: 249 },
    { unit_id: "DBN-UM-014", town: "Durban", facility_id: "DBN-01", facility_name: "Umhlanga Access", size: "MEDIUM", status: "Problem", price_per_day: 109 },
    { unit_id: "DBN-UM-015", town: "Durban", facility_id: "DBN-01", facility_name: "Umhlanga Access", size: "LOCKER", status: "Available", price_per_day: 25 }
  ],
  bookings: [
    // { booking_id: "BKG-001", unit_id: "CPT-CT-001", facility_name: "Cape Town Central", start_date: "2025-01-02", end_date: "", billing: "PREPAY", status: "Active" }
  ]
};

function mockFilterUnits({ town, size, status, search, facilityId } = {}) {
  const s = (search || "").toLowerCase().trim();
  return MOCK.units.filter(u => {
    if (town && u.town !== town) return false;
    if (facilityId && u.facility_id !== facilityId) return false;
    if (size && u.size !== size) return false;
    if (status && u.status !== status) return false;
    if (s) {
      const hay = `${u.unit_id} ${u.facility_name} ${u.town}`.toLowerCase();
      if (!hay.includes(s)) return false;
    }
    return true;
  });
}

/* ---------------- Public API used by UI ---------------- */

export const Api = {
  async health() {
    if (CONFIG.enableMockData) return { ok: true };
    return request(CONFIG.endpoints.health);
  },

  async listUnits(filters = {}) {
    if (CONFIG.enableMockData) return mockFilterUnits(filters);
    return request(CONFIG.endpoints.listUnits, { query: filters });
  },

  async createBooking(payload) {
    if (CONFIG.enableMockData) {
      const booking_id = `BKG-${String(Math.floor(Math.random()*999999)).padStart(6,"0")}`;
      const unit = MOCK.units.find(u => u.unit_id === payload.unit_id);
      if (!unit) throw new Error("Unit not found");
      if (unit.status !== "Available") throw new Error("Unit is not available");

      unit.status = "Reserved";
      const rec = {
        booking_id,
        unit_id: unit.unit_id,
        facility_name: unit.facility_name,
        start_date: payload.start_date,
        end_date: payload.end_date || "",
        billing: payload.billing_option,
        status: "Active"
      };
      MOCK.bookings.unshift(rec);
      return rec;
    }

    return request(CONFIG.endpoints.createBooking, { method: "POST", body: payload });
  },

  async listBookings() {
    if (CONFIG.enableMockData) return MOCK.bookings;
    return request(CONFIG.endpoints.listBookings);
  },

  async cancelBooking(bookingId) {
    if (CONFIG.enableMockData) {
      const b = MOCK.bookings.find(x => x.booking_id === bookingId);
      if (!b) throw new Error("Booking not found");
      b.status = "Cancelling";
      const unit = MOCK.units.find(u => u.unit_id === b.unit_id);
      if (unit) unit.status = "Cancelling";
      return b;
    }

    return request(CONFIG.endpoints.cancelBooking(bookingId), { method: "POST" });
  },

  async supportListUnits({ facilityId, status } = {}) {
    if (CONFIG.enableMockData) return mockFilterUnits({ facilityId, status });
    return request(CONFIG.endpoints.supportListUnits, { query: { facilityId, status } });
  },

  async supportToggleAvailability(unitId, makeAvailable) {
    if (CONFIG.enableMockData) {
      const u = MOCK.units.find(x => x.unit_id === unitId);
      if (!u) throw new Error("Unit not found");
      u.status = makeAvailable ? "Available" : "Unavailable";
      return u;
    }

    return request(CONFIG.endpoints.supportToggleUnit(unitId), {
      method: "PATCH",
      body: { status: makeAvailable ? "Available" : "Unavailable" }
    });
  }
};