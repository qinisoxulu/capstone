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

async function loadUnits() {
  const sel = document.getElementById('unitSelect');
  sel.innerHTML = '';
  try {
    const res = await fetch(`${apiUrl}/storageunits`, { headers: authHeader() });
    const data = await res.json();
    const units = Array.isArray(data) ? data : (data.items || []);
    units.forEach(u => {
      const opt = document.createElement('option');
      opt.value = u.unitId || u.id || '';
      opt.textContent = `${u.name || 'Unit'} — ${u.location || ''}`;
      sel.appendChild(opt);
    });
  } catch (e) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'Unable to load units';
    sel.appendChild(opt);
  }
}

function validDates(start, end) {
  if (!start || !end) return false;
  const s = new Date(start);
  const e = new Date(end);
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return false;
  return e > s;
}

document.getElementById('bookingForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const unitId = document.getElementById('unitSelect').value;
  const startDate = document.getElementById('startDate').value;
  const endDate = document.getElementById('endDate').value;
  const notes = document.getElementById('notes').value.trim();
  if (!unitId) return alert('Select a unit');
  if (!validDates(startDate, endDate)) return alert('Enter valid start and end dates');
  const payload = { unitId, startDate, endDate, notes };
  try {
    const res = await fetch(`${apiUrl}/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    document.getElementById('bookingResult').textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('bookingResult').textContent = `Error: ${e}`;
  }
});

loadUnits();

