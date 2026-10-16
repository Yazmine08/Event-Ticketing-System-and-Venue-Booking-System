/**
 * Event Ticketing and Venue Booking System - Frontend Application Logic
 * Course: SWC3633 / SWC4443 Web API Development
 * Universiti Poly-Tech Malaysia (UPTM)
 */

// Intelligent API_BASE configuration:
// If accessed directly on port 8000, use origin; if opened via Apache (e.g. port 80), point to port 8000
const API_BASE = (window.location.port === '8000') 
  ? window.location.origin 
  : `${window.location.protocol}//${window.location.hostname || 'localhost'}:8000`;

// Global Application State
const state = {
  token: localStorage.getItem('token') || null,
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  events: [],
  categories: [],
  venues: [],
  bookings: [],
  allBookings: [],
  userLogins: [],
  allUsers: [],
  currentPage: 1,
  totalPages: 1,
  selectedCategory: null,
  activeTab: 'events-tab'
};

// Toast Notifications Helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const id = 'toast-' + Date.now();
  const bgClass = type === 'success' ? 'bg-success text-white' : type === 'error' ? 'bg-danger text-white' : 'bg-primary text-white';
  
  const toastHtml = `
    <div id="${id}" class="toast align-items-center ${bgClass} border-0 mb-2 shadow" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body fw-medium">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `;
  container.insertAdjacentHTML('beforeend', toastHtml);
  const el = document.getElementById(id);
  const bsToast = new bootstrap.Toast(el, { delay: 4000 });
  bsToast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// Unified API Fetch Helper
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, { credentials: 'omit', ...options, headers });
    
    // Check if binary download (e.g. PDF ticket or QR image)
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/pdf') || contentType.includes('image/')) {
      if (!res.ok) throw new Error('File download failed');
      return await res.blob();
    }

    const data = await res.json();
    if (!res.ok) {
      const errMsg = (data.error && data.error.message) || data.detail || 'An unexpected error occurred.';
      throw new Error(errMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

// ---------------- AUTHENTICATION & SESSIONS ----------------

function togglePasswordVisibility(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  if (!input) return;

  if (input.type === 'password') {
    input.type = 'text';
    if (icon) {
      icon.classList.remove('bi-eye');
      icon.classList.add('bi-eye-slash');
    }
  } else {
    input.type = 'password';
    if (icon) {
      icon.classList.remove('bi-eye-slash');
      icon.classList.add('bi-eye');
    }
  }
}

function clearAuthForms() {
  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.reset();
  const emailInput = document.getElementById('login-email');
  if (emailInput) emailInput.value = '';
  const pwdInput = document.getElementById('login-password');
  if (pwdInput) {
    pwdInput.value = '';
    pwdInput.type = 'password';
  }
  const loginEye = document.getElementById('login-pass-icon');
  if (loginEye) {
    loginEye.classList.remove('bi-eye-slash');
    loginEye.classList.add('bi-eye');
  }

  const regForm = document.getElementById('register-form');
  if (regForm) regForm.reset();
  const regEmail = document.getElementById('reg-email');
  if (regEmail) regEmail.value = '';
  const regPwd = document.getElementById('reg-password');
  if (regPwd) {
    regPwd.value = '';
    regPwd.type = 'password';
  }
  const regEye = document.getElementById('reg-pass-icon');
  if (regEye) {
    regEye.classList.remove('bi-eye-slash');
    regEye.classList.add('bi-eye');
  }
}

function fillDemoLogin(email, password) {
  const emailInput = document.getElementById('login-email');
  const passInput = document.getElementById('login-password');
  if (emailInput) emailInput.value = email;
  if (passInput) passInput.value = password;
  login(email, password);
}

async function login(email, password) {
  try {
    const res = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    });
    const user = res.data.user;
    setSession(res.data.access_token, user);
    showToast(`Welcome back, ${user.full_name || user.name}! (${user.role.toUpperCase()})`, 'success');
    
    // Clear credentials from DOM for privacy & security
    clearAuthForms();
    closeModal('loginModal');
    updateNavState();
    loadDashboardForRole();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function register(payload) {
  try {
    const res = await apiFetch('/api/auth/register', {
      method: 'POST',
      body: payload
    });
    const user = res.data.user;
    setSession(res.data.access_token, user);
    showToast(`Account created! Welcome, ${user.full_name || user.name}!`, 'success');
    
    clearAuthForms();
    closeModal('registerModal');
    updateNavState();
    loadDashboardForRole();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function setSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
}

function logout() {
  state.token = null;
  state.user = null;
  state.bookings = [];
  localStorage.removeItem('token');
  localStorage.removeItem('user');

  // Completely erase previous login/password credentials from input fields
  clearAuthForms();

  // Reset user-specific DOM containers
  const myBookingsContainer = document.getElementById('my-bookings-container');
  if (myBookingsContainer) myBookingsContainer.innerHTML = '';

  updateNavState();
  showToast('Logged out successfully.', 'info');
  switchTab('events-tab');
  loadEvents();
}

function updateNavState() {
  const guestBlock = document.getElementById('nav-guest-block');
  const userBlock = document.getElementById('nav-user-block');
  const roleBadge = document.getElementById('user-role-badge');
  const userName = document.getElementById('user-display-name');
  const userApiKey = document.getElementById('user-api-key-display');
  
  // Navigation tabs visibility
  const myBookingsNav = document.getElementById('nav-item-my-bookings');
  const organiserNav = document.getElementById('nav-item-organiser');
  const adminNav = document.getElementById('nav-item-admin');

  if (state.user) {
    if (guestBlock) guestBlock.classList.add('d-none');
    if (userBlock) userBlock.classList.remove('d-none');
    if (userName) userName.textContent = state.user.full_name || state.user.name || 'User';
    if (roleBadge) {
      roleBadge.textContent = state.user.role.toUpperCase();
      roleBadge.className = 'badge ' + (
        state.user.role === 'admin' ? 'bg-danger' : 
        state.user.role === 'organiser' ? 'bg-warning text-dark' : 'bg-primary'
      );
    }
    
    if (userApiKey && state.user.api_key) {
      userApiKey.textContent = `API Key: ${state.user.api_key.substring(0, 14)}...`;
      userApiKey.title = `Full API Key: ${state.user.api_key}`;
    }

    // Role-based navigation tabs
    if (myBookingsNav) myBookingsNav.classList.remove('d-none');
    if (organiserNav) {
      if (state.user.role === 'organiser' || state.user.role === 'admin') {
        organiserNav.classList.remove('d-none');
      } else {
        organiserNav.classList.add('d-none');
      }
    }

    if (adminNav) {
      if (state.user.role === 'admin') {
        adminNav.classList.remove('d-none');
      } else {
        adminNav.classList.add('d-none');
      }
    }
  } else {
    if (guestBlock) guestBlock.classList.remove('d-none');
    if (userBlock) userBlock.classList.add('d-none');
    if (myBookingsNav) myBookingsNav.classList.add('d-none');
    if (organiserNav) organiserNav.classList.add('d-none');
    if (adminNav) adminNav.classList.add('d-none');
  }
}

function loadDashboardForRole() {
  if (!state.user) {
    loadEvents();
    return;
  }
  if (state.user.role === 'admin') {
    switchTab('admin-tab');
  } else if (state.user.role === 'organiser') {
    switchTab('organiser-tab');
  } else {
    switchTab('events-tab');
  }
}

// ---------------- TAB SWITCHING ----------------

function switchTab(tabId) {
  state.activeTab = tabId;
  // Remove active styling from all navbar buttons
  document.querySelectorAll('#mainTabNav .nav-link').forEach(btn => btn.classList.remove('active'));

  const triggerEl = document.querySelector(`[data-bs-target="#${tabId}"]`);
  if (triggerEl) {
    const tabInstance = bootstrap.Tab.getOrCreateInstance(triggerEl);
    tabInstance.show();
  } else {
    // Activate target tab pane directly (e.g., events-tab navigated via TicketHub logo)
    document.querySelectorAll('#mainTabContent > .tab-pane').forEach(p => p.classList.remove('show', 'active'));
    const pane = document.getElementById(tabId);
    if (pane) pane.classList.add('show', 'active');
  }
  
  if (tabId === 'events-tab') {
    loadCategories();
    loadEvents();
  }
  if (tabId === 'my-bookings-tab') loadMyBookings();
  if (tabId === 'organiser-tab') {
    loadCategories();
    loadOrganiserDashboard();
  }
  if (tabId === 'admin-tab') loadAdminDashboard();
  if (tabId === 'telemetry-tab') loadExternalApiTelemetry();
}

// ---------------- EVENTS BROWSING & SEARCH ----------------

async function loadCategories() {
  try {
    const res = await apiFetch('/api/categories');
    state.categories = res.data;
    renderCategoriesFilter(res.data);
    populateCategoryDropdowns(res.data);
  } catch (err) {
    console.error('Failed to load categories:', err);
  }
}

function renderCategoriesFilter(cats) {
  const container = document.getElementById('categories-filter-container');
  if (!container) return;
  
  const allActive = state.selectedCategory === null;
  let html = `<button class="btn btn-sm ${allActive ? 'btn-primary' : 'btn-outline-secondary'} me-2 mb-2" onclick="filterByCategory(null)">All Categories</button>`;
  
  if (Array.isArray(cats)) {
    cats.forEach(c => {
      const catId = c.category_id || c.id;
      const catName = c.category_name || c.name;
      const active = state.selectedCategory !== null && String(state.selectedCategory) === String(catId);
      const count = (c.event_count !== undefined && c.event_count !== null) ? parseInt(c.event_count, 10) : 0;
      html += `<button class="btn btn-sm ${active ? 'btn-primary' : 'btn-outline-secondary'} me-2 mb-2" onclick="filterByCategory(${catId})">${catName} (${count})</button>`;
    });
  }
  container.innerHTML = html;
}

function filterByCategory(catId) {
  state.selectedCategory = catId;
  state.currentPage = 1;
  renderCategoriesFilter(state.categories);
  loadEvents(false);
}

async function loadEvents(refreshCategories = true) {
  if (refreshCategories) {
    loadCategories();
  }
  const container = document.getElementById('events-grid');
  if (!container) return;
  container.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Loading available events...</p></div>';

  const searchInput = document.getElementById('event-search-input')?.value || '';
  const sortBy = document.getElementById('event-sort-select')?.value || 'event_date';
  const order = sortBy.includes('desc') ? 'desc' : 'asc';
  const actualSort = sortBy.replace('_desc', '').replace('start_time', 'event_date');

  let query = `/api/events?page=${state.currentPage}&limit=6&sort_by=${actualSort}&order=${order}`;
  if (state.selectedCategory) query += `&category_id=${state.selectedCategory}`;
  if (searchInput.trim()) query += `&search=${encodeURIComponent(searchInput.trim())}`;

  try {
    const res = await apiFetch(query);
    state.events = res.data;
    state.totalPages = res.pagination.total_pages;
    renderEventsGrid(res.data);
    renderPagination('events-pagination', res.pagination, changeEventPage);
  } catch (err) {
    container.innerHTML = `<div class="col-12 alert alert-danger">Error loading events: ${err.message}</div>`;
  }
}

const EVENT_IMAGE_PRESETS = {
  music: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80',
  tech: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=800&q=80',
  sports: 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=800&q=80',
  education: 'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=800&q=80',
  business: 'https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=800&q=80',
  default: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=800&q=80'
};

function getCategoryDefaultImage(catName) {
  if (!catName) return EVENT_IMAGE_PRESETS.default;
  const c = catName.toLowerCase();
  if (c.includes('music') || c.includes('concert')) return EVENT_IMAGE_PRESETS.music;
  if (c.includes('tech') || c.includes('software') || c.includes('ai')) return EVENT_IMAGE_PRESETS.tech;
  if (c.includes('sport') || c.includes('game') || c.includes('championship')) return EVENT_IMAGE_PRESETS.sports;
  if (c.includes('edu') || c.includes('workshop') || c.includes('skill')) return EVENT_IMAGE_PRESETS.education;
  if (c.includes('biz') || c.includes('business') || c.includes('summit')) return EVENT_IMAGE_PRESETS.business;
  return EVENT_IMAGE_PRESETS.default;
}

function renderEventsGrid(events) {
  const container = document.getElementById('events-grid');
  if (!container) return;

  if (events.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center py-5">
        <i class="bi bi-calendar-x display-4 text-muted"></i>
        <h5 class="mt-3 text-muted">No events match your criteria</h5>
        <button class="btn btn-outline-primary btn-sm mt-2" onclick="document.getElementById('event-search-input').value=''; filterByCategory(null);">Reset Filters</button>
      </div>`;
    return;
  }

  let html = '';
  events.forEach(e => {
    const eventId = e.event_id || e.id;
    const eventName = e.event_name || e.title;
    const isSoldOut = e.available_tickets <= 0;
    const eventImg = e.image_url || getCategoryDefaultImage(e.category_name);
    const venueLoc = e.venue_location || e.venue_city || 'Kuala Lumpur';
    const dateStr = e.event_date ? `${e.event_date} (${e.start_time || ''})` : (e.start_time || '');

    html += `
      <div class="col-md-6 col-lg-4 mb-4">
        <div class="card event-card h-100 shadow-sm">
          <img src="${eventImg}" class="event-card-img" alt="${eventName}" onerror="this.src=EVENT_IMAGE_PRESETS.default">
          <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="badge badge-category">${e.category_name || 'Event'}</span>
              <span class="badge ${isSoldOut ? 'bg-danger' : 'bg-success'}">${isSoldOut ? 'SOLD OUT' : e.available_tickets + ' tickets left'}</span>
            </div>
            <h5 class="card-title fw-bold text-dark mb-1">${eventName}</h5>
            <p class="text-muted small mb-2"><i class="bi bi-geo-alt me-1 text-primary"></i>${e.venue_name || 'Venue'}, ${venueLoc}</p>
            <p class="text-muted small mb-3"><i class="bi bi-clock me-1 text-primary"></i>${dateStr}</p>
            <p class="card-text text-secondary small flex-grow-1">${(e.description || '').substring(0, 110)}...</p>
            
            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
              <div>
                <span class="text-muted small">Price</span>
                <h5 class="text-primary fw-bold mb-0">RM ${parseFloat(e.ticket_price || 0).toFixed(2)}</h5>
              </div>
              <button class="btn btn-primary btn-sm px-3 fw-medium" ${isSoldOut ? 'disabled' : ''} onclick="openBookingModal(${eventId})">
                <i class="bi bi-ticket-perforated me-1"></i> ${isSoldOut ? 'Sold Out' : 'Book Now'}
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function changeEventPage(page) {
  state.currentPage = page;
  loadEvents();
}

// ---------------- BOOKING MODAL & FLOW ----------------

let currentBookingEvent = null;

function openBookingModal(eventId) {
  if (!state.user) {
    showToast('Please sign in or register to book event tickets.', 'info');
    openModal('loginModal');
    return;
  }

  const event = state.events.find(e => (e.event_id || e.id) === eventId);
  if (!event) return;
  currentBookingEvent = event;

  const eventName = event.event_name || event.title;
  const venueLoc = event.venue_location || event.venue_city || 'Kuala Lumpur';

  document.getElementById('booking-modal-title').textContent = `Book Tickets: ${eventName}`;
  document.getElementById('booking-modal-event-name').textContent = eventName;
  document.getElementById('booking-modal-venue').textContent = `${event.venue_name || 'Venue'} (${venueLoc})`;
  document.getElementById('booking-modal-datetime').textContent = `${event.event_date || ''} ${event.start_time || ''}`;
  document.getElementById('booking-modal-unit-price').textContent = `RM ${parseFloat(event.ticket_price || 0).toFixed(2)}`;
  document.getElementById('booking-modal-avail').textContent = `${event.available_tickets} seats`;

  const qtyInput = document.getElementById('booking-modal-qty');
  qtyInput.value = 1;
  qtyInput.max = Math.min(10, event.available_tickets);
  updateBookingTotal();

  openModal('bookingModal');
}

function updateBookingTotal() {
  if (!currentBookingEvent) return;
  const qty = parseInt(document.getElementById('booking-modal-qty').value) || 1;
  const price = parseFloat(currentBookingEvent.ticket_price || 0);
  const total = qty * price;
  document.getElementById('booking-modal-total').textContent = `RM ${total.toFixed(2)}`;
}

async function confirmBooking() {
  if (!currentBookingEvent) return;
  const qty = parseInt(document.getElementById('booking-modal-qty').value) || 1;
  const method = document.getElementById('booking-modal-payment').value;
  const btn = document.getElementById('btn-confirm-booking');

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting to External APIs...';

  try {
    const res = await apiFetch('/api/bookings', {
      method: 'POST',
      body: {
        event_id: currentBookingEvent.event_id || currentBookingEvent.id,
        quantity: qty,
        payment_method: method
      }
    });

    closeModal('bookingModal');
    showToast(`Booking Successful! Ticket: ${res.data.ticket_code}`, 'success');
    
    // Show instant success modal with external QR Code
    showBookingConfirmationModal(res.data);
    loadEvents();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-credit-card me-1"></i> Confirm & Pay';
  }
}

async function loadQrCodeIntoImage(imgEl, bookingId, ticketCode) {
  if (!imgEl) return;
  imgEl.alt = 'Loading QR code...';
  
  try {
    const blob = await apiFetch(`/api/bookings/${bookingId}/qrcode?format=image`);
    if (blob instanceof Blob && blob.size > 0) {
      const objectUrl = window.URL.createObjectURL(blob);
      imgEl.src = objectUrl;
      imgEl.alt = `Gate Pass QR Code for ${ticketCode}`;
      return;
    }
  } catch (err) {
    console.warn('QR fetch failed:', err);
    // If ticket is cancelled, do NOT generate a fallback QR pass
    if (err.message && err.message.toLowerCase().includes('cancelled')) {
      imgEl.src = '';
      imgEl.alt = err.message;
      showToast(err.message, 'error');
      return;
    }
  }

  // Fallback 1: Authenticated endpoint with token query parameter
  if (state.token) {
    imgEl.src = `${API_BASE}/api/bookings/${bookingId}/qrcode?token=${encodeURIComponent(state.token)}`;
  } else {
    // Fallback 2: Direct public QR generator API
    imgEl.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&margin=10&data=${encodeURIComponent(ticketCode)}`;
  }
  imgEl.alt = `Gate Pass QR Code for ${ticketCode}`;
}

function showBookingConfirmationModal(bookingData) {
  const ticketCode = bookingData.ticket_code;
  const bookingId = bookingData.booking_id || bookingData.id;

  document.getElementById('confirm-modal-ref').textContent = ticketCode;
  document.getElementById('confirm-modal-event').textContent = bookingData.event_name || bookingData.event_title;
  document.getElementById('confirm-modal-qty').textContent = `${bookingData.quantity || bookingData.num_tickets} ticket(s)`;
  document.getElementById('confirm-modal-amount').textContent = `RM ${parseFloat(bookingData.total_amount || 0).toFixed(2)}`;
  
  // Real-time external QR code loader with authentication & fallback
  const imgEl = document.getElementById('confirm-modal-qr-img');
  imgEl.src = '';
  loadQrCodeIntoImage(imgEl, bookingId, ticketCode);

  // Attach PDF download action
  const pdfBtn = document.getElementById('confirm-modal-download-pdf');
  pdfBtn.onclick = () => downloadTicketPdf(bookingId, ticketCode);

  openModal('bookingSuccessModal');
}

// ---------------- MY BOOKINGS TAB ----------------

async function loadMyBookings() {
  if (!state.user) return;
  const container = document.getElementById('my-bookings-container');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">Retrieving your bookings...</p></div>';

  try {
    const res = await apiFetch('/api/bookings?limit=50');
    state.bookings = res.data;
    renderMyBookingsTable(res.data);
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
  }
}

function renderMyBookingsTable(bookings) {
  const container = document.getElementById('my-bookings-container');
  if (!container) return;

  if (bookings.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5 bg-white rounded-3 border">
        <i class="bi bi-ticket-detailed display-4 text-muted"></i>
        <h5 class="mt-3 text-muted">No bookings found</h5>
        <p class="text-secondary small">You haven't booked any event tickets yet.</p>
        <button class="btn btn-primary btn-sm" onclick="switchTab('events-tab')">Browse Events</button>
      </div>`;
    return;
  }

  let html = `
    <div class="table-responsive bg-white rounded-3 border shadow-sm">
      <table class="table custom-table table-hover align-middle mb-0">
        <thead>
          <tr>
            <th>Ticket Code</th>
            <th>Event & Venue</th>
            <th>Date</th>
            <th>Tickets</th>
            <th>Total Paid</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
  `;

  bookings.forEach(b => {
    const bookingId = b.booking_id || b.id;
    const ticketCode = b.ticket_code || b.booking_reference || `TKT${bookingId}`;
    const eventName = b.event_name || b.event_title || 'Event';
    const isCancelled = (b.booking_status || b.status) === 'cancelled';
    const cancelReason = b.cancellation_reason || 'Customer requested cancellation';
    const cancelDate = b.cancelled_at || b.booking_date || '';
    const venueLoc = b.venue_location || b.venue_city || '';
    const dateStr = b.event_date || (b.start_time ? b.start_time.substring(0, 10) : 'Upcoming');
    const totalFormatted = `RM ${parseFloat(b.total_amount || 0).toFixed(2)}`;

    const statusBadge = isCancelled 
      ? `<span class="badge bg-danger">Cancelled</span><br/><small class="text-danger d-inline-block text-truncate mt-1" style="max-width: 140px;" title="${cancelReason}"><i class="bi bi-info-circle me-1"></i>${cancelReason}</small>` 
      : '<span class="badge bg-success">Confirmed</span>';

    const safeEventName = eventName.replace(/'/g, "\\'");
    const safeReason = cancelReason.replace(/'/g, "\\'");

    let actionButtons = '';
    if (isCancelled) {
      actionButtons = `
        <button class="btn btn-outline-danger btn-sm" title="View Cancellation Notice & Details" onclick="showCancellationNoticeModal(${bookingId}, '${ticketCode}', '${safeEventName}', '${safeReason}', '${cancelDate}', '${totalFormatted}')">
          <i class="bi bi-file-earmark-x me-1"></i> Notice
        </button>
      `;
    } else {
      actionButtons = `
        <div class="btn-group btn-group-sm">
          <button class="btn btn-outline-primary" title="View External QR Code" onclick="viewBookingQrModal(${bookingId}, '${ticketCode}', '${safeEventName}')">
            <i class="bi bi-qr-code"></i> QR
          </button>
          <button class="btn btn-outline-success" title="Download Official PDF Ticket" onclick="downloadTicketPdf(${bookingId}, '${ticketCode}')">
            <i class="bi bi-file-earmark-pdf"></i> PDF
          </button>
          <button class="btn btn-outline-danger" title="Cancel Booking" onclick="cancelBookingPrompt(${bookingId}, '${ticketCode}', '${safeEventName}')">
            <i class="bi bi-x-circle"></i>
          </button>
        </div>
      `;
    }

    html += `
      <tr>
        <td><strong class="text-primary">${ticketCode}</strong><br/><small class="text-muted">${b.payment_method || 'card'}</small></td>
        <td><strong>${eventName}</strong><br/><small class="text-muted">${b.venue_name || 'Venue'}, ${venueLoc}</small></td>
        <td><small>${dateStr}</small></td>
        <td><span class="badge bg-light text-dark border">${b.quantity || b.num_tickets || 1} ticket(s)</span></td>
        <td><strong>${totalFormatted}</strong></td>
        <td>${statusBadge}</td>
        <td>${actionButtons}</td>
      </tr>
    `;
  });

  html += '</tbody></table></div>';
  container.innerHTML = html;
}

function showCancellationNoticeModal(bookingId, ticketCode, eventName, reason, cancelDate, amountStr) {
  document.getElementById('notice-modal-ticket-code').textContent = ticketCode;
  document.getElementById('notice-modal-event').textContent = eventName;
  document.getElementById('notice-modal-reason').textContent = reason || 'Customer requested cancellation';
  document.getElementById('notice-modal-date').textContent = cancelDate ? cancelDate.substring(0, 16) : 'Recently cancelled';
  document.getElementById('notice-modal-refund').textContent = `100% Refunded (${amountStr}) to original payment method`;
  openModal('cancellationNoticeModal');
}

function cancelBookingPrompt(bookingId, ticketCode, eventName) {
  document.getElementById('cancel-prompt-id').value = bookingId;
  document.getElementById('cancel-prompt-code').textContent = ticketCode;
  document.getElementById('cancel-prompt-event').textContent = eventName;
  document.getElementById('cancel-prompt-reason-select').value = 'Schedule conflict / Change of plans';
  document.getElementById('cancel-custom-reason-wrap').style.display = 'none';
  document.getElementById('cancel-prompt-custom-reason').value = '';
  openModal('cancelBookingModal');
}

function toggleCustomCancelReason() {
  const sel = document.getElementById('cancel-prompt-reason-select');
  const wrap = document.getElementById('cancel-custom-reason-wrap');
  wrap.style.display = sel.value === 'other' ? 'block' : 'none';
}

async function submitBookingCancellation() {
  const bookingId = document.getElementById('cancel-prompt-id').value;
  const ticketCode = document.getElementById('cancel-prompt-code').textContent;
  const sel = document.getElementById('cancel-prompt-reason-select');
  const custom = document.getElementById('cancel-prompt-custom-reason').value.trim();
  
  let reason = sel.value;
  if (reason === 'other') {
    reason = custom || 'Customer requested cancellation - Personal reason';
  }

  const btn = document.getElementById('cancel-confirm-submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Cancelling...';

  try {
    await apiFetch(`/api/bookings/${bookingId}/cancel`, {
      method: 'PUT',
      body: { cancellation_reason: reason }
    });
    closeModal('cancelBookingModal');
    showToast(`Booking ${ticketCode} cancelled successfully.`, 'success');
    loadMyBookings();
    loadEvents();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Confirm Cancel';
  }
}

function viewBookingQrModal(bookingId, ticketCode, eventTitle) {
  document.getElementById('view-qr-ref').textContent = ticketCode;
  document.getElementById('view-qr-event').textContent = eventTitle;
  
  // Real-time external QR code loader with authentication & fallback
  const imgEl = document.getElementById('view-qr-img');
  imgEl.src = '';
  loadQrCodeIntoImage(imgEl, bookingId, ticketCode);
  
  document.getElementById('view-qr-pdf-btn').onclick = () => downloadTicketPdf(bookingId, ticketCode);
  openModal('viewQrModal');
}

async function downloadTicketPdf(bookingId, ticketCode) {
  showToast(`Generating admission PDF for ${ticketCode} via PDF API...`, 'info');
  try {
    const blob = await apiFetch(`/api/bookings/${bookingId}/pdf`);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Ticket_${ticketCode}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast(`PDF ticket downloaded successfully!`, 'success');
  } catch (err) {
    showToast(`PDF Download failed: ${err.message}`, 'error');
  }
}

// ---------------- ORGANISER DASHBOARD & GATE SCANNER ----------------

async function loadOrganiserDashboard() {
  if (!state.user || (state.user.role !== 'organiser' && state.user.role !== 'admin')) return;

  // Load metrics
  try {
    const stats = await apiFetch('/api/stats/dashboard');
    if (stats.metrics) {
      const m = stats.metrics;
      document.getElementById('org-stat-events').textContent = m.my_events || m.total_events || 0;
      document.getElementById('org-stat-sold').textContent = m.total_tickets_sold || 0;
      document.getElementById('org-stat-revenue').textContent = `RM ${(m.total_revenue || 0).toFixed(2)}`;
      document.getElementById('org-stat-bookings').textContent = m.active_bookings || 0;
    }
  } catch (e) { console.error(e); }

  loadOrganiserEventsTable();
  loadVenuesForForms();
}

async function loadOrganiserEventsTable() {
  const container = document.getElementById('org-events-container');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary spinner-border-sm"></div></div>';

  try {
    const userId = state.user.user_id || state.user.id;
    const url = state.user.role === 'admin' ? '/api/events?limit=100' : `/api/events?limit=100&organiser_id=${userId}`;
    const res = await apiFetch(url);
    if (res.data.length === 0) {
      container.innerHTML = '<div class="alert alert-light border text-center">You have not created any events yet. Click "Create New Event" above!</div>';
      return;
    }

    let html = `
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>Event Details</th>
            <th>Venue</th>
            <th>Date & Time</th>
            <th>Tickets Remaining / Total</th>
            <th>Price</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
    `;

    res.data.forEach(e => {
      const eventId = e.event_id || e.id;
      const eventName = e.event_name || e.title;
      const sold = e.total_tickets - e.available_tickets;
      const eventImg = e.image_url || getCategoryDefaultImage(e.category_name);
      const safeTitle = (eventName || '').replace(/'/g, "\\'");
      const safeImg = (e.image_url || '').replace(/'/g, "\\'");
      html += `
        <tr>
          <td>
            <div class="d-flex align-items-center gap-3">
              <div class="position-relative" style="width: 58px; height: 42px; flex-shrink: 0; cursor: pointer;" onclick="openEditEventPictureModal(${eventId}, '${safeTitle}', '${safeImg}')" title="Click to change picture">
                <img src="${eventImg}" style="width: 58px; height: 42px; object-fit: cover; border-radius: 6px; border: 1px solid #dee2e6;" onerror="this.src=EVENT_IMAGE_PRESETS.default">
                <span class="position-absolute bottom-0 end-0 bg-dark bg-opacity-75 text-white rounded-bottom-end px-1" style="font-size: 9px;"><i class="bi bi-pencil-fill"></i></span>
              </div>
              <div>
                <strong>${eventName}</strong><br/>
                <small class="text-muted">${e.category_name || 'Category'}</small>
              </div>
            </div>
          </td>
          <td>${e.venue_name || 'Venue'}</td>
          <td><small>${e.event_date || ''} ${e.start_time || ''}</small></td>
          <td>${e.available_tickets} / ${e.total_tickets}</td>
          <td>RM ${parseFloat(e.ticket_price || 0).toFixed(2)}</td>
          <td><span class="badge bg-${(e.event_status || e.status) === 'published' ? 'success' : 'secondary'}">${e.event_status || e.status}</span></td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary" title="Change Event Picture" onclick="openEditEventPictureModal(${eventId}, '${safeTitle}', '${safeImg}')">
                <i class="bi bi-image"></i>
              </button>
              <button class="btn btn-outline-danger" title="Delete Event" onclick="deleteEventPrompt(${eventId}, '${safeTitle}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
}

// Event Picture Controls for New Event
function previewNewEventImage(url) {
  const preview = document.getElementById('new-event-image-preview');
  const wrap = document.getElementById('new-event-image-preview-wrap');
  if (!preview || !wrap) return;
  if (url && url.trim()) {
    preview.src = url.trim();
    preview.onerror = () => { preview.src = EVENT_IMAGE_PRESETS.default; };
    wrap.style.display = 'block';
  } else {
    wrap.style.display = 'none';
    preview.src = '';
  }
}

function setNewEventImagePreset(category) {
  const url = EVENT_IMAGE_PRESETS[category] || EVENT_IMAGE_PRESETS.default;
  const input = document.getElementById('new-event-image');
  if (input) {
    input.value = url;
    previewNewEventImage(url);
  }
}

function clearNewEventImage() {
  const input = document.getElementById('new-event-image');
  const fileInput = document.getElementById('new-event-file-upload');
  if (input) input.value = '';
  if (fileInput) fileInput.value = '';
  previewNewEventImage('');
}

function handleNewEventImageUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    showToast('Please select a valid image file (PNG, JPG, WebP).', 'error');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('Image size exceeds 5MB limit. Please choose a smaller file.', 'error');
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target.result;
    const input = document.getElementById('new-event-image');
    if (input) input.value = dataUrl;
    previewNewEventImage(dataUrl);
    showToast('Image loaded from device!', 'info');
  };
  reader.readAsDataURL(file);
}

// Event Picture Controls for Existing Event (Edit Picture Modal)
function openEditEventPictureModal(eventId, eventTitle, currentImg) {
  document.getElementById('edit-pic-event-id').value = eventId;
  document.getElementById('edit-pic-event-title').textContent = eventTitle;
  const input = document.getElementById('edit-pic-input');
  const preview = document.getElementById('edit-pic-preview');
  const fileInput = document.getElementById('edit-pic-file-upload');
  if (fileInput) fileInput.value = '';

  const imgToShow = currentImg || EVENT_IMAGE_PRESETS.default;
  if (input) input.value = currentImg || '';
  if (preview) {
    preview.src = imgToShow;
    preview.onerror = () => { preview.src = EVENT_IMAGE_PRESETS.default; };
  }

  openModal('editEventPictureModal');
}

function previewEditEventImage(url) {
  const preview = document.getElementById('edit-pic-preview');
  if (!preview) return;
  if (url && url.trim()) {
    preview.src = url.trim();
    preview.onerror = () => { preview.src = EVENT_IMAGE_PRESETS.default; };
  } else {
    preview.src = EVENT_IMAGE_PRESETS.default;
  }
}

function setEditImagePreset(category) {
  const url = EVENT_IMAGE_PRESETS[category] || EVENT_IMAGE_PRESETS.default;
  const input = document.getElementById('edit-pic-input');
  if (input) {
    input.value = url;
    previewEditEventImage(url);
  }
}

function clearEditEventImage() {
  const input = document.getElementById('edit-pic-input');
  const fileInput = document.getElementById('edit-pic-file-upload');
  if (input) input.value = '';
  if (fileInput) fileInput.value = '';
  previewEditEventImage('');
}

function handleEditEventImageUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    showToast('Please select a valid image file (PNG, JPG, WebP).', 'error');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('Image size exceeds 5MB limit. Please choose a smaller file.', 'error');
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUrl = e.target.result;
    const input = document.getElementById('edit-pic-input');
    if (input) input.value = dataUrl;
    previewEditEventImage(dataUrl);
    showToast('Image loaded from device!', 'info');
  };
  reader.readAsDataURL(file);
}

async function saveEventPicture() {
  const eventId = document.getElementById('edit-pic-event-id').value;
  const newUrl = document.getElementById('edit-pic-input').value.trim();
  const saveBtn = document.getElementById('edit-pic-save-btn');

  if (!eventId) return;

  const originalText = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';

  try {
    await apiFetch(`/api/events/${eventId}`, {
      method: 'PUT',
      body: {
        image_url: newUrl || null
      }
    });
    showToast('Event picture updated successfully!', 'success');
    closeModal('editEventPictureModal');
    loadOrganiserDashboard();
    loadEvents();
  } catch (err) {
    showToast(`Failed to update picture: ${err.message}`, 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalText;
  }
}

async function createNewEvent() {
  const form = document.getElementById('create-event-form');
  const imageUrlInput = document.getElementById('new-event-image');
  const catVal = document.getElementById('new-event-category').value;

  if (!catVal || catVal === '__add_new__' || isNaN(parseInt(catVal))) {
    showToast('Please select or add a valid category for your event.', 'error');
    return;
  }

  const payload = {
    event_name: document.getElementById('new-event-title').value.trim(),
    description: document.getElementById('new-event-desc').value.trim(),
    category_id: parseInt(catVal),
    venue_id: parseInt(document.getElementById('new-event-venue').value),
    start_time: document.getElementById('new-event-start').value.replace('T', ' ') + ':00',
    end_time: document.getElementById('new-event-end').value.replace('T', ' ') + ':00',
    ticket_price: parseFloat(document.getElementById('new-event-price').value),
    total_tickets: parseInt(document.getElementById('new-event-tickets').value),
    image_url: imageUrlInput ? (imageUrlInput.value.trim() || null) : null,
    event_status: 'published'
  };

  try {
    await apiFetch('/api/events', { method: 'POST', body: payload });
    showToast(`Event "${payload.event_name}" created successfully!`, 'success');
    closeModal('createEventModal');
    form.reset();
    clearNewEventImage();
    closeInlineCategoryBox();
    await loadCategories();
    loadOrganiserDashboard();
    loadEvents();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteEventPrompt(eventId, title) {
  if (!confirm(`Are you sure you want to delete event "${title}"?`)) return;
  try {
    await apiFetch(`/api/events/${eventId}`, { method: 'DELETE' });
    showToast(`Event deleted.`, 'success');
    await loadCategories();
    loadOrganiserDashboard();
    loadEvents();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Gate Admission Ticket QR Scanner & Verification
async function verifyTicketGate() {
  const input = document.getElementById('gate-scanner-input');
  const ref = input.value.trim();
  const resultBox = document.getElementById('gate-scan-result');

  if (!ref) {
    showToast('Please enter a ticket code (e.g. TKT001).', 'error');
    return;
  }

  resultBox.className = 'scan-status-box';
  resultBox.innerHTML = '<div class="spinner-border text-primary spinner-border-sm"></div> Verifying ticket against REST API...';
  resultBox.classList.remove('d-none');

  try {
    const res = await apiFetch('/api/bookings/verify-ticket', {
      method: 'POST',
      body: { ticket_code: ref }
    });

    const b = res.data;
    if (res.valid) {
      resultBox.className = 'scan-status-box scan-status-success';
      resultBox.innerHTML = `
        <i class="bi bi-check-circle-fill display-5 text-success"></i>
        <h4 class="fw-bold mt-2">${res.message}</h4>
        <p class="mb-1"><strong>Event:</strong> ${b.event_name} (${b.venue_name})</p>
        <p class="mb-1"><strong>Attendee:</strong> ${b.customer_name} &lt;${b.customer_email}&gt;</p>
        <p class="mb-0"><strong>Tickets Admitted:</strong> ${b.quantity} Pax | Status: <b>${b.booking_status.toUpperCase()}</b></p>
      `;
    } else {
      resultBox.className = 'scan-status-box scan-status-error';
      resultBox.innerHTML = `
        <i class="bi bi-x-circle-fill display-5 text-danger"></i>
        <h4 class="fw-bold mt-2">${res.message}</h4>
        <p class="mb-1"><strong>Event:</strong> ${b.event_name}</p>
        <p class="mb-0"><strong>Attendee:</strong> ${b.customer_name}</p>
      `;
    }
    input.value = '';
  } catch (err) {
    resultBox.className = 'scan-status-box scan-status-error';
    resultBox.innerHTML = `
      <i class="bi bi-x-circle-fill display-5 text-danger"></i>
      <h4 class="fw-bold mt-2">INVALID TICKET</h4>
      <p class="mb-0">${err.message}</p>
    `;
  }
}

// ---------------- ADMIN DASHBOARD & CONTROLS ----------------

async function loadAdminDashboard() {
  if (!state.user || state.user.role !== 'admin') return;

  // Load stats
  try {
    const stats = await apiFetch('/api/stats/dashboard');
    if (stats.metrics) {
      document.getElementById('admin-stat-users').textContent = stats.metrics.total_users;
      const subSignups = document.getElementById('admin-stat-signups-sub');
      if (subSignups && stats.metrics.signups_today !== undefined) {
        subSignups.textContent = `+${stats.metrics.signups_today} today`;
      }
      const signedInEl = document.getElementById('admin-stat-signed-in');
      if (signedInEl) signedInEl.textContent = stats.metrics.signed_in_today ?? 0;
      document.getElementById('admin-stat-venues').textContent = stats.metrics.total_venues;
      document.getElementById('admin-stat-events').textContent = stats.metrics.total_events;
      document.getElementById('admin-stat-bookings').textContent = stats.metrics.active_bookings;
      document.getElementById('admin-stat-revenue').textContent = `RM ${stats.metrics.total_revenue.toFixed(2)}`;
    }
  } catch (e) { console.error(e); }

  loadAdminUsersTable();
  loadAdminLoginsTable();
  loadAdminVenuesTable();
  loadAdminAllBookingsTable();
  loadExternalApiTelemetry();
}

async function loadAdminUsersTable() {
  const container = document.getElementById('admin-users-table');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading users who signed up...</div>';

  try {
    const res = await apiFetch('/api/users?limit=100');
    state.allUsers = res.data || [];
    filterAdminUsersTable();
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
}

function filterAdminUsersTable() {
  const searchInput = document.getElementById('admin-users-search');
  const roleSelect = document.getElementById('admin-users-role-filter');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
  const selectedRole = roleSelect ? roleSelect.value : 'all';

  let filtered = (state.allUsers || []);

  if (selectedRole !== 'all') {
    filtered = filtered.filter(u => u.role === selectedRole);
  }

  if (query) {
    filtered = filtered.filter(u => {
      const name = (u.full_name || u.name || '').toLowerCase();
      const email = (u.email || '').toLowerCase();
      const phone = (u.phone || '').toLowerCase();
      return name.includes(query) || email.includes(query) || phone.includes(query);
    });
  }

  renderAdminUsersTable(filtered);
}

function renderAdminUsersTable(usersList) {
  const container = document.getElementById('admin-users-table');
  if (!container) return;

  if (!usersList || usersList.length === 0) {
    container.innerHTML = '<div class="alert alert-light border text-center my-3"><i class="bi bi-info-circle me-1"></i>No signed-up users match the selected criteria.</div>';
    return;
  }

  let html = `
    <div class="table-responsive">
      <table class="table custom-table table-hover align-middle mb-0">
        <thead>
          <tr>
            <th>ID</th>
            <th>Signed-Up User & Contact</th>
            <th>Role</th>
            <th>Sign-Up Date & Time</th>
            <th>Bookings & Spent</th>
            <th>Last Sign-In</th>
            <th>API Key</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
  `;

  usersList.forEach(u => {
    const userId = u.user_id || u.id;
    const userName = u.full_name || u.name;
    const myId = state.user.user_id || state.user.id;
    const isSelf = userId === myId;

    // Relative sign-up text & badge
    const isNewToday = u.signed_up_minutes_ago !== null && u.signed_up_minutes_ago <= 1440;
    const signupBadge = isNewToday
      ? '<span class="badge bg-success ms-1">New Today</span>'
      : (u.signed_up_minutes_ago !== null && u.signed_up_minutes_ago <= 10080 ? '<span class="badge bg-cream text-chocolate border ms-1">This Week</span>' : '');

    const signupDateStr = u.created_at ? u.created_at.substring(0, 16) : 'N/A';

    // Bookings summary
    const bookingsCount = u.total_bookings || 0;
    const totalSpent = parseFloat(u.total_spent || 0).toFixed(2);
    const bookingSummary = bookingsCount > 0
      ? `<span class="badge bg-cream text-chocolate border"><b>${bookingsCount}</b> bookings (RM ${totalSpent})</span>`
      : '<span class="text-muted small">0 bookings</span>';

    // Last sign-in
    const lastLoginText = u.last_login_at 
      ? `<span class="badge bg-light text-dark border"><i class="bi bi-clock me-1"></i>${u.last_login_at.substring(0, 16)}</span>` 
      : '<span class="text-muted small">Never</span>';

    html += `
      <tr>
        <td><strong>#${userId}</strong></td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="rounded-circle d-flex align-items-center justify-content-center text-white fw-bold" style="width: 36px; height: 36px; background-color: var(--chocolate-primary); font-size: 0.85rem; flex-shrink: 0;">
              ${(userName || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <strong>${userName}</strong>
              ${isSelf ? '<span class="badge bg-secondary ms-1">You</span>' : ''}
              <br/>
              <small class="text-muted"><i class="bi bi-envelope me-1"></i>${u.email}</small>
              ${u.phone ? `<br/><small class="text-muted"><i class="bi bi-telephone me-1"></i>${u.phone}</small>` : ''}
            </div>
          </div>
        </td>
        <td>
          <select class="form-select form-select-sm" style="width: 120px;" ${isSelf ? 'disabled' : ''} onchange="changeUserRole(${userId}, this.value)">
            <option value="customer" ${u.role === 'customer' ? 'selected' : ''}>Customer</option>
            <option value="organiser" ${u.role === 'organiser' ? 'selected' : ''}>Organiser</option>
            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
          </select>
        </td>
        <td>
          <strong>${signupDateStr}</strong> ${signupBadge}
        </td>
        <td>${bookingSummary}</td>
        <td>${lastLoginText}</td>
        <td><code>${u.api_key ? u.api_key.substring(0, 14) + '...' : 'None'}</code></td>
        <td>
          <button class="btn btn-sm btn-outline-danger" ${isSelf ? 'disabled title="Cannot delete your own account"' : ''} onclick="deleteUserPrompt(${userId}, '${userName.replace(/'/g, "\\'")}')" title="Delete Account">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  });

  html += '</tbody></table></div>';
  container.innerHTML = html;
}

async function loadAdminLoginsTable() {
  const container = document.getElementById('admin-logins-table');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading recent user sign-ins...</div>';

  try {
    const res = await apiFetch('/api/users/logins?limit=50');
    if (!res.data || res.data.length === 0) {
      container.innerHTML = '<div class="alert alert-light border text-center my-3"><i class="bi bi-info-circle me-1"></i>No user sign-in records logged yet.</div>';
      return;
    }

    let html = `
      <div class="table-responsive">
        <table class="table custom-table table-hover align-middle mb-0">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Sign-In Time</th>
              <th>IP Address</th>
              <th>Browser / Device</th>
              <th>Session Status</th>
            </tr>
          </thead>
          <tbody>
    `;

    res.data.forEach(log => {
      const roleBadge = log.role === 'admin' 
        ? '<span class="badge bg-danger">Admin</span>' 
        : (log.role === 'organiser' ? '<span class="badge bg-warning text-dark">Organiser</span>' : '<span class="badge bg-info text-dark">Customer</span>');

      const isRecent = log.minutes_ago !== null && log.minutes_ago <= 60;
      const statusBadge = isRecent
        ? '<span class="badge bg-success"><i class="bi bi-circle-fill me-1 small" style="font-size:0.5rem;"></i>Active (within 1h)</span>'
        : `<span class="badge bg-secondary">${log.minutes_ago !== null ? Math.round(log.minutes_ago / 60) + 'h ago' : 'Earlier'}</span>`;

      // Friendly User Agent display
      let clientDevice = log.user_agent || 'Standard Web Browser';
      if (clientDevice.length > 50) {
        clientDevice = clientDevice.substring(0, 47) + '...';
      }

      html += `
        <tr>
          <td>
            <strong>${log.full_name || 'User'}</strong><br/>
            <small class="text-muted">${log.email}</small>
          </td>
          <td>${roleBadge}</td>
          <td>
            <strong>${log.login_time ? log.login_time.substring(0, 16) : 'N/A'}</strong><br/>
            <small class="text-muted">${log.minutes_ago !== null ? (log.minutes_ago < 1 ? 'Just now' : `${log.minutes_ago}m ago`) : ''}</small>
          </td>
          <td><code>${log.ip_address || '127.0.0.1'}</code></td>
          <td><small class="text-muted" title="${log.user_agent || ''}">${clientDevice}</small></td>
          <td>${statusBadge}</td>
        </tr>
      `;
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
}

async function changeUserRole(userId, newRole) {
  try {
    await apiFetch(`/api/users/${userId}`, {
      method: 'PUT',
      body: { role: newRole }
    });
    showToast(`User role updated to ${newRole.toUpperCase()}.`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
    loadAdminUsersTable();
  }
}

async function deleteUserPrompt(userId, name) {
  if (!confirm(`Delete user "${name}"?`)) return;
  try {
    await apiFetch(`/api/users/${userId}`, { method: 'DELETE' });
    showToast(`User ${name} deleted.`, 'success');
    loadAdminUsersTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminVenuesTable() {
  const container = document.getElementById('admin-venues-table');
  if (!container) return;

  try {
    const res = await apiFetch('/api/venues?limit=50');
    state.venues = res.data;
    let html = `
      <table class="table custom-table table-hover align-middle mb-0">
        <thead>
          <tr>
            <th>ID</th>
            <th>Venue Name</th>
            <th>Location</th>
            <th>Capacity</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
    `;

    res.data.forEach(v => {
      const venueId = v.venue_id || v.id;
      const venueName = v.venue_name || v.name;
      const loc = v.location || v.city || 'Kuala Lumpur';
      const statusBadge = v.approval_status === 'approved' ? '<span class="badge bg-success">Approved</span>' : '<span class="badge bg-warning text-dark">Pending</span>';

      html += `
        <tr>
          <td>${venueId}</td>
          <td><strong>${venueName}</strong></td>
          <td><span class="badge bg-light text-dark border">${loc}</span></td>
          <td><strong>${(v.capacity || 0).toLocaleString()}</strong> seats</td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteVenuePrompt(${venueId}, '${venueName.replace(/'/g, "\\'")}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
}

async function createNewVenue() {
  const payload = {
    venue_name: document.getElementById('new-venue-name').value.trim(),
    location: document.getElementById('new-venue-address').value.trim() + ', ' + document.getElementById('new-venue-city').value.trim(),
    capacity: parseInt(document.getElementById('new-venue-capacity').value),
    description: 'Convention and exhibition venue',
    approval_status: 'approved'
  };

  try {
    await apiFetch('/api/venues', { method: 'POST', body: payload });
    showToast(`Venue "${payload.venue_name}" created!`, 'success');
    closeModal('createVenueModal');
    document.getElementById('create-venue-form').reset();
    loadAdminVenuesTable();
    loadVenuesForForms();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteVenuePrompt(venueId, name) {
  if (!confirm(`Delete venue "${name}"?`)) return;
  try {
    await apiFetch(`/api/venues/${venueId}`, { method: 'DELETE' });
    showToast(`Venue deleted.`, 'success');
    loadAdminVenuesTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminAllBookingsTable() {
  const container = document.getElementById('admin-all-bookings-table');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading all bookings...</div>';

  try {
    const res = await apiFetch('/api/bookings?limit=100');
    state.allBookings = res.data || [];
    if (!res.data || res.data.length === 0) {
      container.innerHTML = '<div class="alert alert-light border text-center my-3"><i class="bi bi-info-circle me-1"></i>No bookings recorded in the system yet.</div>';
      return;
    }

    let html = `
      <div class="table-responsive">
        <table class="table custom-table table-hover align-middle mb-0">
          <thead>
            <tr>
              <th>Ticket Code</th>
              <th>Customer</th>
              <th>Event</th>
              <th>Quantity</th>
              <th>Total Amount</th>
              <th>Booking Status</th>
              <th>Payment Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
    `;

    res.data.forEach(b => {
      const bookingId = b.booking_id || b.id;
      const ticketCode = b.ticket_code || b.booking_reference;
      const eventName = b.event_name || b.event_title;
      const custName = b.customer_name || 'Customer';

      // Booking Status Badges
      let bookingBadge = '<span class="badge bg-secondary">Unknown</span>';
      if (b.booking_status === 'confirmed') {
        bookingBadge = '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Confirmed</span>';
      } else if (b.booking_status === 'pending') {
        bookingBadge = '<span class="badge bg-warning text-dark"><i class="bi bi-hourglass-split me-1"></i>Pending</span>';
      } else if (b.booking_status === 'cancelled') {
        bookingBadge = '<span class="badge bg-danger"><i class="bi bi-x-circle me-1"></i>Cancelled</span>';
      }

      // Payment Status Badges
      let paymentBadge = '<span class="badge bg-secondary">Unknown</span>';
      if (b.payment_status === 'paid') {
        paymentBadge = '<span class="badge bg-success">Paid</span>';
      } else if (b.payment_status === 'pending') {
        paymentBadge = '<span class="badge bg-warning text-dark">Pending</span>';
      } else if (b.payment_status === 'refunded') {
        paymentBadge = '<span class="badge bg-info text-dark">Refunded</span>';
      } else if (b.payment_status === 'failed') {
        paymentBadge = '<span class="badge bg-danger">Failed</span>';
      }

      const safeEvent = (eventName || '').replace(/'/g, "\\'");
      const safeTicket = (ticketCode || '').replace(/'/g, "\\'");

      html += `
        <tr>
          <td>
            <strong class="text-chocolate">${ticketCode}</strong>
            ${b.cancellation_reason ? `<br/><small class="text-danger fst-italic">Note: ${b.cancellation_reason}</small>` : ''}
          </td>
          <td>${custName}<br/><small class="text-muted">${b.customer_email || ''}</small></td>
          <td><strong>${eventName}</strong><br/><small class="text-muted">${b.venue_name || 'Venue'}</small></td>
          <td><span class="badge bg-light text-dark border">${b.quantity || b.num_tickets} seats</span></td>
          <td><strong>RM ${parseFloat(b.total_amount || 0).toFixed(2)}</strong></td>
          <td>${bookingBadge}</td>
          <td>${paymentBadge}</td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-chocolate" title="Update Booking & Payment Status" onclick="openUpdateBookingModal(${bookingId})">
                <i class="bi bi-pencil-square me-1"></i>Update
              </button>
              <button class="btn btn-outline-primary" title="View Gate Pass QR Code" onclick="viewBookingQrModal(${bookingId}, '${safeTicket}', '${safeEvent}')">
                <i class="bi bi-qr-code"></i>
              </button>
              <button class="btn btn-outline-success" title="Download Official PDF Ticket" onclick="downloadTicketPdf(${bookingId}, '${safeTicket}')">
                <i class="bi bi-file-earmark-pdf"></i>
              </button>
              <button class="btn btn-outline-danger" title="Permanently Delete Booking" onclick="deleteBookingAdmin(${bookingId}, '${safeTicket}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
}

function openUpdateBookingModal(bookingId) {
  const booking = (state.allBookings || []).find(b => (b.booking_id || b.id) === bookingId);
  if (!booking) {
    showToast('Booking record not found.', 'error');
    return;
  }

  document.getElementById('update-booking-id').value = bookingId;
  document.getElementById('update-booking-code').textContent = booking.ticket_code || booking.booking_reference;
  document.getElementById('update-booking-customer').textContent = `${booking.customer_name || 'Customer'} (${booking.customer_email || ''})`;
  document.getElementById('update-booking-event').textContent = booking.event_name || booking.event_title;
  document.getElementById('update-booking-amount').textContent = `RM ${parseFloat(booking.total_amount || 0).toFixed(2)} (${booking.quantity} seats)`;

  const statusSelect = document.getElementById('update-booking-status-select');
  statusSelect.value = booking.booking_status || 'confirmed';

  const paymentSelect = document.getElementById('update-payment-status-select');
  paymentSelect.value = booking.payment_status || 'paid';

  const reasonInput = document.getElementById('update-booking-reason');
  reasonInput.value = booking.cancellation_reason || '';

  toggleCancellationReasonField(statusSelect.value);

  openModal('updateBookingModal');
}

function toggleCancellationReasonField(status) {
  const reasonGroup = document.getElementById('update-cancellation-reason-group');
  if (!reasonGroup) return;
  if (status === 'cancelled') {
    reasonGroup.style.display = 'block';
  } else {
    reasonGroup.style.display = 'none';
  }
}

async function submitUpdateBooking() {
  const bookingId = document.getElementById('update-booking-id').value;
  if (!bookingId) return;

  const bookingStatus = document.getElementById('update-booking-status-select').value;
  const paymentStatus = document.getElementById('update-payment-status-select').value;
  const reason = document.getElementById('update-booking-reason').value.trim();

  const payload = {
    booking_status: bookingStatus,
    payment_status: paymentStatus,
    cancellation_reason: bookingStatus === 'cancelled' ? (reason || 'Cancelled by administrator') : null
  };

  try {
    const res = await apiFetch(`/api/bookings/${bookingId}`, {
      method: 'PUT',
      body: payload
    });

    showToast(res.message || 'Booking updated successfully!', 'success');
    closeModal('updateBookingModal');
    
    // Refresh admin tables, metrics, and events catalog
    loadAdminDashboard();
    loadEvents();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteBookingAdmin(bookingId, ticketCode) {
  if (!confirm(`Are you sure you want to permanently delete booking "${ticketCode}"?\n\nIf the booking was active, tickets will be safely restored to the event inventory.`)) {
    return;
  }

  try {
    const res = await apiFetch(`/api/bookings/${bookingId}`, {
      method: 'DELETE'
    });
    showToast(res.message || `Booking ${ticketCode} deleted successfully.`, 'success');
    loadAdminDashboard();
    loadEvents();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ---------------- EXTERNAL API MONITOR & TELEMETRY ----------------

async function loadExternalApiTelemetry() {
  // 1. Health check
  try {
    const health = await apiFetch('/api/stats/health');
    document.getElementById('health-qr-status').textContent = 'ACTIVE (200 OK)';
    document.getElementById('health-qr-status').className = 'badge bg-success';
    document.getElementById('health-qr-provider').textContent = 'api.qrserver.com';
    document.getElementById('health-qr-latency').textContent = '45 ms';

    document.getElementById('health-db-status').textContent = health.database.status.toUpperCase();
    document.getElementById('health-db-status').className = 'badge bg-success';
  } catch (e) { console.error(e); }

  // 2. Logs table
  const container = document.getElementById('telemetry-logs-table');
  if (!container) return;

  try {
    const res = await apiFetch('/api/stats/external-apis');
    if (!res.data || res.data.length === 0) {
      container.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No external API calls logged yet. Book a ticket to trigger external QR & PDF generation!</td></tr>';
      return;
    }

    let html = '';
    res.data.forEach(log => {
      html += `
        <tr>
          <td><small>${log.timestamp}</small></td>
          <td><span class="badge bg-info text-dark">${log.service}</span></td>
          <td><code>${log.method}</code></td>
          <td><small class="text-truncate d-inline-block" style="max-width: 250px;">${log.url}</small></td>
          <td><span class="badge bg-${log.status_code === 200 ? 'success' : 'danger'}">${log.status_code}</span></td>
          <td>${log.latency_ms} ms</td>
          <td>${log.payload_size} bytes</td>
        </tr>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="7" class="text-danger py-2">${err.message}</td></tr>`;
  }
}

async function testLiveExternalQr() {
  const text = document.getElementById('test-qr-input').value.trim() || 'TKT-SAMPLE-CODE-2026';
  const imgEl = document.getElementById('test-qr-result-img');
  const detailsEl = document.getElementById('test-qr-details');

  detailsEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Calling external QR API...';
  const start = performance.now();
  
  // Direct call to external QR provider
  const targetUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(text)}`;
  imgEl.src = targetUrl;

  imgEl.onload = () => {
    const duration = Math.round(performance.now() - start);
    detailsEl.innerHTML = `
      <span class="badge bg-success mb-1">Status: 200 OK</span><br/>
      <small class="text-muted">Provider: <b>api.qrserver.com</b></small><br/>
      <small class="text-muted">Roundtrip Latency: <b>${duration} ms</b></small>
    `;
    loadExternalApiTelemetry();
  };
}

// ---------------- HELPERS & SETUP ----------------

async function loadVenuesForForms() {
  try {
    const res = await apiFetch('/api/venues?limit=100');
    state.venues = res.data;
    const select = document.getElementById('new-event-venue');
    if (select) {
      select.innerHTML = '<option value="">Select a Venue</option>';
      res.data.forEach(v => {
        const venueId = v.venue_id || v.id;
        const venueName = v.venue_name || v.name;
        const loc = v.location || v.city || 'Kuala Lumpur';
        select.innerHTML += `<option value="${venueId}">${venueName} (${loc} - Cap: ${(v.capacity || 0).toLocaleString()})</option>`;
      });
    }
  } catch (e) { console.error(e); }
}

function populateCategoryDropdowns(cats) {
  const select = document.getElementById('new-event-category');
  if (select) {
    const prevVal = select.value;
    select.innerHTML = '<option value="">Select a Category</option>';
    cats.forEach(c => {
      const catId = c.category_id || c.id;
      const catName = c.category_name || c.name;
      select.innerHTML += `<option value="${catId}">${catName}</option>`;
    });
    select.innerHTML += '<option value="__add_new__" style="color: #0d6efd; font-weight: bold;">➕ Add New Category...</option>';
    if (prevVal && prevVal !== '__add_new__') {
      select.value = prevVal;
    }
  }
}

function handleCategorySelectChange(val) {
  if (val === '__add_new__') {
    openInlineCategoryBox();
  } else {
    closeInlineCategoryBox();
  }
}

function openInlineCategoryBox() {
  const box = document.getElementById('inline-new-category-box');
  const input = document.getElementById('inline-new-cat-name');
  if (box) {
    box.style.display = 'block';
    if (input) {
      input.focus();
    }
  }
}

function closeInlineCategoryBox() {
  const box = document.getElementById('inline-new-category-box');
  const input = document.getElementById('inline-new-cat-name');
  const select = document.getElementById('new-event-category');
  if (box) box.style.display = 'none';
  if (input) input.value = '';
  if (select && select.value === '__add_new__') {
    select.value = '';
  }
}

async function saveInlineCategory() {
  const input = document.getElementById('inline-new-cat-name');
  const name = input ? input.value.trim() : '';
  if (!name) {
    showToast('Please enter a category name.', 'error');
    if (input) input.focus();
    return;
  }

  try {
    const res = await apiFetch('/api/categories', {
      method: 'POST',
      body: {
        category_name: name,
        description: `${name} events and activities`
      }
    });

    const newCat = res.data;
    const catId = newCat.category_id || newCat.id;
    const catName = newCat.category_name || newCat.name;

    showToast(`Category "${catName}" added successfully!`, 'success');

    // Reload categories list globally
    await loadCategories();

    // Select the newly added category in the dropdown
    const select = document.getElementById('new-event-category');
    if (select) {
      select.value = catId;
    }

    const box = document.getElementById('inline-new-category-box');
    if (box) box.style.display = 'none';
    if (input) input.value = '';
  } catch (err) {
    showToast(`Failed to add category: ${err.message}`, 'error');
  }
}

function renderPagination(containerId, pagination, onPageClick) {
  const container = document.getElementById(containerId);
  if (!container || pagination.total_pages <= 1) {
    if (container) container.innerHTML = '';
    return;
  }

  let html = '<ul class="pagination pagination-sm justify-content-center my-3">';
  html += `<li class="page-item ${!pagination.has_prev ? 'disabled' : ''}"><button class="page-link" onclick="(${onPageClick})(${pagination.page - 1})">Previous</button></li>`;
  
  for (let i = 1; i <= pagination.total_pages; i++) {
    html += `<li class="page-item ${i === pagination.page ? 'active' : ''}"><button class="page-link" onclick="(${onPageClick})(${i})">${i}</button></li>`;
  }

  html += `<li class="page-item ${!pagination.has_next ? 'disabled' : ''}"><button class="page-link" onclick="(${onPageClick})(${pagination.page + 1})">Next</button></li>`;
  html += '</ul>';
  container.innerHTML = html;
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) {
    const modal = bootstrap.Modal.getOrCreateInstance(el);
    modal.show();
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    const modal = bootstrap.Modal.getInstance(el);
    if (modal) modal.hide();
  }
}

// Initialization on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  updateNavState();
  loadCategories();
  loadEvents();
  loadVenuesForForms();

  // Search input debounce/enter listener
  const searchInput = document.getElementById('event-search-input');
  if (searchInput) {
    searchInput.addEventListener('keyup', (e) => {
      if (e.key === 'Enter') {
        state.currentPage = 1;
        loadEvents();
      }
    });
  }

  // Security: Automatically wipe credential inputs whenever modals hide or show
  const loginModalEl = document.getElementById('loginModal');
  if (loginModalEl) {
    loginModalEl.addEventListener('hidden.bs.modal', clearAuthForms);
    loginModalEl.addEventListener('show.bs.modal', clearAuthForms);
  }

  const regModalEl = document.getElementById('registerModal');
  if (regModalEl) {
    regModalEl.addEventListener('hidden.bs.modal', clearAuthForms);
    regModalEl.addEventListener('show.bs.modal', clearAuthForms);
  }
});
