/**
 * Bullz Platform - Python & MongoDB Edition
 * Main Interactive Application Script
 */

// Global State
const state = {
  currentUser: null,
  token: null,
  activeAdminTab: 'clients',
  adminClients: [],
  selectedClient: null,
  activeLedgerClient: null,
  currentPlanSelection: {
    amount: 500,
    tenure: '4 Month',
    ratePercent: 5,
    term: 'Short Term'
  }
};

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  loadStoredAuth();
  updateNavAuthState();
  initTypewriter();
  initCalculator();
  hideLoader();

  // If on admin page and logged in as admin, load admin dashboard
  if (window.location.pathname.includes('/admin') && state.currentUser && state.currentUser.role === 'admin') {
    loadAdminDashboard();
  }
  // If on portfolio page and logged in, load portfolio
  if (window.location.pathname.includes('/portfolio')) {
    if (!state.currentUser) {
      window.location.href = '/login';
    } else {
      loadPortfolioPage();
    }
  }

  // Poll notifications if admin
  if (state.currentUser && state.currentUser.role === 'admin') {
    fetchNotifications();
    setInterval(fetchNotifications, 15000);
  }
});

// Hide loader
function hideLoader() {
  const loader = document.getElementById('pageLoader');
  if (loader) {
    setTimeout(() => {
      loader.classList.add('done');
    }, 350);
  }
}

// Toast Notification
function showToast(message, type = 'info') {
  let toast = document.getElementById('bullzToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'bullzToast';
    toast.className = 'custom-alert-toast';
    document.body.appendChild(toast);
  }
  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `<span style="font-size:16px;">${icon}</span> <span>${message}</span>`;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

// Theme Handling
function initTheme() {
  const saved = localStorage.getItem('bullz_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  const themeBtn = document.getElementById('themeBtn');
  if (themeBtn) {
    themeBtn.textContent = saved === 'light' ? '☀️' : '🌙';
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('bullz_theme', next);
  const themeBtn = document.getElementById('themeBtn');
  if (themeBtn) {
    themeBtn.textContent = next === 'light' ? '☀️' : '🌙';
  }
}

// Auth State Persistence
function loadStoredAuth() {
  try {
    const storedUser = localStorage.getItem('bullz_user');
    const storedToken = localStorage.getItem('bullz_token');
    if (storedUser) {
      state.currentUser = JSON.parse(storedUser);
      state.token = storedToken;
    }
  } catch (e) {
    console.warn('Could not parse stored auth:', e);
  }
}

function saveAuth(user, token) {
  state.currentUser = user;
  state.token = token;
  localStorage.setItem('bullz_user', JSON.stringify(user));
  if (token) localStorage.setItem('bullz_token', token);
  updateNavAuthState();
}

function logout() {
  state.currentUser = null;
  state.token = null;
  localStorage.removeItem('bullz_user');
  localStorage.removeItem('bullz_token');
  showToast('Logged out successfully', 'info');
  setTimeout(() => {
    window.location.href = '/';
  }, 400);
}

function updateNavAuthState() {
  const navGreeting = document.getElementById('navUserGreeting');
  const greetingName = document.getElementById('navGreetingName');
  const navUserLogin = document.getElementById('navUserLoginItem');
  const navAdminLogin = document.getElementById('navAdminLoginItem');
  const navPortfolio = document.getElementById('navPortfolioItem');
  const navProfileBtn = document.getElementById('navProfileBtn');
  const navNotif = document.getElementById('navNotifItem');

  if (state.currentUser) {
    if (navGreeting) {
      navGreeting.style.display = 'flex';
      if (greetingName) greetingName.textContent = state.currentUser.name || 'User';
    }
    if (navUserLogin) navUserLogin.style.display = 'none';
    if (navAdminLogin) navAdminLogin.style.display = state.currentUser.role === 'admin' ? 'none' : 'block';
    if (navPortfolio) navPortfolio.style.display = 'block';
    if (navProfileBtn) navProfileBtn.style.display = 'grid';

    if (state.currentUser.role === 'admin') {
      if (navNotif) navNotif.style.display = 'block';
      if (navPortfolio) {
        const link = navPortfolio.querySelector('a');
        if (link) {
          link.innerHTML = '🛡️ Admin Center';
          link.setAttribute('href', '/admin');
        }
      }
    }
  } else {
    if (navGreeting) navGreeting.style.display = 'none';
    if (navUserLogin) navUserLogin.style.display = 'block';
    if (navAdminLogin) navAdminLogin.style.display = 'block';
    if (navPortfolio) navPortfolio.style.display = 'none';
    if (navProfileBtn) navProfileBtn.style.display = 'none';
    if (navNotif) navNotif.style.display = 'none';
  }
}

// Typewriter Hero Animation
function initTypewriter() {
  const el = document.getElementById('typewriterText');
  if (!el) return;
  const words = [
    'Grow Your Money with Bullz get 10% return',
    'Disciplined Monthly Ledger & Direct Payouts',
    'Compound Your Capital with High Transparency'
  ];
  let wordIdx = 0, charIdx = 0, isDeleting = false;

  function type() {
    const current = words[wordIdx];
    if (isDeleting) {
      el.textContent = current.substring(0, charIdx - 1);
      charIdx--;
    } else {
      el.textContent = current.substring(0, charIdx + 1);
      charIdx++;
    }

    let speed = isDeleting ? 30 : 70;
    if (!isDeleting && charIdx === current.length) {
      speed = 2200;
      isDeleting = true;
    } else if (isDeleting && charIdx === 0) {
      isDeleting = false;
      wordIdx = (wordIdx + 1) % words.length;
      speed = 400;
    }
    setTimeout(type, speed);
  }
  type();
}

// Auth Handlers (User & Admin)
async function handleUserLogin(e) {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  const submitBtn = e.target.querySelector('button[type="submit"]');

  if (submitBtn) submitBtn.disabled = true;
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role: 'user' })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');

    saveAuth(data.user, data.token);
    showToast(`Welcome back, ${data.user.name}!`, 'success');
    setTimeout(() => {
      window.location.href = '/portfolio';
    }, 600);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleAdminLogin(e) {
  e.preventDefault();
  const email = document.getElementById('adminLoginEmail').value.trim();
  const password = document.getElementById('adminLoginPassword').value;
  const submitBtn = e.target.querySelector('button[type="submit"]');

  if (submitBtn) submitBtn.disabled = true;
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role: 'admin' })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Admin authentication failed');

    saveAuth(data.user, data.token);
    showToast(`Admin Console Unlocked! Welcome ${data.user.name}`, 'success');
    setTimeout(() => {
      window.location.href = '/admin';
    }, 600);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleSignup(e) {
  e.preventDefault();
  const name = document.getElementById('signupName').value.trim();
  const email = document.getElementById('signupEmail').value.trim();
  const phone = document.getElementById('signupPhone').value.trim();
  const password = document.getElementById('signupPassword').value;
  const confirm = document.getElementById('signupConfirm').value;
  const submitBtn = e.target.querySelector('button[type="submit"]');

  if (password !== confirm) {
    showToast('Passwords do not match!', 'error');
    return;
  }

  if (submitBtn) submitBtn.disabled = true;
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');

    saveAuth(data.user, data.token);
    showToast('Account created successfully! Welcome to Bullz', 'success');
    setTimeout(() => {
      window.location.href = '/plans';
    }, 700);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function fillDemoLogin(email, pw) {
  const eInput = document.getElementById('loginEmail') || document.getElementById('adminLoginEmail');
  const pInput = document.getElementById('loginPassword') || document.getElementById('adminLoginPassword');
  if (eInput) eInput.value = email;
  if (pInput) pInput.value = pw;
}

// Contact Form Handler
function handleContactSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('contactName').value;
  showToast(`Thank you, ${name}! Your query has been received. Our team will contact you shortly.`, 'success');
  e.target.reset();
}

// Interactive Investment Calculator
function initCalculator() {
  const amtInput = document.getElementById('calcAmountInput');
  const tenureSelect = document.getElementById('calcTenureSelect');
  const rateChips = document.querySelectorAll('.rate-chip');

  if (!amtInput) return;

  function updateCalc() {
    const raw = amtInput.value ? amtInput.value.trim() : '';
    let amount = parseFloat(raw);
    if (isNaN(amount) || amount < 0) {
      amount = 0;
    }
    const tenure = tenureSelect ? tenureSelect.value : '4 Month';
    const activeRateChip = document.querySelector('.rate-chip.active');
    const ratePercent = activeRateChip ? parseFloat(activeRateChip.getAttribute('data-rate')) : 5;

    let months = 4;
    const m = tenure.match(/\d+/);
    if (m) {
      months = parseInt(m[0], 10);
      if (/year/i.test(tenure)) months *= 12;
    }

    const monthlyProfit = Math.round((amount * ratePercent) / 100);
    const totalProfit = Math.round(monthlyProfit * months);
    const totalMaturity = Math.round(amount + totalProfit);

    state.currentPlanSelection = {
      amount,
      tenure,
      ratePercent,
      term: months >= 12 ? 'Long Term' : 'Short Term',
      monthlyProfit,
      totalProfit,
      totalMaturity
    };

    // Update display values
    const dMonthly = document.getElementById('calcMonthlyReturn');
    const dTotal = document.getElementById('calcTotalReturn');
    const dMaturity = document.getElementById('calcMaturityAmount');
    const dDuration = document.getElementById('calcDisplayDuration');

    if (dMonthly) dMonthly.textContent = `₹${monthlyProfit.toLocaleString()}`;
    if (dTotal) dTotal.textContent = `₹${totalProfit.toLocaleString()}`;
    if (dMaturity) dMaturity.textContent = `₹${totalMaturity.toLocaleString()}`;
    if (dDuration) dDuration.textContent = `${tenure} (${ratePercent}% monthly)`;
  }

  amtInput.addEventListener('input', updateCalc);
  if (tenureSelect) tenureSelect.addEventListener('change', updateCalc);

  rateChips.forEach(chip => {
    chip.addEventListener('click', () => {
      rateChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      updateCalc();
    });
  });

  updateCalc();
}

function setCalcAmount(val) {
  const amtInput = document.getElementById('calcAmountInput');
  if (amtInput) {
    amtInput.value = val;
    initCalculator();
  }
}

// Payment Checkout Modal
function openPaymentModal(customPlan = null) {
  if (!state.currentUser) {
    showToast('Please log in or sign up before investing', 'info');
    setTimeout(() => {
      window.location.href = '/login';
    }, 700);
    return;
  }

  // If amount was edited in calculator, preserve it
  const amtInput = document.getElementById('calcAmountInput');
  if (!customPlan && amtInput && parseFloat(amtInput.value)) {
    state.currentPlanSelection.amount = parseFloat(amtInput.value);
  }

  const plan = customPlan || state.currentPlanSelection;
  if (!plan.amount || plan.amount < 500) {
    plan.amount = 500;
  }

  const overlay = document.getElementById('paymentModalOverlay');
  if (!overlay) return;

  const dAmt = document.getElementById('payModalAmount');
  const dInput = document.getElementById('payModalAmountInput');
  const dTenure = document.getElementById('payModalTenure');
  const dRate = document.getElementById('payModalRate');

  if (dAmt) dAmt.textContent = `₹${plan.amount.toLocaleString()}`;
  if (dInput) dInput.value = plan.amount;
  if (dTenure) dTenure.textContent = plan.tenure;
  if (dRate) dRate.textContent = `${plan.ratePercent}% Monthly`;

  overlay.classList.add('open');
}

function handlePayModalAmountInput(val) {
  const num = parseFloat(val);
  const validNum = (!isNaN(num) && num > 0) ? num : 0;
  state.currentPlanSelection.amount = validNum;
  const dAmt = document.getElementById('payModalAmount');
  if (dAmt) {
    dAmt.textContent = `₹${validNum.toLocaleString()}`;
  }
}

function setPayModalAmount(val) {
  const dInput = document.getElementById('payModalAmountInput');
  if (dInput) {
    dInput.value = val;
    handlePayModalAmountInput(val);
  }
}

function closePaymentModal() {
  const overlay = document.getElementById('paymentModalOverlay');
  if (overlay) overlay.classList.remove('open');
}

function switchPayTab(tabName) {
  document.querySelectorAll('.pay-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.pay-tab-content').forEach(c => c.classList.remove('active'));

  const tabBtn = document.getElementById(`payTab_${tabName}`);
  const content = document.getElementById(`payContent_${tabName}`);
  if (tabBtn) tabBtn.classList.add('active');
  if (content) content.classList.add('active');
}

async function executePayment(method = 'UPI') {
  if (!state.currentUser) {
    showToast('Please log in first', 'error');
    return;
  }

  const dInput = document.getElementById('payModalAmountInput');
  if (dInput && dInput.value) {
    const parsed = parseFloat(dInput.value);
    if (!isNaN(parsed)) {
      state.currentPlanSelection.amount = parsed;
    }
  }

  const plan = state.currentPlanSelection;
  if (!plan.amount || plan.amount < 500) {
    showToast('Minimum starting investment amount is ₹500. Please enter ₹500 or more.', 'error');
    if (dInput) dInput.focus();
    return;
  }

  showToast('Creating payment order...', 'info');

  try {
    // 1. Create order
    const orderRes = await fetch('/api/payments/create-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: plan.amount,
        userEmail: state.currentUser.email,
        userName: state.currentUser.name,
        planDetails: plan
      })
    });
    const orderData = await orderRes.json();
    if (!orderRes.ok) throw new Error(orderData.detail || 'Could not initiate payment');

    // 2. Complete payment
    const verifyRes = await fetch('/api/payments/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        orderId: orderData.orderId,
        paymentId: `PAY_BULLZ_${Date.now()}`,
        method: method,
        userEmail: state.currentUser.email,
        plan: plan
      })
    });
    const verifyData = await verifyRes.json();
    if (!verifyRes.ok) throw new Error(verifyData.detail || 'Payment verification failed');

    closePaymentModal();
    showToast(`Payment of ₹${plan.amount.toLocaleString()} Successful! Plan Activated.`, 'success');

    // If on portfolio, refresh
    if (window.location.pathname.includes('/portfolio')) {
      setTimeout(loadPortfolioPage, 1000);
    } else {
      setTimeout(() => {
        window.location.href = '/portfolio';
      }, 1200);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// User Portfolio Loader
async function loadPortfolioPage() {
  if (!state.currentUser) return;
  const email = state.currentUser.email;

  try {
    const res = await fetch(`/api/ledger?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch portfolio');

    const summary = data.summary || {};
    const entries = data.entries || [];

    // Render KPI Cards
    const kpiBalance = document.getElementById('portCurrentBalance');
    const kpiInvested = document.getElementById('portTotalInvested');
    const kpiProfit = document.getElementById('portTotalProfit');
    const kpiRate = document.getElementById('portCurrentRate');
    const kpiName = document.getElementById('portUserName');
    const kpiEmail = document.getElementById('portUserEmail');
    const kpiCount = document.getElementById('portEntryCount');

    if (kpiBalance) kpiBalance.textContent = `₹${(summary.currentBalance || 0).toLocaleString()}`;
    if (kpiInvested) kpiInvested.textContent = `₹${(summary.totalInvested || 0).toLocaleString()}`;
    if (kpiProfit) kpiProfit.textContent = `₹${(summary.totalInterest || 0).toLocaleString()}`;
    if (kpiRate) kpiRate.textContent = summary.latestRate || '10%';
    if (kpiName) kpiName.textContent = state.currentUser.name;
    if (kpiEmail) kpiEmail.textContent = state.currentUser.email;
    if (kpiCount) kpiCount.textContent = summary.entryCount || entries.length;

    // Render Table
    const tbody = document.getElementById('portfolioLedgerTbody');
    const mobileContainer = document.getElementById('portfolioLedgerMobileCards');

    if (tbody) {
      if (entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--mute);">No ledger records yet. Invest in a plan to start compounding!</td></tr>`;
      } else {
        tbody.innerHTML = entries.map(row => `
          <tr>
            <td class="col-date">${row.entryDate || ''}</td>
            <td class="col-amount">₹${(row.investmentAdded || 0).toLocaleString()}</td>
            <td class="col-prev">₹${(row.previousBalance || 0).toLocaleString()}</td>
            <td class="col-rate"><span class="badge-rate r10">${row.rate || 10}%</span></td>
            <td class="col-interest">+₹${(row.interest || 0).toLocaleString()}</td>
            <td class="col-total">₹${(row.totalBalance || 0).toLocaleString()}</td>
            <td class="col-note">${row.note || 'Monthly compound accrual'}</td>
          </tr>
        `).join('');
      }
    }

    if (mobileContainer) {
      if (entries.length === 0) {
        mobileContainer.innerHTML = `<div style="text-align:center; padding:20px; color:var(--mute);">No ledger records yet.</div>`;
      } else {
        mobileContainer.innerHTML = entries.map(row => `
          <div class="ledger-mobile-card">
            <div class="ledger-mobile-card-head">
              <strong style="color:var(--mint);">${row.entryDate}</strong>
              <span class="badge-rate r10">${row.rate || 10}%</span>
            </div>
            <div class="ledger-mobile-card-row"><span>Added:</span> <b>₹${(row.investmentAdded || 0).toLocaleString()}</b></div>
            <div class="ledger-mobile-card-row"><span>Prev Balance:</span> <b>₹${(row.previousBalance || 0).toLocaleString()}</b></div>
            <div class="ledger-mobile-card-row"><span>Interest:</span> <b style="color:var(--mint);">+₹${(row.interest || 0).toLocaleString()}</b></div>
            <div class="ledger-mobile-card-row"><span>Total Balance:</span> <b style="color:var(--gold);">₹${(row.totalBalance || 0).toLocaleString()}</b></div>
            <div class="ledger-mobile-card-row"><span>Note:</span> <small style="color:var(--mute);">${row.note || '-'}</small></div>
          </div>
        `).join('');
      }
    }

  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Export Ledger to CSV
function exportLedgerCSV() {
  const table = document.getElementById('portfolioLedgerTable');
  if (!table) return;

  let csv = [];
  const rows = table.querySelectorAll('tr');
  rows.forEach(row => {
    const cols = row.querySelectorAll('th, td');
    const rowData = [];
    cols.forEach(col => {
      let text = col.innerText.replace(/(\r\n|\n|\r)/gm, '').trim();
      text = text.replace(/"/g, '""');
      rowData.push(`"${text}"`);
    });
    csv.push(rowData.join(','));
  });

  const csvString = csv.join('\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.setAttribute('href', url);
  a.setAttribute('download', `Bullz_Compound_Ledger_${Date.now()}.csv`);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast('Ledger exported to CSV successfully', 'success');
}

// Profile Modal Handlers
function openProfileModal() {
  if (!state.currentUser) return;
  const overlay = document.getElementById('profileModalOverlay');
  if (!overlay) return;

  const nInput = document.getElementById('profileModalName');
  const eInput = document.getElementById('profileModalEmail');
  const pInput = document.getElementById('profileModalPhone');

  if (nInput) nInput.value = state.currentUser.name || '';
  if (eInput) eInput.value = state.currentUser.email || '';
  if (pInput) pInput.value = state.currentUser.phone || '';

  overlay.classList.add('open');
}

function closeProfileModal() {
  const overlay = document.getElementById('profileModalOverlay');
  if (overlay) overlay.classList.remove('open');
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const name = document.getElementById('profileModalName').value.trim();
  const phone = document.getElementById('profileModalPhone').value.trim();
  const password = document.getElementById('profileModalPassword').value;

  try {
    const res = await fetch('/api/auth/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: state.currentUser.email,
        name,
        phone,
        password: password || undefined
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Profile update failed');

    state.currentUser.name = name;
    state.currentUser.phone = phone;
    saveAuth(state.currentUser, state.token);
    closeProfileModal();
    showToast('Profile updated successfully!', 'success');
    if (window.location.pathname.includes('/portfolio')) {
      loadPortfolioPage();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// =========================================================================
// ADMIN CONSOLE LOGIC
// =========================================================================

function switchAdminTab(tabKey) {
  state.activeAdminTab = tabKey;
  document.querySelectorAll('.adm-tab').forEach(b => b.classList.remove('on'));
  document.querySelectorAll('.adm-panel').forEach(p => p.classList.remove('on'));

  const btn = document.getElementById(`tabBtn_${tabKey}`);
  const panel = document.getElementById(`panel_${tabKey}`);
  if (btn) btn.classList.add('on');
  if (panel) panel.classList.add('on');
}

async function loadAdminDashboard() {
  try {
    const res = await fetch('/api/admin/clients');
    const clients = await res.json();
    if (!res.ok) throw new Error(clients.detail || 'Failed to fetch admin data');

    state.adminClients = clients;

    // Calculate Admin KPIs
    const totalAUM = clients.reduce((sum, c) => sum + (c.totalAmount || 0), 0);
    const activeClientsCount = clients.length;
    const monthlyPayout = clients.reduce((sum, c) => sum + (c.monthlyPayout || 0), 0);
    const totalInvestmentsCount = clients.reduce((sum, c) => sum + (c.totalInvestments || 0), 0);

    const kpiAum = document.getElementById('adminKpiAum');
    const kpiClients = document.getElementById('adminKpiClients');
    const kpiPayout = document.getElementById('adminKpiPayout');
    const kpiInvs = document.getElementById('adminKpiInvs');

    if (kpiAum) kpiAum.textContent = `₹${totalAUM.toLocaleString()}`;
    if (kpiClients) kpiClients.textContent = activeClientsCount;
    if (kpiPayout) kpiPayout.textContent = `₹${monthlyPayout.toLocaleString()}`;
    if (kpiInvs) kpiInvs.textContent = totalInvestmentsCount;

    renderAdminClientsList(clients);
    populateLedgerClientSelect(clients);
    loadAllInvestmentsTab();
    fetchNotifications();

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderAdminClientsList(clients) {
  const tbody = document.getElementById('adminClientsTbody');
  if (!tbody) return;

  if (clients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="adm-empty">No clients found yet. Click "+ Onboard New Client" to add one!</td></tr>`;
    return;
  }

  tbody.innerHTML = clients.map(c => `
    <tr onclick="openClientDrawer('${c.id}')">
      <td class="cc">
        <div class="av">${(c.name || 'U').charAt(0).toUpperCase()}</div>
        <div>
          <b>${c.name}</b><br>
          <small>${c.email}</small>
        </div>
      </td>
      <td>₹${(c.totalAmount || 0).toLocaleString()}</td>
      <td><span class="badge-rate r10">${c.rate || '10%'}</span></td>
      <td>₹${(c.monthlyPayout || 0).toLocaleString()}</td>
      <td>${c.startDate || 'Recent'}</td>
      <td>
        <button class="btn-ledger-edit" onclick="event.stopPropagation(); inspectClientLedger('${c.email}')">📊 Ledger</button>
      </td>
    </tr>
  `).join('');
}

function filterClients() {
  const q = (document.getElementById('clientSearchInput')?.value || '').toLowerCase();
  const filtered = state.adminClients.filter(c =>
    (c.name || '').toLowerCase().includes(q) || (c.email || '').toLowerCase().includes(q)
  );
  renderAdminClientsList(filtered);
}

// Client Drawer / Inspector
function openClientDrawer(clientId) {
  const client = state.adminClients.find(c => String(c.id) === String(clientId));
  if (!client) return;
  state.selectedClient = client;

  const drawer = document.getElementById('admDrawer');
  if (!drawer) return;

  document.getElementById('drawerClientName').textContent = client.name;
  document.getElementById('drawerClientEmail').textContent = client.email;
  document.getElementById('drawerBalance').textContent = `₹${(client.totalAmount || 0).toLocaleString()}`;
  document.getElementById('drawerRate').textContent = client.rate || '10%';
  document.getElementById('drawerPayout').textContent = `₹${(client.monthlyPayout || 0).toLocaleString()}`;

  drawer.classList.add('open');
}

function closeClientDrawer() {
  const drawer = document.getElementById('admDrawer');
  if (drawer) drawer.classList.remove('open');
}

// Onboard Client Modal
function openCreateClientModal() {
  const overlay = document.getElementById('clientCreateModalOverlay');
  if (overlay) overlay.classList.add('open');
}

function closeCreateClientModal() {
  const overlay = document.getElementById('clientCreateModalOverlay');
  if (overlay) overlay.classList.remove('open');
}

async function handleAdminCreateClient(e) {
  e.preventDefault();
  const name = document.getElementById('createClientName').value.trim();
  const email = document.getElementById('createClientEmail').value.trim();
  const password = document.getElementById('createClientPassword').value;
  const phone = document.getElementById('createClientPhone').value.trim();
  const startDate = document.getElementById('createClientStartDate').value;
  const initialAmount = parseFloat(document.getElementById('createClientInitialAmount').value) || 0;
  const initialRate = parseFloat(document.getElementById('createClientInitialRate').value) || 10;
  const notes = document.getElementById('createClientNotes').value.trim();

  try {
    const res = await fetch('/api/admin/create-client', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        password: password || '1234',
        phone,
        startDate,
        initialAmount,
        initialRate,
        notes
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to onboard client');

    closeCreateClientModal();
    showToast(`Client ${name} created with initial ledger entry!`, 'success');
    loadAdminDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Delete Client
async function deleteCurrentClient() {
  if (!state.selectedClient) return;
  if (!confirm(`Are you sure you want to completely delete client ${state.selectedClient.name}? This will remove all their ledgers and investments.`)) return;

  try {
    const res = await fetch(`/api/admin/clients/${state.selectedClient.id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Delete client failed');

    closeClientDrawer();
    showToast('Client deleted', 'info');
    loadAdminDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// =========================================================================
// ADMIN MONTHLY COMPOUND LEDGER MANAGER
// =========================================================================

function populateLedgerClientSelect(clients) {
  const sel = document.getElementById('adminLedgerClientSelect');
  if (!sel) return;

  sel.innerHTML = clients.map(c => `
    <option value="${c.email}">${c.name} (${c.email})</option>
  `).join('');

  if (clients.length > 0) {
    inspectClientLedger(clients[0].email);
  }
}

function handleLedgerClientChange() {
  const sel = document.getElementById('adminLedgerClientSelect');
  if (sel && sel.value) {
    inspectClientLedger(sel.value);
  }
}

async function inspectClientLedger(email) {
  state.activeLedgerClient = email;
  switchAdminTab('ledger');

  const sel = document.getElementById('adminLedgerClientSelect');
  if (sel) sel.value = email;

  try {
    const res = await fetch(`/api/ledger?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch ledger');

    renderAdminLedgerTable(data.entries || [], data.summary || {});
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderAdminLedgerTable(entries, summary) {
  const tbody = document.getElementById('adminLedgerTbody');
  if (!tbody) return;

  // Summary labels
  const dBal = document.getElementById('admSummaryBalance');
  const dInv = document.getElementById('admSummaryInvested');
  const dProfit = document.getElementById('admSummaryInterest');
  const dRate = document.getElementById('admSummaryRate');

  if (dBal) dBal.textContent = `₹${(summary.currentBalance || 0).toLocaleString()}`;
  if (dInv) dInv.textContent = `₹${(summary.totalInvested || 0).toLocaleString()}`;
  if (dProfit) dProfit.textContent = `₹${(summary.totalInterest || 0).toLocaleString()}`;
  if (dRate) dRate.textContent = summary.latestRate || '10%';

  if (entries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="adm-empty">No ledger entries yet for this client. Use the form below to add one!</td></tr>`;
    return;
  }

  tbody.innerHTML = entries.map(row => `
    <tr>
      <td class="col-date">${row.entryDate}</td>
      <td class="col-amount">₹${(row.investmentAdded || 0).toLocaleString()}</td>
      <td class="col-prev">₹${(row.previousBalance || 0).toLocaleString()}</td>
      <td class="col-rate"><span class="badge-rate r10">${row.rate || 10}%</span></td>
      <td class="col-interest">+₹${(row.interest || 0).toLocaleString()}</td>
      <td class="col-total">₹${(row.totalBalance || 0).toLocaleString()}</td>
      <td class="col-actions">
        <button class="btn-ledger-edit" onclick="editLedgerEntryPrompt('${row._id}', '${row.entryDate}', ${row.investmentAdded}, ${row.rate}, '${row.note || ''}')">✏️ Edit</button>
        <button class="btn-ledger-delete" onclick="deleteLedgerEntry('${row._id}')">🗑️</button>
      </td>
    </tr>
  `).join('');
}

// Add Entry
async function handleAdminAddLedgerEntry(e) {
  e.preventDefault();
  if (!state.activeLedgerClient) {
    showToast('Select a client first', 'error');
    return;
  }

  const entryDate = document.getElementById('ledgerAddDate').value;
  const investmentAdded = parseFloat(document.getElementById('ledgerAddAmount').value) || 0;
  const rate = parseFloat(document.getElementById('ledgerAddRate').value) || 10;
  const note = document.getElementById('ledgerAddNote').value.trim();

  try {
    const res = await fetch('/api/ledger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userEmail: state.activeLedgerClient,
        entryDate,
        investmentAdded,
        rate,
        note
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Add ledger entry failed');

    showToast('Ledger entry added & cascade recalculated!', 'success');
    e.target.reset();
    inspectClientLedger(state.activeLedgerClient);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Edit Entry
async function editLedgerEntryPrompt(id, oldDate, oldAmt, oldRate, oldNote) {
  const newDate = prompt('Update Entry Date (DD-MM-YYYY or YYYY-MM-DD):', oldDate);
  if (newDate === null) return;
  const newAmt = prompt('Update Added Investment Amount (₹):', oldAmt);
  if (newAmt === null) return;
  const newRate = prompt('Update Monthly Rate %:', oldRate);
  if (newRate === null) return;
  const newNote = prompt('Update Note:', oldNote);

  try {
    const res = await fetch(`/api/ledger/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userEmail: state.activeLedgerClient,
        entryDate: newDate,
        investmentAdded: parseFloat(newAmt) || 0,
        rate: parseFloat(newRate) || 10,
        note: newNote
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Edit entry failed');

    showToast('Entry updated & compounding balances recalculated!', 'success');
    inspectClientLedger(state.activeLedgerClient);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Delete Entry
async function deleteLedgerEntry(id) {
  if (!confirm('Are you sure you want to delete this ledger entry? All subsequent rows will be automatically recalculated.')) return;

  try {
    const res = await fetch(`/api/ledger/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Delete entry failed');

    showToast('Entry deleted & ledger cascade recalculated!', 'info');
    inspectClientLedger(state.activeLedgerClient);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// =========================================================================
// INVESTMENTS TAB & RATE UPDATION / ROLLOVER
// =========================================================================

async function loadAllInvestmentsTab() {
  const tbody = document.getElementById('adminInvestmentsTbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/investments');
    const invs = await res.json();
    if (!res.ok) throw new Error(invs.detail || 'Failed to fetch investments');

    if (invs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="adm-empty">No investment contracts yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = invs.map(inv => `
      <tr>
        <td><b>${inv.userName}</b><br><small>${inv.userEmail}</small></td>
        <td>₹${(inv.amount || 0).toLocaleString()}</td>
        <td>${inv.tenure || '4 Month'}</td>
        <td><span class="badge-rate r10">${inv.rateLabel || inv.ratePercent + '%'}</span></td>
        <td>₹${(inv.monthlyProfit || 0).toLocaleString()}</td>
        <td><span class="pill ${inv.status === 'Running' ? '' : 'off'}">${inv.status}</span></td>
        <td>
          <button class="btn-ledger-edit" onclick="openRolloverModal('${inv._id}', ${inv.amount}, ${inv.ratePercent || 5})">📈 Update Rate</button>
          <button class="btn-ledger-delete" onclick="toggleInvestmentStatus('${inv._id}')">Status</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

let activeRolloverInvId = null;

function openRolloverModal(invId, amount, currentRate) {
  activeRolloverInvId = invId;
  const overlay = document.getElementById('rolloverModalOverlay');
  if (!overlay) return;

  document.getElementById('rolloverCurrentPrincipal').textContent = `₹${(amount || 0).toLocaleString()}`;
  document.getElementById('rolloverNewRate').value = currentRate || 5;

  overlay.classList.add('open');
}

function closeRolloverModal() {
  const overlay = document.getElementById('rolloverModalOverlay');
  if (overlay) overlay.classList.remove('open');
}

async function handleRolloverSubmit(e) {
  e.preventDefault();
  if (!activeRolloverInvId) return;

  const newRate = parseFloat(document.getElementById('rolloverNewRate').value) || 5;
  const addMonths = parseInt(document.getElementById('rolloverExtensionMonths').value, 10) || 4;
  const rolloverProfit = document.getElementById('rolloverProfitCheck').checked;
  const note = document.getElementById('rolloverNote').value.trim();

  try {
    const res = await fetch(`/api/investments/${activeRolloverInvId}/rate-or-extend`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        newRatePercent: newRate,
        additionalMonths: addMonths,
        rolloverProfit: rolloverProfit,
        note: note
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Rate update failed');

    closeRolloverModal();
    showToast('Investment rate and balance updated successfully!', 'success');
    loadAllInvestmentsTab();
    loadAdminDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function toggleInvestmentStatus(id) {
  try {
    const res = await fetch(`/api/investments/${id}/status`, { method: 'PUT' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Status toggle failed');

    showToast(`Status changed to ${data.investment.status}`, 'info');
    loadAllInvestmentsTab();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// =========================================================================
// ADMIN NOTIFICATIONS FEED
// =========================================================================

function toggleNotifDropdown(e) {
  e.stopPropagation();
  const dd = document.getElementById('navNotifDropdown');
  if (dd) dd.classList.toggle('show');
}

document.addEventListener('click', (e) => {
  const dd = document.getElementById('navNotifDropdown');
  if (dd && !dd.contains(e.target) && !e.target.closest('#navNotifBtn')) {
    dd.classList.remove('show');
  }
});

async function fetchNotifications() {
  try {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    if (!res.ok) return;

    const list = data.list || [];
    const unread = data.unreadCount || 0;

    const badge = document.getElementById('navNotifBadge');
    if (badge) {
      if (unread > 0) {
        badge.textContent = unread;
        badge.style.display = 'block';
      } else {
        badge.style.display = 'none';
      }
    }

    const container = document.getElementById('navNotifList');
    if (container) {
      if (list.length === 0) {
        container.innerHTML = `<div class="notif-empty">No notifications yet</div>`;
      } else {
        container.innerHTML = list.map(n => `
          <div class="notif-item ${n.isRead ? '' : 'unread'}" onclick="markNotifRead('${n._id}')">
            <div class="notif-icon">${n.type === 'USER_SIGNUP' ? '👤' : n.type === 'PAYMENT_RECEIVED' ? '💳' : '🔔'}</div>
            <div class="notif-content">
              <div class="notif-title">${n.title}</div>
              <div class="notif-msg">${n.message}</div>
              <div class="notif-time">${new Date(n.createdAt).toLocaleTimeString()}</div>
            </div>
          </div>
        `).join('');
      }
    }

  } catch (e) {
    console.warn('Notifications fetch note:', e);
  }
}

async function markNotifRead(id) {
  try {
    await fetch(`/api/notifications/${id}/read`, { method: 'PUT' });
    fetchNotifications();
  } catch (e) {}
}

async function markAllNotifsRead(e) {
  if (e) e.stopPropagation();
  try {
    await fetch('/api/notifications/read-all', { method: 'PUT' });
    fetchNotifications();
    showToast('All notifications marked as read', 'info');
  } catch (e) {}
}

async function clearAllNotifs(e) {
  if (e) e.stopPropagation();
  try {
    await fetch('/api/notifications', { method: 'DELETE' });
    fetchNotifications();
    showToast('Notifications feed cleared', 'info');
  } catch (e) {}
}
