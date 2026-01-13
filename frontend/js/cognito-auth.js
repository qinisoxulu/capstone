import { CONFIG } from './config.js';

/**
 * Cognito OAuth 2.0 PKCE Authentication Module
 */
export const CognitoAuth = {
  // Generate a random code verifier for PKCE
  generateCodeVerifier() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return this.base64URLEncode(array);
  },

  // Generate code challenge from verifier
  async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return this.base64URLEncode(new Uint8Array(hash));
  },

  // Base64 URL encoding
  base64URLEncode(buffer) {
    const base64 = btoa(String.fromCharCode(...buffer));
    return base64
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  },

  // Check if user is authenticated
  isAuthenticated() {
    const token = this.getAccessToken();
    if (!token) return false;

    // Check if token is expired
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return false;

    return Date.now() < parseInt(expiresAt);
  },

  // Get access token
  getAccessToken() {
    return localStorage.getItem('access_token');
  },

  // Get ID token
  getIdToken() {
    return localStorage.getItem('id_token');
  },

  // Get refresh token
  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  },

  // Get user info from ID token
  getUserInfo() {
    const idToken = this.getIdToken();
    if (!idToken) return null;

    try {
      const payload = idToken.split('.')[1];
      const decoded = JSON.parse(atob(payload));
      return {
        email: decoded.email,
        sub: decoded.sub,
        name: decoded.name || decoded.email,
        phoneNumber: decoded.phone_number
      };
    } catch (e) {
      console.error('Error decoding token:', e);
      return null;
    }
  },

  // Store tokens
  storeTokens(tokenResponse) {
    localStorage.setItem('access_token', tokenResponse.access_token);
    localStorage.setItem('id_token', tokenResponse.id_token);
    if (tokenResponse.refresh_token) {
      localStorage.setItem('refresh_token', tokenResponse.refresh_token);
    }

    // Calculate expiration time
    const expiresIn = tokenResponse.expires_in || 3600;
    const expiresAt = Date.now() + (expiresIn * 1000);
    localStorage.setItem('token_expires_at', expiresAt.toString());
  },

  // Clear tokens
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('id_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('code_verifier');
  },

  // Initiate login flow
  async login() {
    const codeVerifier = this.generateCodeVerifier();
    const codeChallenge = await this.generateCodeChallenge(codeVerifier);

    // Store code verifier for later use
    localStorage.setItem('code_verifier', codeVerifier);

    // Build authorization URL
    const params = new URLSearchParams({
      client_id: CONFIG.cognito.clientId,
      response_type: 'code',
      scope: CONFIG.cognito.scopes.join(' '),
      redirect_uri: CONFIG.cognito.redirectUri,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256'
    });

    const authUrl = `${CONFIG.cognito.domain}/oauth2/authorize?${params.toString()}`;
    window.location.href = authUrl;
  },

  // Handle redirect callback
  async handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');

    if (error) {
      throw new Error(`Authentication error: ${error}`);
    }

    if (!code) {
      return false; // No code present, not a callback
    }

    // Get stored code verifier
    const codeVerifier = localStorage.getItem('code_verifier');
    if (!codeVerifier) {
      throw new Error('Code verifier not found');
    }

    // Exchange code for tokens
    const tokenResponse = await this.exchangeCodeForTokens(code, codeVerifier);
    this.storeTokens(tokenResponse);

    // Clean up
    localStorage.removeItem('code_verifier');

    // Clean URL
    window.history.replaceState({}, document.title, window.location.pathname);

    return true;
  },

  // Exchange authorization code for tokens
  async exchangeCodeForTokens(code, codeVerifier) {
    const params = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: CONFIG.cognito.clientId,
      code: code,
      redirect_uri: CONFIG.cognito.redirectUri,
      code_verifier: codeVerifier
    });

    const response = await fetch(`${CONFIG.cognito.domain}/oauth2/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params.toString()
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Token exchange failed: ${error}`);
    }

    return await response.json();
  },

  // Refresh access token
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const params = new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: CONFIG.cognito.clientId,
      refresh_token: refreshToken
    });

    const response = await fetch(`${CONFIG.cognito.domain}/oauth2/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params.toString()
    });

    if (!response.ok) {
      // Refresh failed, user needs to log in again
      this.clearTokens();
      throw new Error('Token refresh failed');
    }

    const tokenResponse = await response.json();
    this.storeTokens(tokenResponse);
  },

  // Logout
  logout() {
    this.clearTokens();

    const params = new URLSearchParams({
      client_id: CONFIG.cognito.clientId,
      logout_uri: CONFIG.cognito.logoutUri
    });

    window.location.href = `${CONFIG.cognito.domain}/logout?${params.toString()}`;
  }
};
