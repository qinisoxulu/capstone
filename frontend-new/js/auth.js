/**
 * Authentication Module - Cognito OAuth Integration
 */

import { CONFIG } from '../config.js';

const AUTH_STORAGE_KEY = 'capstone_auth';

/**
 * Get stored authentication data
 */
function getStoredAuth() {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

/**
 * Store authentication data
 */
function storeAuth(authData) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
}

/**
 * Clear authentication data
 */
function clearAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

/**
 * Check if user is currently authenticated
 */
export function isAuthenticated() {
  const auth = getStoredAuth();
  if (!auth || !auth.access_token) {
    return false;
  }

  // Check if token has expired
  if (auth.expires_at && Date.now() >= auth.expires_at) {
    clearAuth();
    return false;
  }

  return true;
}

/**
 * Get the current access token
 */
export function getAccessToken() {
  const auth = getStoredAuth();
  if (!auth || !isAuthenticated()) {
    return null;
  }
  return auth.access_token;
}

/**
 * Get the current ID token
 */
export function getIdToken() {
  const auth = getStoredAuth();
  if (!auth || !isAuthenticated()) {
    return null;
  }
  return auth.id_token;
}

/**
 * Get user info from the ID token
 */
export function getUserInfo() {
  const idToken = getIdToken();
  if (!idToken) {
    return null;
  }

  try {
    // Decode JWT payload (base64)
    const payload = idToken.split('.')[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

/**
 * Build Cognito authorization URL
 */
function buildAuthUrl() {
  const { cognito } = CONFIG;
  const params = new URLSearchParams({
    response_type: 'token',
    client_id: cognito.clientId,
    redirect_uri: cognito.redirectUri,
    scope: cognito.scopes.join(' '),
  });

  return `${cognito.domain}/oauth2/authorize?${params.toString()}`;
}

/**
 * Initiate login - redirect to Cognito hosted UI
 */
export function login() {
  window.location.href = buildAuthUrl();
}

/**
 * Initiate signup - redirect to Cognito hosted UI with signup
 */
export function signup() {
  const authUrl = buildAuthUrl();
  // Add screen hint to show signup form
  window.location.href = authUrl;
}

/**
 * Logout user
 */
export function logout() {
  clearAuth();

  const { cognito } = CONFIG;
  const params = new URLSearchParams({
    client_id: cognito.clientId,
    logout_uri: cognito.logoutUri,
  });

  window.location.href = `${cognito.domain}/logout?${params.toString()}`;
}

/**
 * Handle OAuth callback - parse tokens from URL hash
 */
export function handleCallback() {
  const hash = window.location.hash.substring(1);
  if (!hash) {
    return false;
  }

  const params = new URLSearchParams(hash);
  const accessToken = params.get('access_token');
  const idToken = params.get('id_token');
  const expiresIn = params.get('expires_in');

  if (!accessToken) {
    // Check for error
    const error = params.get('error');
    if (error) {
      console.error('Auth error:', error, params.get('error_description'));
    }
    return false;
  }

  // Calculate expiry time
  const expiresAt = expiresIn ? Date.now() + (parseInt(expiresIn, 10) * 1000) : null;

  // Store auth data
  storeAuth({
    access_token: accessToken,
    id_token: idToken,
    expires_at: expiresAt,
  });

  // Clear the hash from URL
  window.history.replaceState(null, '', window.location.pathname);

  return true;
}

/**
 * Initialize auth - check for callback and update UI
 */
export function initAuth() {
  // Check if this is a callback from Cognito
  if (window.location.hash.includes('access_token')) {
    handleCallback();
  }

  // Update navbar based on auth status
  updateNavbar();
}

/**
 * Update navbar based on authentication status
 */
export function updateNavbar() {
  const authButton = document.getElementById('auth-btn');
  const dashboardLink = document.getElementById('dashboard-link');

  if (isAuthenticated()) {
    // User is logged in
    if (authButton) {
      authButton.textContent = 'Dashboard';
      authButton.href = 'dashboard.html';
      authButton.onclick = null;
    }
    if (dashboardLink) {
      dashboardLink.classList.remove('hidden');
    }
  } else {
    // User is not logged in
    if (authButton) {
      authButton.textContent = 'Sign Up';
      authButton.href = '#';
      authButton.onclick = (e) => {
        e.preventDefault();
        signup();
      };
    }
    if (dashboardLink) {
      dashboardLink.classList.add('hidden');
    }
  }
}

/**
 * Require authentication - redirect to login if not authenticated
 */
export function requireAuth() {
  if (!isAuthenticated()) {
    // Store current URL for redirect after login
    sessionStorage.setItem('auth_redirect', window.location.href);
    login();
    return false;
  }
  return true;
}
