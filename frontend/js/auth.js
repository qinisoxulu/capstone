//authentification script
const poolData = {
    UserPoolId: 'us-east-1_hd0ZQEQwt',       // pool id change
    ClientId: '58ct9qscf836sr5b45hibqgspp'   //  app client
};

const apiUrl = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

// capturing sign up information
document.getElementById('signUpForm').addEventListener('submit', e => {
    e.preventDefault();

    const name = document.getElementById('signUpName').value;
    const email = document.getElementById('signUpEmail').value;
    const password = document.getElementById('signUpPassword').value;
    const idNumber = document.getElementById('signUpId').value;
    const address = document.getElementById('signUpAddress').value;
    const phone = document.getElementById('signUpPhone').value;

// cognito attribute objects
    const attributes = [
        new AmazonCognitoIdentity.CognitoUserAttribute({ Name: 'name', Value: name }),
        new AmazonCognitoIdentity.CognitoUserAttribute({ Name: 'email', Value: email }),
        new AmazonCognitoIdentity.CognitoUserAttribute({ Name: 'custom:id_number', Value: idNumber }),
        new AmazonCognitoIdentity.CognitoUserAttribute({ Name: 'custom:physical_address', Value: address }),
        new AmazonCognitoIdentity.CognitoUserAttribute({ Name: 'phone_number', Value: phone })
    ];

    userPool.signUp(email, password, attributes, null, (err, result) => {
        if (err) {
        alert(err.message || JSON.stringify(err));
        return;
        }
        alert('Account created! Check your email or SMS for verification.');

        document.getElementById('confirmationSection').style.display = 'block';
        document.getElementById('signUpForm').style.display = 'none';
        document.getElementById('no_account').style.display = 'none';
    });
});

// moving between forms
document.getElementById('showSignUp').onclick = () => {
    console.log('Switching to sign up form');
    document.getElementById('signUpForm').style.display = 'block';
    document.getElementById('loginForm').style.display = 'none';
};

// confirming user registration
document.getElementById('confirmBtn').addEventListener('click', function() {
  const code = document.getElementById('confirmationCode').value;
  const email = document.getElementById('signUpEmail').value;

  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
     Username: email,
      Pool: userPool
     });

  cognitoUser.confirmRegistration(code, true, function(err, result) {
    if (err) {
      alert(err.message || JSON.stringify(err));
      return;
    }

    console.log('Confirmation result: ' + result);

    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('confirmationSection').style.display = 'none';
    document.getElementById('no_account').style.display = 'none';
    
  });
});

// signing in
document.getElementById('loginForm').addEventListener('submit', e => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const authData = { Username: email, Password: password };
    const authDetails = new AmazonCognitoIdentity.AuthenticationDetails(authData);
    const userData = { Username: email, Pool: userPool };
    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    cognitoUser.authenticateUser(authDetails, {
        onSuccess: result => {
        const idToken = result.getIdToken().getJwtToken();
        sessionStorage.setItem('jwt', idToken);
        window.location.href = 'dashboard.html';
        },
        onFailure: err => { alert(err.message || JSON.stringify(err)); }
    });
});