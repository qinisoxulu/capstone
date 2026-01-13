const poolData = {
    UserPoolId: 'eu-north-1_J8Gs87IFX',
    ClientId: '2qp8a2aam6i8q19f7aj6adf0ji',
};
const apiUrl = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

function authHeader() {
    const token = sessionStorage.getItem('jwt');
    if (!token) throw new Error('Please login first.');
    return { Authorization: `Bearer ${token}` };
}

async function refreshList() {
    try {
        const res = await fetch(`${apiUrl}/storageunits`, { headers: authHeader() });
        const data = await res.json();
        document.getElementById('listOutput').textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        document.getElementById('listOutput').textContent = `Error: ${e}`;
    }
}

document.getElementById('refresh').addEventListener('click', refreshList);

document.getElementById('createForm').addEventListener('submit', async (e) => {
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
        alert(data.message || 'Created');
        refreshList();
    } catch (e) {
        alert(`Error: ${e}`);
    }
});

document.getElementById('updateBtn').addEventListener('click', async () => {
    const unitId = document.getElementById('unitId').value;
    if (!unitId) return alert('Provide Unit ID');
    const payload = {};
    const name = document.getElementById('editName').value; if (name) payload.name = name;
    const location = document.getElementById('editLocation').value; if (location) payload.location = location;
    const capacity = document.getElementById('editCapacity').value; if (capacity !== '') payload.capacity = Number(capacity);
    const description = document.getElementById('editDescription').value; if (description) payload.description = description;

    if (Object.keys(payload).length === 0) return alert('No fields to update');

    try {
        const res = await fetch(`${apiUrl}/storageunits/${unitId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', ...authHeader() },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        alert(data.message || 'Updated');
        refreshList();
    } catch (e) { alert(`Error: ${e}`); }
});

document.getElementById('deleteBtn').addEventListener('click', async () => {
    const unitId = document.getElementById('unitId').value;
    if (!unitId) return alert('Provide Unit ID');
    if (!confirm('Delete this unit?')) return;
    try {
        const res = await fetch(`${apiUrl}/storageunits/${unitId}`, {
            method: 'DELETE',
            headers: authHeader(),
        });
        const data = await res.json();
        alert(data.message || 'Deleted');
        refreshList();
    } catch (e) { alert(`Error: ${e}`); }
});

document.getElementById('logout').addEventListener('click', () => {
    sessionStorage.removeItem('jwt');
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) cognitoUser.signOut();
    window.location.href = 'index.html';
});

// initial load
refreshList();
