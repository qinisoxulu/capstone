const poolData = {
  UserPoolId: 'us-east-1_QdbTrfM9m',
  ClientId: '65lurh63ghpb48l9uo8gn9t5op',
};
const apiUrl = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

function authHeader() {
  const token = sessionStorage.getItem('jwt');
  if (!token) throw new Error('Please login first.');
  return { Authorization: `Bearer ${token}` };
}

function validCard(number) {
  const n = number.replace(/\s+/g, '');
  if (!/^\d{13,19}$/.test(n)) return false;
  let sum = 0, alt = false;
  for (let i = n.length - 1; i >= 0; i--) {
    let d = parseInt(n[i], 10);
    if (alt) { d *= 2; if (d > 9) d -= 9; }
    sum += d; alt = !alt;
  }
  return sum % 10 === 0;
}

function validExpiry(exp) {
  const m = exp.match(/^(\d{2})\/(\d{2})$/);
  if (!m) return false;
  const mm = parseInt(m[1], 10);
  const yy = parseInt(m[2], 10);
  if (mm < 1 || mm > 12) return false;
  const now = new Date();
  const year = now.getFullYear() % 100;
  const month = now.getMonth() + 1;
  if (yy < year || (yy === year && mm < month)) return false;
  return true;
}

document.getElementById('paymentForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const amount = parseFloat(document.getElementById('amount').value);
  const unitId = document.getElementById('unitId').value.trim();
  const cardName = document.getElementById('cardName').value.trim();
  const cardNumber = document.getElementById('cardNumber').value.trim();
  const expiry = document.getElementById('expiry').value.trim();
  const cvv = document.getElementById('cvv').value.trim();

  if (!amount || amount <= 0) return alert('Enter a valid amount');
  if (!cardName) return alert('Enter cardholder name');
  if (!validCard(cardNumber)) return alert('Enter a valid card number');
  if (!validExpiry(expiry)) return alert('Enter a valid expiry');
  if (!/^\d{3,4}$/.test(cvv)) return alert('Enter a valid CVV');

  const payload = {
    amount,
    currency: 'USD',
    unitId: unitId || null,
    card: { name: cardName, number: cardNumber, expiry, cvv },
  };

  try {
    const res = await fetch(`${apiUrl}/payments/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    document.getElementById('paymentResult').textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('paymentResult').textContent = `Error: ${e}`;
  }
});

