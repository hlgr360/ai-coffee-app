// main.js - Handles all dynamic UI logic for ai-coffee-app

// Settings flyout logic
async function openSettings() {
    const flyout = document.getElementById('settings-flyout');
    const resp = await fetch('/settings', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (resp.ok) {
        const html = await resp.text();
        flyout.innerHTML = `
            <div id="settings-flyout-modal" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.6);backdrop-filter:blur(2px);z-index:1000;display:flex;align-items:center;justify-content:center;">
                <div id="settings-flyout-content" style="background:#fff;padding:2em;max-width:700px;width:100%;border-radius:8px;position:relative;max-height:90vh;overflow:auto;">
                    ${html}
                </div>
            </div>`;
        flyout.style.display = 'block';
        // Trap clicks outside the modal to close it
        document.getElementById('settings-flyout-modal').onclick = function(e) {
            if (e.target === this) closeSettings();
        };
        // Re-bind event handlers and update tables for dynamic content
        if (document.getElementById('add-user-btn')) {
            document.getElementById('add-user-btn').onclick = addUser;
            updateUsersTable();
        }
        if (document.getElementById('add-cup-form')) {
            document.getElementById('add-cup-form').onsubmit = addCup;
            updateCupsTable();
        }
    }
}
function closeSettings() {
    const flyout = document.getElementById('settings-flyout');
    flyout.style.display = 'none';
    flyout.innerHTML = '';
}
async function addCup(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const resp = await fetch('/api/cups', {
        method: 'POST',
        body: formData
    });
    if (resp.ok) {
        updateCupsTable();
        form.reset();
    }
}
async function updateCupsTable() {
    const resp = await fetch('/api/cups');
    if (!resp.ok) return;
    const cups = await resp.json();
    const tbody = document.getElementById('cups-table-body');
    tbody.innerHTML = '';
    if (cups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No cups defined.</td></tr>';
    } else {
        for (const cup of cups) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${cup.name}</td><td>${cup.size}</td><td><button onclick=\"deleteCup('${cup.id}')\" style=\"background:#e53935;color:#fff;border:none;border-radius:4px;padding:0.3em 0.8em;cursor:pointer;\">Delete</button></td>`;
            tbody.appendChild(tr);
        }
    }
}
async function updateUsersTable() {
    const resp = await fetch('/api/users');
    if (!resp.ok) return;
    const data = await resp.json();
    const adminCount = data.users.filter(u => u.is_admin).length;
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';
    if (data.users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No users found.</td></tr>';
    } else {
        for (const user of data.users) {
            const isLastAdmin = user.is_admin && adminCount === 1;
            const deleteBtn = `<button onclick=\"deleteUser('${user.id}')\" style=\"background:#e53935;color:#fff;border:none;border-radius:4px;padding:0.3em 0.8em;cursor:pointer;\" ${isLastAdmin ? 'disabled title="Cannot delete last admin"' : ''}>Delete</button>`;
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${user.username}</td><td>${user.is_admin ? 'Yes' : 'No'}</td><td>${deleteBtn}</td>`;
            tbody.appendChild(tr);
        }
    }
}
async function addUser(event) {
    if (event) event.preventDefault();
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;
    const isAdmin = document.getElementById('new-is-admin').checked;
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    if (isAdmin) formData.append('is_admin', 'on');
    const resp = await fetch('/settings/users/add', {
        method: 'POST',
        body: formData
    });
    if (resp.redirected || resp.ok) {
        updateUsersTable();
        document.getElementById('new-username').value = '';
        document.getElementById('new-password').value = '';
        document.getElementById('new-is-admin').checked = false;
    }
}
async function deleteCup(id) {
    const resp = await fetch(`/api/cups/${id}`, { method: 'DELETE' });
    if (resp.ok) updateCupsTable();
}
async function deleteUser(id) {
    // Use a form POST to /settings/users/delete, matching backend
    const formData = new FormData();
    formData.append('user_id', id);
    const resp = await fetch('/settings/users/delete', {
        method: 'POST',
        body: formData
    });
    if (resp.redirected || resp.ok) {
        updateUsersTable();
    }
}
// Password change validation
function validatePasswordForm() {
    const pw1 = document.getElementById('new_password').value;
    const pw2 = document.getElementById('confirm_password').value;
    if (pw1 !== pw2) {
        alert('Passwords do not match.');
        return false;
    }
    return true;
}
// Expose functions globally for inline event handlers
window.openSettings = openSettings;
window.closeSettings = closeSettings;
window.addCup = addCup;
window.updateCupsTable = updateCupsTable;
window.updateUsersTable = updateUsersTable;
window.addUser = addUser;
window.deleteCup = deleteCup;
window.deleteUser = deleteUser;
window.validatePasswordForm = validatePasswordForm;
