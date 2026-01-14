// Configuration for the application
export const CONFIG = {
  // Cognito Configuration
  cognito: {
    domain: 'https://capstone-stack-225974461356.auth.af-south-1.amazoncognito.com',
    clientId: 'm7kvqlu44ecobiovd4cor6uhf',
    redirectUri: 'http://localhost:8080/dashboard.html',
    logoutUri: 'http://localhost:8080/index.html',
    scopes: ['email', 'openid', 'phone'],
    region: 'af-south-1',
    userPoolId: 'af-south-1_VFMM7Xzy3'
  },

  apiBaseUrl: localStorage.getItem('apiBaseUrl') || 'https://h43ytgotbl.execute-api.af-south-1.amazonaws.com/Prod',

  setApiBaseUrl(url) {
    localStorage.setItem('apiBaseUrl', url);
    this.apiBaseUrl = url;
  }
};
