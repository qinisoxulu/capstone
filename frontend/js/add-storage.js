const poolData = {
  UserPoolId: 'us-east-1_QdbTrfM9m',
  ClientId: '65lurh63ghpb48l9uo8gn9t5op',
};
const apiUrl = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

function authHeader() {
  const token = sessionStorage.getItem('jwt');
  if (!token) throw new Error('Login required');
  return { Authorization: `Bearer ${token}` };
}

document.getElementById('addStorageForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById('name').value,
    location: document.getElementById('location').value,
    capacity: Number(document.getElementById('capacity').value || 0),
    description: document.getElementById('description').value || '',
  };
  try {
    const res = await fetch(`${apiUrl}/storageunits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = `Error: ${e}`;
  }
});

