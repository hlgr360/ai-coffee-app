// Helper to fetch the current admin count from the backend
async function getAdminCount() {
    const resp = await fetch('/api/users');
    if (!resp.ok) return 0;
    const data = await resp.json();
    return data.users.filter(u => u.is_admin).length;
}
window.getAdminCount = getAdminCount;
