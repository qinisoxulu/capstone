import { CONFIG } from './config.js';
import { CognitoAuth } from './cognito-auth.js';

/**
 * API Client for all backend Lambda functions
 */
class APIClient {
  constructor() {
    this.baseUrl = CONFIG.apiBaseUrl;
  }

  /**
   * Make an authenticated API request
   */
  async request(path, options = {}) {
    const { method = 'GET', body, queryParams } = options;

    // Build URL with query parameters
    let url = this.baseUrl + path;
    if (queryParams) {
      const params = new URLSearchParams();
      Object.entries(queryParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value);
        }
      });
      const queryString = params.toString();
      if (queryString) {
        url += '?' + queryString;
      }
    }

    // Prepare headers
    const headers = {
      'Content-Type': 'application/json'
    };

    // Add authorization header
    if (CognitoAuth.isAuthenticated()) {
      const accessToken = CognitoAuth.getAccessToken();
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    // Make request
    const fetchOptions = {
      method,
      headers
    };

    if (body && method !== 'GET') {
      fetchOptions.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, fetchOptions);

      // Handle 401 - try to refresh token
      if (response.status === 401) {
        try {
          await CognitoAuth.refreshAccessToken();
          // Retry request with new token
          headers['Authorization'] = `Bearer ${CognitoAuth.getAccessToken()}`;
          const retryResponse = await fetch(url, fetchOptions);
          return await this.handleResponse(retryResponse);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          CognitoAuth.login();
          throw new Error('Session expired. Please log in again.');
        }
      }

      return await this.handleResponse(response);
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Handle API response
   */
  async handleResponse(response) {
    const contentType = response.headers.get('content-type');

    let data;
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const message = typeof data === 'object' && data.message
        ? data.message
        : typeof data === 'string'
        ? data
        : 'Request failed';

      const error = new Error(`${response.status}: ${message}`);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  // ==================== Facilities ====================

  /**
   * GET /facilities - List all facilities or filter by city
   */
  async getFacilities(city = null) {
    const queryParams = city ? { city } : {};
    return this.request('/facilities', { queryParams });
  }

  /**
   * GET /facilities/{facility_id}/availability - Get available units for a facility
   */
  async getFacilityAvailability(facilityId) {
    return this.request(`/facilities/${encodeURIComponent(facilityId)}/availability`);
  }

  // ==================== Units ====================

  /**
   * GET /units/{unit_id} - Get unit details
   */
  async getUnitDetails(unitId) {
    return this.request(`/units/${encodeURIComponent(unitId)}`);
  }

  /**
   * GET /units/{unit_id}/pricing - Get unit pricing information
   */
  async getUnitPricing(unitId) {
    return this.request(`/units/${encodeURIComponent(unitId)}/pricing`);
  }

  /**
   * GET /units/{unit_id}/shared-users - Get list of users who have access to this unit
   */
  async getSharedUsers(unitId) {
    return this.request(`/units/${encodeURIComponent(unitId)}/shared-users`);
  }

  /**
   * POST /units/{unit_id}/share - Share unit access with another user
   * @param {string} unitId
   * @param {object} payload - { shared_with_user_id, permissions }
   */
  async shareUnitAccess(unitId, payload) {
    return this.request(`/units/${encodeURIComponent(unitId)}/share`, {
      method: 'POST',
      body: payload
    });
  }

  /**
   * POST /units/{unit_id}/request-access - Request access to a unit
   * @param {string} unitId
   * @param {object} payload - { message }
   */
  async requestUnitAccess(unitId, payload = {}) {
    return this.request(`/units/${encodeURIComponent(unitId)}/request-access`, {
      method: 'POST',
      body: payload
    });
  }

  // ==================== Rentals ====================

  /**
   * GET /rentals - Get user's rentals
   * @param {string} userId - Optional user ID (defaults to current user from token)
   */
  async getUserRentals(userId = null) {
    const queryParams = userId ? { user_id: userId } : {};
    return this.request('/rentals', { queryParams });
  }

  /**
   * POST /rentals - Create a new rental
   * @param {object} payload - { unit_id, start_date, end_date, billing_option, payment_method_id }
   */
  async createRental(payload) {
    return this.request('/rentals', {
      method: 'POST',
      body: payload
    });
  }

  /**
   * DELETE /rentals/{rental_id} - Cancel/delete a rental
   */
  async deleteRental(rentalId) {
    return this.request(`/rentals/${encodeURIComponent(rentalId)}`, {
      method: 'DELETE'
    });
  }

  // ==================== Share Requests ====================

  /**
   * GET /share-requests - Get share requests for current user
   * @param {string} status - Optional filter: 'pending', 'approved', 'rejected'
   */
  async getShareRequests(status = null) {
    const queryParams = status ? { status } : {};
    return this.request('/share-requests', { queryParams });
  }

  /**
   * PUT /share-requests/{request_id} - Approve or reject a share request
   * @param {string} requestId
   * @param {object} payload - { status: 'approved' or 'rejected' }
   */
  async updateShareRequest(requestId, payload) {
    return this.request(`/share-requests/${encodeURIComponent(requestId)}`, {
      method: 'PUT',
      body: payload
    });
  }

  // ==================== Invoices ====================

  /**
   * GET /invoices - Get invoices for user
   * @param {object} filters - { user_id, status, from_date, to_date }
   */
  async getInvoices(filters = {}) {
    return this.request('/invoices', { queryParams: filters });
  }

  // ==================== Payment Methods ====================

  /**
   * GET /payment-methods - Get user's payment methods
   */
  async getPaymentMethods() {
    return this.request('/payment-methods');
  }

  /**
   * POST /payment-methods - Add or update a payment method
   * @param {object} payload - { payment_method_id, type, last_four, is_default }
   */
  async upsertPaymentMethod(payload) {
    return this.request('/payment-methods', {
      method: 'POST',
      body: payload
    });
  }

  // ==================== Access Control ====================

  /**
   * POST /access-control - Record an access event
   * @param {object} payload - { unit_id, action: 'lock' or 'unlock' }
   */
  async recordAccessEvent(payload) {
    return this.request('/access-control', {
      method: 'POST',
      body: payload
    });
  }

  // ==================== Utility Methods ====================

  /**
   * Update the API base URL
   */
  updateBaseUrl(newBaseUrl) {
    this.baseUrl = newBaseUrl;
    CONFIG.setApiBaseUrl(newBaseUrl);
  }

  /**
   * Get current API base URL
   */
  getBaseUrl() {
    return this.baseUrl;
  }
}

// Export singleton instance
export const Api = new APIClient();
