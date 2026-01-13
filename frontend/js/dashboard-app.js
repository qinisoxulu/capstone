import { CognitoAuth } from './cognito-auth.js';
import { Api } from './api-client.js';
import { CONFIG } from './config.js';

// ==================== Utility Functions ====================

const el = (selector) => document.querySelector(selector);
const els = (selector) => Array.from(document.querySelectorAll(selector));

function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'info') {
  // Simple toast notification (you can enhance this)
  alert(`${type.toUpperCase()}: ${message}`);
}

function showElement(element) {
  element.classList.remove('hidden');
}

function hideElement(element) {
  element.classList.add('hidden');
}

// ==================== State Management ====================

const state = {
  currentView: 'explore',
  facilities: [],
  units: [],
  rentals: [],
  shareRequests: [],
  invoices: [],
  paymentMethods: [],
  currentUnit: null,
  currentRental: null
};

// ==================== View Management ====================

function setView(viewName) {
  state.currentView = viewName;

  // Update tab styles
  els('.tab').forEach(tab => {
    if (tab.dataset.view === viewName) {
      tab.classList.add('is-active');
    } else {
      tab.classList.remove('is-active');
    }
  });

  // Show/hide views
  els('.view').forEach(view => {
    if (view.id === `view${viewName.charAt(0).toUpperCase() + viewName.slice(1)}`) {
      showElement(view);
    } else {
      hideElement(view);
    }
  });

  // Load data for the view
  loadViewData(viewName);
}

async function loadViewData(viewName) {
  try {
    switch (viewName) {
      case 'explore':
        await loadFacilities();
        break;
      case 'rentals':
        await loadRentals();
        break;
      case 'sharing':
        await loadShareRequests();
        break;
      case 'invoices':
        await loadInvoices();
        break;
      case 'payment':
        await loadPaymentMethods();
        break;
    }
  } catch (error) {
    console.error(`Error loading ${viewName} data:`, error);
    showToast(error.message, 'error');
  }
}

// ==================== Facilities & Units ====================

async function loadFacilities(city = null) {
  try {
    const facilities = await Api.getFacilities(city);
    state.facilities = Array.isArray(facilities) ? facilities : facilities.facilities || [];
    renderFacilities();
  } catch (error) {
    console.error('Error loading facilities:', error);
    showToast('Failed to load facilities: ' + error.message, 'error');
  }
}

function renderFacilities() {
  const grid = el('#unitsGrid');
  const empty = el('#unitsEmpty');

  if (!state.facilities.length) {
    hideElement(grid);
    showElement(empty);
    grid.innerHTML = '';
    return;
  }

  showElement(grid);
  hideElement(empty);

  // For now, show facilities and their units
  // You may need to call getFacilityAvailability for each facility
  grid.innerHTML = '<div class="empty">Loading units from facilities...</div>';

  // Load units from all facilities
  loadAllUnits();
}

async function loadAllUnits() {
  const grid = el('#unitsGrid');

  try {
    // Aggregate units from all facilities
    let allUnits = [];

    for (const facility of state.facilities) {
      try {
        const availability = await Api.getFacilityAvailability(facility.facility_id || facility.id);
        const units = Array.isArray(availability) ? availability : availability.units || [];

        // Add facility info to each unit
        units.forEach(unit => {
          unit.facility_name = facility.name || facility.facility_name;
          unit.facility_id = facility.facility_id || facility.id;
          unit.city = facility.city || facility.town;
        });

        allUnits = allUnits.concat(units);
      } catch (err) {
        console.error(`Failed to load units for facility ${facility.facility_id}:`, err);
      }
    }

    state.units = allUnits;
    renderUnits();
  } catch (error) {
    console.error('Error loading units:', error);
    grid.innerHTML = `<div class="empty">Error loading units: ${escapeHtml(error.message)}</div>`;
  }
}

async function searchUnits() {
  const town = el('#fTown').value.trim();
  const size = el('#fSize').value;
  const status = el('#fStatus').value;
  const search = el('#fSearch').value.trim().toLowerCase();

  // First load facilities
  if (town) {
    await loadFacilities(town);
  } else {
    await loadFacilities();
  }

  // Filter units based on criteria
  let filtered = state.units;

  if (size) {
    filtered = filtered.filter(u => u.size === size);
  }

  if (status) {
    filtered = filtered.filter(u => u.status === status);
  }

  if (search) {
    filtered = filtered.filter(u => {
      const searchable = `${u.unit_id} ${u.facility_name} ${u.city}`.toLowerCase();
      return searchable.includes(search);
    });
  }

  state.units = filtered;
  renderUnits();
}

function renderUnits() {
  const grid = el('#unitsGrid');
  const empty = el('#unitsEmpty');

  if (!state.units.length) {
    hideElement(grid);
    showElement(empty);
    grid.innerHTML = '';
    return;
  }

  showElement(grid);
  hideElement(empty);

  grid.innerHTML = state.units.map(unit => `
    <div class="unit">
      <div class="unit__top">
        <div>
          <div class="unit__title">${escapeHtml(unit.unit_id || unit.id)}</div>
          <div class="unit__meta">${escapeHtml(unit.facility_name || 'Facility')} • ${escapeHtml(unit.city || '')}</div>
        </div>
        <span class="badge badge--${escapeHtml(unit.status || 'Unknown')}">${escapeHtml(unit.status || 'Unknown')}</span>
      </div>
      <div class="unit__row">
        <span>Size: ${escapeHtml(unit.size || 'N/A')}</span>
        <span class="strong">R${escapeHtml(unit.price_per_day || unit.price || '—')}/day</span>
      </div>
      <div class="unit__actions">
        <button class="btn btn-primary" onclick="window.openBookModal('${escapeHtml(unit.unit_id || unit.id)}')" ${unit.status !== 'Available' ? 'disabled' : ''}>
          Book now
        </button>
        <button class="btn btn-ghost" onclick="window.viewUnitDetails('${escapeHtml(unit.unit_id || unit.id)}')">
          Details
        </button>
      </div>
    </div>
  `).join('');
}

// ==================== Rentals ====================

async function loadRentals() {
  try {
    const rentals = await Api.getUserRentals();
    state.rentals = Array.isArray(rentals) ? rentals : rentals.rentals || [];
    renderRentals();
  } catch (error) {
    console.error('Error loading rentals:', error);
    showToast('Failed to load rentals: ' + error.message, 'error');
  }
}

function renderRentals() {
  const list = el('#rentalsList');
  const empty = el('#rentalsEmpty');

  if (!state.rentals.length) {
    hideElement(list);
    showElement(empty);
    list.innerHTML = '';
    return;
  }

  showElement(list);
  hideElement(empty);

  list.innerHTML = state.rentals.map(rental => `
    <div class="item">
      <div>
        <div class="item__title">Rental: ${escapeHtml(rental.rental_id || rental.id)}</div>
        <div class="item__meta">
          Unit: ${escapeHtml(rental.unit_id)} •
          Start: ${escapeHtml(rental.start_date)} •
          Billing: ${escapeHtml(rental.billing_option || 'N/A')}
        </div>
      </div>
      <div class="item__actions">
        <button class="btn btn-ghost" onclick="window.shareRentalAccess('${escapeHtml(rental.rental_id || rental.id)}', '${escapeHtml(rental.unit_id)}')">
          Share
        </button>
        <button class="btn btn-ghost" onclick="window.cancelRental('${escapeHtml(rental.rental_id || rental.id)}')">
          Cancel
        </button>
      </div>
    </div>
  `).join('');
}

async function cancelRental(rentalId) {
  if (!confirm('Are you sure you want to cancel this rental?')) {
    return;
  }

  try {
    await Api.deleteRental(rentalId);
    showToast('Rental cancelled successfully', 'success');
    await loadRentals();
  } catch (error) {
    console.error('Error cancelling rental:', error);
    showToast('Failed to cancel rental: ' + error.message, 'error');
  }
}

// ==================== Booking ====================

async function openBookModal(unitId) {
  state.currentUnit = state.units.find(u => (u.unit_id || u.id) === unitId);

  if (!state.currentUnit) {
    // Try to fetch unit details
    try {
      state.currentUnit = await Api.getUnitDetails(unitId);
    } catch (error) {
      showToast('Failed to load unit details', 'error');
      return;
    }
  }

  // Update modal info
  el('#bookUnitMeta').textContent = `Unit: ${unitId} • ${state.currentUnit.size || 'N/A'} • ${state.currentUnit.facility_name || ''}`;

  // Set default start date to today
  const today = new Date().toISOString().split('T')[0];
  el('#startDate').value = today;
  el('#endDate').value = '';
  el('#billingOption').value = 'RECURRING_MONTHLY';

  // Load payment methods for dropdown
  await loadPaymentMethodsForBooking();

  // Show modal
  el('#bookModal').showModal();
}

async function loadPaymentMethodsForBooking() {
  try {
    const methods = await Api.getPaymentMethods();
    state.paymentMethods = Array.isArray(methods) ? methods : methods.payment_methods || [];

    const select = el('#paymentMethodSelect');
    select.innerHTML = '<option value="">Select payment method</option>' +
      state.paymentMethods.map(pm => `
        <option value="${escapeHtml(pm.payment_method_id || pm.id)}">
          ${escapeHtml(pm.type || 'Card')} •••• ${escapeHtml(pm.last_four || '****')}
          ${pm.is_default ? ' (Default)' : ''}
        </option>
      `).join('');
  } catch (error) {
    console.error('Error loading payment methods:', error);
  }
}

async function submitBooking(event) {
  event.preventDefault();

  const payload = {
    unit_id: state.currentUnit.unit_id || state.currentUnit.id,
    start_date: el('#startDate').value,
    end_date: el('#endDate').value || null,
    billing_option: el('#billingOption').value,
    payment_method_id: el('#paymentMethodSelect').value
  };

  try {
    hideElement(el('#modalError'));
    hideElement(el('#modalOk'));

    const result = await Api.createRental(payload);

    showElement(el('#modalOk'));
    el('#modalOk').textContent = `Booking created successfully! Rental ID: ${result.rental_id || result.id || 'N/A'}`;

    setTimeout(() => {
      el('#bookModal').close();
      loadRentals();
    }, 2000);
  } catch (error) {
    console.error('Error creating booking:', error);
    showElement(el('#modalError'));
    el('#modalError').textContent = `Failed to create booking: ${error.message}`;
  }
}

// ==================== Sharing ====================

async function loadShareRequests() {
  try {
    const requests = await Api.getShareRequests();
    state.shareRequests = Array.isArray(requests) ? requests : requests.requests || [];
    renderShareRequests();
  } catch (error) {
    console.error('Error loading share requests:', error);
    showToast('Failed to load share requests: ' + error.message, 'error');
  }
}

function renderShareRequests() {
  const list = el('#shareRequestsList');
  const empty = el('#shareRequestsEmpty');

  if (!state.shareRequests.length) {
    hideElement(list);
    showElement(empty);
    list.innerHTML = '';
    return;
  }

  showElement(list);
  hideElement(empty);

  list.innerHTML = state.shareRequests.map(request => `
    <div class="item">
      <div>
        <div class="item__title">Request from: ${escapeHtml(request.requester_user_id || 'User')}</div>
        <div class="item__meta">
          Unit: ${escapeHtml(request.unit_id)} •
          Status: ${escapeHtml(request.status || 'pending')} •
          ${escapeHtml(request.message || 'No message')}
        </div>
      </div>
      <div class="item__actions">
        ${request.status === 'pending' ? `
          <button class="btn btn-primary" onclick="window.approveShareRequest('${escapeHtml(request.request_id || request.id)}', 'approved')">
            Approve
          </button>
          <button class="btn btn-ghost" onclick="window.approveShareRequest('${escapeHtml(request.request_id || request.id)}', 'rejected')">
            Reject
          </button>
        ` : `<span class="badge">${escapeHtml(request.status)}</span>`}
      </div>
    </div>
  `).join('');
}

async function approveShareRequest(requestId, status) {
  try {
    await Api.updateShareRequest(requestId, { status });
    showToast(`Share request ${status}`, 'success');
    await loadShareRequests();
  } catch (error) {
    console.error('Error updating share request:', error);
    showToast('Failed to update share request: ' + error.message, 'error');
  }
}

async function requestUnitAccess() {
  const unitId = el('#requestUnitId').value.trim();
  const message = el('#requestMessage').value.trim();

  if (!unitId) {
    showToast('Please enter a unit ID', 'error');
    return;
  }

  try {
    await Api.requestUnitAccess(unitId, { message });
    showToast('Access request sent successfully', 'success');
    el('#requestUnitId').value = '';
    el('#requestMessage').value = '';
  } catch (error) {
    console.error('Error requesting access:', error);
    showToast('Failed to request access: ' + error.message, 'error');
  }
}

function shareRentalAccess(rentalId, unitId) {
  state.currentRental = { rentalId, unitId };
  el('#shareUnitMeta').textContent = `Unit: ${unitId} • Rental: ${rentalId}`;
  el('#shareModal').showModal();
}

async function submitShareAccess(event) {
  event.preventDefault();

  const payload = {
    shared_with_user_id: el('#shareWithUserId').value.trim(),
    permissions: el('#sharePermissions').value
  };

  try {
    hideElement(el('#shareModalError'));
    hideElement(el('#shareModalOk'));

    await Api.shareUnitAccess(state.currentRental.unitId, payload);

    showElement(el('#shareModalOk'));
    el('#shareModalOk').textContent = 'Access shared successfully!';

    setTimeout(() => {
      el('#shareModal').close();
    }, 2000);
  } catch (error) {
    console.error('Error sharing access:', error);
    showElement(el('#shareModalError'));
    el('#shareModalError').textContent = `Failed to share access: ${error.message}`;
  }
}

// ==================== Invoices ====================

async function loadInvoices() {
  try {
    const invoices = await Api.getInvoices();
    state.invoices = Array.isArray(invoices) ? invoices : invoices.invoices || [];
    renderInvoices();
  } catch (error) {
    console.error('Error loading invoices:', error);
    showToast('Failed to load invoices: ' + error.message, 'error');
  }
}

function renderInvoices() {
  const list = el('#invoicesList');
  const empty = el('#invoicesEmpty');

  if (!state.invoices.length) {
    hideElement(list);
    showElement(empty);
    list.innerHTML = '';
    return;
  }

  showElement(list);
  hideElement(empty);

  list.innerHTML = state.invoices.map(invoice => `
    <div class="item">
      <div>
        <div class="item__title">Invoice: ${escapeHtml(invoice.invoice_id || invoice.id)}</div>
        <div class="item__meta">
          Rental: ${escapeHtml(invoice.rental_id)} •
          Amount: R${escapeHtml(invoice.amount || 0)} •
          Status: ${escapeHtml(invoice.status || 'pending')}
        </div>
      </div>
      <div class="item__actions">
        <span class="badge badge--${escapeHtml(invoice.status || 'pending')}">${escapeHtml(invoice.status || 'pending')}</span>
      </div>
    </div>
  `).join('');
}

// ==================== Payment Methods ====================

async function loadPaymentMethods() {
  try {
    const methods = await Api.getPaymentMethods();
    state.paymentMethods = Array.isArray(methods) ? methods : methods.payment_methods || [];
    renderPaymentMethods();
  } catch (error) {
    console.error('Error loading payment methods:', error);
    showToast('Failed to load payment methods: ' + error.message, 'error');
  }
}

function renderPaymentMethods() {
  const list = el('#paymentsList');
  const empty = el('#paymentsEmpty');

  if (!state.paymentMethods.length) {
    hideElement(list);
    showElement(empty);
    list.innerHTML = '';
    return;
  }

  showElement(list);
  hideElement(empty);

  list.innerHTML = state.paymentMethods.map(pm => `
    <div class="item">
      <div>
        <div class="item__title">${escapeHtml(pm.type || 'Card')} •••• ${escapeHtml(pm.last_four || '****')}</div>
        <div class="item__meta">
          ${pm.is_default ? '<strong>Default payment method</strong>' : ''}
        </div>
      </div>
    </div>
  `).join('');
}

async function submitPaymentMethod(event) {
  event.preventDefault();

  const payload = {
    type: el('#paymentType').value,
    last_four: el('#paymentLastFour').value,
    is_default: el('#paymentIsDefault').checked
  };

  try {
    hideElement(el('#paymentModalError'));
    hideElement(el('#paymentModalOk'));

    await Api.upsertPaymentMethod(payload);

    showElement(el('#paymentModalOk'));
    el('#paymentModalOk').textContent = 'Payment method added successfully!';

    setTimeout(() => {
      el('#paymentModal').close();
      loadPaymentMethods();
    }, 2000);
  } catch (error) {
    console.error('Error adding payment method:', error);
    showElement(el('#paymentModalError'));
    el('#paymentModalError').textContent = `Failed to add payment method: ${error.message}`;
  }
}

// ==================== Unit Details ====================

async function viewUnitDetails(unitId) {
  try {
    const details = await Api.getUnitDetails(unitId);
    const pricing = await Api.getUnitPricing(unitId);

    alert(`Unit Details:\n\nUnit ID: ${details.unit_id}\nSize: ${details.size}\nStatus: ${details.status}\n\nPricing:\nDaily: R${pricing.price_per_day || 'N/A'}\nMonthly: R${pricing.price_per_month || 'N/A'}`);
  } catch (error) {
    console.error('Error fetching unit details:', error);
    showToast('Failed to load unit details: ' + error.message, 'error');
  }
}

// ==================== Initialization ====================

async function init() {
  try {
    // Handle OAuth callback
    const isCallback = await CognitoAuth.handleCallback();

    // Check if authenticated
    if (!CognitoAuth.isAuthenticated()) {
      // Redirect to login
      CognitoAuth.login();
      return;
    }

    // Display user info
    const userInfo = CognitoAuth.getUserInfo();
    if (userInfo) {
      el('#userName').textContent = userInfo.name || userInfo.email;
      el('#userEmail').textContent = userInfo.email;
    }

    // Display API URL
    el('#apiStatus').textContent = Api.getBaseUrl();
    el('#apiUrlInput').value = Api.getBaseUrl();

    // Set up event listeners
    setupEventListeners();

    // Load initial view
    setView('explore');

  } catch (error) {
    console.error('Initialization error:', error);
    showToast('Failed to initialize: ' + error.message, 'error');
  }
}

function setupEventListeners() {
  // Tab navigation
  els('.tab').forEach(tab => {
    tab.addEventListener('click', () => setView(tab.dataset.view));
  });

  // Hero buttons
  el('#btnGoExplore').addEventListener('click', () => setView('explore'));
  el('#btnGoRentals').addEventListener('click', () => setView('rentals'));

  // Logout
  el('#btnLogout').addEventListener('click', () => CognitoAuth.logout());

  // API URL update
  el('#btnUpdateApi').addEventListener('click', () => {
    const newUrl = el('#apiUrlInput').value.trim();
    if (newUrl) {
      Api.updateBaseUrl(newUrl);
      el('#apiStatus').textContent = newUrl;
      showToast('API URL updated', 'success');
    }
  });

  // Explore view
  el('#btnSearchUnits').addEventListener('click', () => searchUnits());
  el('#btnRefreshUnits').addEventListener('click', () => loadAllUnits());

  // Rentals view
  el('#btnRefreshRentals').addEventListener('click', () => loadRentals());

  // Sharing view
  el('#btnRefreshShareRequests').addEventListener('click', () => loadShareRequests());
  el('#btnRequestAccess').addEventListener('click', () => requestUnitAccess());

  // Invoices view
  el('#btnRefreshInvoices').addEventListener('click', () => loadInvoices());

  // Payment view
  el('#btnRefreshPayments').addEventListener('click', () => loadPaymentMethods());
  el('#btnAddPayment').addEventListener('click', () => el('#paymentModal').showModal());

  // Modal close buttons
  el('#btnCloseBookModal').addEventListener('click', () => el('#bookModal').close());
  el('#btnCloseShareModal').addEventListener('click', () => el('#shareModal').close());
  el('#btnClosePaymentModal').addEventListener('click', () => el('#paymentModal').close());

  // Form submissions
  el('#bookForm').addEventListener('submit', submitBooking);
  el('#shareForm').addEventListener('submit', submitShareAccess);
  el('#paymentForm').addEventListener('submit', submitPaymentMethod);
}

// ==================== Global Functions ====================
// Expose functions to window for onclick handlers
window.openBookModal = openBookModal;
window.viewUnitDetails = viewUnitDetails;
window.cancelRental = cancelRental;
window.shareRentalAccess = shareRentalAccess;
window.approveShareRequest = approveShareRequest;

// Start the application
init();
