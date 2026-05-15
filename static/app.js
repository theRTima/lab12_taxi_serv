function getToken() {
  return localStorage.getItem('access_token');
}

function authHeaders() {
  return {
    Authorization: 'Bearer ' + getToken(),
    'Content-Type': 'application/json',
  };
}

function showError(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}

function hideError(el) {
  if (!el) el = document.getElementById('error');
  if (el) el.classList.remove('visible');
}

function showSuccess(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}

function apiErrorMessage(data, status) {
  const detail = data && data.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(function (d) { return d.msg; }).join(', ');
  return status === 401 ? 'Session expired' : 'Request failed';
}

async function api(url, options) {
  const res = await fetch(url, options);
  let data = null;
  const text = await res.text();
  if (text) {
    if (text.trim().startsWith('<')) {
      throw new Error('Server returned HTML instead of JSON for ' + url);
    }
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }
  if (!res.ok) {
    const err = new Error(apiErrorMessage(data, res.status));
    err.status = res.status;
    throw err;
  }
  return data;
}

function requireAuth(redirect) {
  if (!getToken()) {
    window.location.href = redirect || '/login';
    return false;
  }
  return true;
}

async function fetchMe() {
  return api('/auth/me', { headers: authHeaders() });
}

function renderNav(container, user) {
  if (!container) return;
  const links = ['<a href="/">Home</a>', '<a href="/orders">Orders</a>', '<a href="/profile">Profile</a>'];
  if (user.role === 'client') {
    links.push('<a href="/orders/new">Book ride</a>');
  }
  if (user.role === 'driver') {
    links.push('<a href="/drivers">Driver panel</a>');
  }
  if (user.role === 'admin') {
    links.push('<a href="/dashboard">Dashboard</a>');
    links.push('<a href="/tariffs">Tariffs</a>');
    links.push('<a href="/drivers">Drivers</a>');
    links.push('<a href="/admin/users">Users</a>');
  }
  links.push('<a href="/docs" target="_blank">API docs</a>');
  container.innerHTML = links.join('');
}

function statusBadge(status) {
  return '<span class="badge badge-' + status + '">' + status + '</span>';
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

async function loadTariffs() {
  return api('/tariffs/list', {});
}

async function initPage(options) {
  const errorEl = document.getElementById('error');
  const navEl = document.getElementById('nav');
  if (!requireAuth()) return null;
  try {
    const user = await fetchMe();
    renderNav(navEl, user);
    hideError(errorEl);
    if (options && options.onReady) {
      try {
        await options.onReady(user);
      } catch (err) {
        if (errorEl) showError(errorEl, err.message || 'Failed to load page');
      }
    }
    return user;
  } catch (err) {
    if (err.status === 401 || !getToken()) {
      localStorage.removeItem('access_token');
      if (errorEl) showError(errorEl, err.message || 'Session expired');
      setTimeout(function () { window.location.href = '/login'; }, 1500);
    } else if (errorEl) {
      showError(errorEl, err.message || 'Failed to load page');
    }
    return null;
  }
}
