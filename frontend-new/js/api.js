/**
 * API Service Module - HTTP client for backend APIs
 */

import { CONFIG } from '../config.js';
import { getAccessToken } from './auth.js';

/**
 * Make an API request
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${CONFIG.apiBaseUrl}${endpoint}`;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization header if authenticated
  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || `HTTP error ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * GET request
 */
async function get(endpoint, params = {}) {
  const queryString = new URLSearchParams(params).toString();
  const url = queryString ? `${endpoint}?${queryString}` : endpoint;
  return apiRequest(url, { method: 'GET' });
}

/**
 * POST request
 */
async function post(endpoint, body = {}) {
  return apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * PUT request
 */
async function put(endpoint, body = {}) {
  return apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

/**
 * DELETE request
 */
async function del(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}

// ============================================
// Public API - Facilities
// ============================================

/**
 * Get all facilities, optionally filtered by city
 */
export async function getFacilities(city = null) {
  const params = city ? { city } : {};
  return get('/facilities', params);
}

/**
 * Get available units for a facility
 */
export async function getFacilityAvailability(facilityId) {
  return get(`/facilities/${facilityId}/availability`);
}

// ============================================
// Public API - Units
// ============================================

/**
 * Get unit details
 */
export async function getUnitDetails(unitId) {
  return get(`/units/${unitId}`);
}

/**
 * Get unit pricing
 */
export async function getUnitPricing(unitId) {
  return get(`/units/${unitId}/pricing`);
}

// ============================================
// Authenticated API - Rentals
// ============================================

/**
 * Get user's rentals
 */
export async function getUserRentals() {
  return get('/rentals');
}

/**
 * Create a new rental
 */
export async function createRental(unitId, paymentMethodId, rentalType = 'subscription') {
  return post('/rentals', {
    unit_id: unitId,
    payment_method_id: paymentMethodId,
    rental_type: rentalType,
  });
}

/**
 * Cancel/delete a rental
 */
export async function deleteRental(rentalId) {
  return del(`/rentals/${rentalId}`);
}

// ============================================
// Authenticated API - Payment Methods
// ============================================

/**
 * Get user's payment methods
 */
export async function getPaymentMethods() {
  return get('/payment-methods');
}

/**
 * Create or update a payment method
 */
export async function upsertPaymentMethod(paymentData) {
  return post('/payment-methods', paymentData);
}

// ============================================
// Authenticated API - Invoices
// ============================================

/**
 * Get user's invoices
 */
export async function getInvoices(status = null) {
  const params = status ? { status } : {};
  return get('/invoices', params);
}

// ============================================
// Authenticated API - Unit Sharing
// ============================================

/**
 * Share unit access with another user
 */
export async function shareUnitAccess(unitId, email) {
  return post(`/units/${unitId}/share`, { email });
}

/**
 * Get users with shared access to a unit
 */
export async function getSharedUsers(unitId) {
  return get(`/units/${unitId}/shared-users`);
}

/**
 * Request access to a unit
 */
export async function requestUnitAccess(unitId, message = '') {
  return post(`/units/${unitId}/request-access`, { message });
}

/**
 * Get share requests for user's units
 */
export async function getShareRequests() {
  return get('/share-requests');
}

/**
 * Approve or deny a share request
 */
export async function updateShareRequest(requestId, status) {
  return put(`/share-requests/${requestId}`, { status });
}

// ============================================
// API - Access Control
// ============================================

/**
 * Check/verify access to a unit (for IoT integration)
 */
export async function checkAccess(unitId, userId) {
  return post('/access-control', {
    unit_id: unitId,
    user_id: userId,
  });
}
