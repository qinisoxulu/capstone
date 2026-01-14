// Configuration for the application
export const CONFIG = {
  // Cognito Configuration
  cognito: {
    domain: 'https://eu-central-1kx3gocjqv.auth.eu-central-1.amazoncognito.com',
    clientId: '15h813phjsbvkuo49brcdiu3qn',
    redirectUri: window.location.origin + '/dashboard.html',
    logoutUri: window.location.origin + '/index.html',
    scopes: ['email', 'openid', 'phone'],
    region: 'eu-central-1',
    userPoolId: 'eu-central-1_Kx3gocJqV'
  },

  apiBaseUrl: localStorage.getItem('apiBaseUrl') || 'https://your-api-id.execute-api.eu-central-1.amazonaws.com/Prod',

  setApiBaseUrl(url) {
    localStorage.setItem('apiBaseUrl', url);
    this.apiBaseUrl = url;
  }
};
