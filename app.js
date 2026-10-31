// Determine API Base URL
const API_BASE = window.location.origin.includes('5173') || window.location.origin.includes('3000') 
  ? 'http://127.0.0.1:8000/api' 
  : `${window.location.origin}/api`;

// State
let allLocations = [];
let allItems = [];
let allClaims = [];
let currentTab = 'items';
let currentStatusFilter = '';
let currentSelectedItem = null;
let debounceTimer = null;

// Icons mapping for categories
const CATEGORY_ICONS = {
  "Electronics": "laptop",
  "Bags & Wallets": "briefcase",
  "Keys": "key",
  "Books & Stationery": "book-open",
  "Bottles & Containers": "cup-soda",
  "Clothing": "shirt",
  "Jewelry & Accessories": "watch",
  "Other": "help-circle"
};

// Default fallback images
const CATEGORY_IMAGES = {
  "Electronics": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60",
  "Bags & Wallets": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=500&auto=format&fit=crop&q=60",
  "Keys": "https://images.unsplash.com/photo-1582139329536-e7284fece509?w=500&auto=format&fit=crop&q=60",
  "Books & Stationery": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=60",
  "Bottles & Containers": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop&q=60",
  "Clothing": "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=500&auto=format&fit=crop&q=60",
  "Jewelry & Accessories": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&auto=format&fit=crop&q=60",
  "Other": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop&q=60"
};

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  // Set default report date to today
  const todayStr = new Date().toISOString().split('T')[0];
  document.getElementById('reportDate').value = todayStr;

  await checkApiHealth();
  await loadLocations();
  await fetchItems();
  await fetchAllMatches();
  await fetchClaims();
  await fetchStats();
  
  lucide.createIcons();
});

// Check API Health
async function checkApiHealth() {
  const pill = document.getElementById('backendStatusPill');
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      pill.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Connected: API Online`;
      pill.className = "px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-700/50 flex items-center gap-1";
    } else {
      throw new Error();
    }
  } catch (err) {
    pill.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping"></span> Connecting to API...`;
    pill.className = "px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-950 text-rose-300 border border-rose-700/50 flex items-center gap-1";
  }
}

// Load Campus Locations
async function loadLocations() {
  try {
    const res = await fetch(`${API_BASE}/locations`);
    allLocations = await res.json();
    
    const filterSelect = document.getElementById('filterLocation');
    const reportSelect = document.getElementById('reportLocation');

    // Populate filter select
    filterSelect.innerHTML = `<option value="">All Campus Locations</option>` + 
      allLocations.map(loc => `<option value="${loc.id}">${loc.name} (${loc.building})</option>`).join('');

    // Populate report select
    reportSelect.innerHTML = `<option value="">Select Location</option>` + 
      allLocations.map(loc => `<option value="${loc.name}">${loc.name} - ${loc.building} (${loc.zone || ''})</option>`).join('');
  } catch (err) {
    console.error("Error loading locations:", err);
  }
}

// Switch Active Tab
function switchTab(tab) {
  currentTab = tab;

  // View elements
  const views = {
    'items': document.getElementById('viewItems'),
    'matches': document.getElementById('viewMatches'),
    'claims': document.getElementById('viewClaims'),
    'stats': document.getElementById('viewStats')
  };

  // Nav buttons
  const navBtns = {
    'items': document.getElementById('navTabItems'),
    'matches': document.getElementById('navTabMatches'),
    'claims': document.getElementById('navTabClaims'),
    'stats': document.getElementById('navTabStats')
  };

  // Toggle views
  Object.keys(views).forEach(key => {
    if (key === tab) {
      views[key].classList.remove('hidden');
    } else {
      views[key].classList.add('hidden');
    }
  });

  // Toggle active button style
  Object.keys(navBtns).forEach(key => {
    if (navBtns[key]) {
      if (key === tab) {
        navBtns[key].className = "nav-tab px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 bg-white text-indigo-600 shadow-sm";
      } else {
        navBtns[key].className = "nav-tab px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900";
      }
    }
  });

  // Trigger data reload for specific tabs
  if (tab === 'matches') fetchAllMatches();
  if (tab === 'claims') fetchClaims();
  if (tab === 'stats') fetchStats();

  lucide.createIcons();
}

// Fetch Items with Filters
async function fetchItems() {
  const type = document.getElementById('filterType').value;
  const category = document.getElementById('filterCategory').value;
  const locationId = document.getElementById('filterLocation').value;
  const search = document.getElementById('filterSearch').value.trim();

  let url = `${API_BASE}/items?`;
  if (type) url += `type=${encodeURIComponent(type)}&`;
  if (category) url += `category=${encodeURIComponent(category)}&`;
  if (locationId) url += `location_id=${encodeURIComponent(locationId)}&`;
  if (currentStatusFilter) url += `status=${encodeURIComponent(currentStatusFilter)}&`;
  if (search) url += `search=${encodeURIComponent(search)}&`;

  try {
    const res = await fetch(url);
    allItems = await res.json();
    renderItems(allItems);
  } catch (err) {
    console.error("Error fetching items:", err);
    showToast("Failed to load items from server", "error");
  }
}

function debouncedFetchItems() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchItems();
  }, 250);
}

function setStatusFilter(statusVal) {
  currentStatusFilter = statusVal;
  document.querySelectorAll('.status-btn').forEach(btn => {
    if (btn.getAttribute('data-status') === statusVal) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  fetchItems();
}

function resetFilters() {
  document.getElementById('filterType').value = "";
  document.getElementById('filterCategory').value = "";
  document.getElementById('filterLocation').value = "";
  document.getElementById('filterSearch').value = "";
  setStatusFilter("");
  fetchItems();
}

// Render Item Cards
function renderItems(items) {
  const grid = document.getElementById('itemsGrid');
  const empty = document.getElementById('itemsEmptyState');
  const countText = document.getElementById('itemsCountText');

  countText.innerText = `Showing ${items.length} item${items.length === 1 ? '' : 's'}`;

  if (!items || items.length === 0) {
    grid.innerHTML = "";
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');

  grid.innerHTML = items.map(item => {
    const isLost = item.type === 'lost';
    const typeBadge = isLost 
      ? `<span class="px-2 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wide bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Lost</span>`
      : `<span class="px-2 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wide bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Found</span>`;

    let statusBadge = '';
    if (item.status === 'open') {
      statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">Open</span>`;
    } else if (item.status === 'claim_pending') {
      statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-amber-500 animate-ping"></span> Claim Pending</span>`;
    } else if (item.status === 'claimed') {
      statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">Claimed</span>`;
    } else if (item.status === 'returned') {
      statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300">Returned</span>`;
    } else {
      statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">${item.status}</span>`;
    }

    const imgUrl = item.image_url || CATEGORY_IMAGES[item.category] || CATEGORY_IMAGES["Other"];
    const catIcon = CATEGORY_ICONS[item.category] || "tag";

    return `
      <div class="item-card bg-white rounded-2xl border border-slate-200/90 overflow-hidden flex flex-col justify-between shadow-sm">
        
        <!-- Top Image with Badges -->
        <div class="relative h-44 bg-slate-100 overflow-hidden group cursor-pointer" onclick="openItemDetails(${item.id})">
          <img src="${imgUrl}" alt="${item.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
          <div class="absolute inset-0 bg-gradient-to-t from-slate-900/60 via-transparent to-black/20"></div>
          
          <div class="absolute top-3 left-3 flex items-center gap-1.5">
            ${typeBadge}
            ${statusBadge}
          </div>

          <div class="absolute bottom-2.5 left-3 right-3 flex items-center justify-between text-white text-xs">
            <span class="flex items-center gap-1 drop-shadow-md font-medium">
              <i data-lucide="${catIcon}" class="w-3.5 h-3.5"></i> ${item.category}
            </span>
            <span class="text-[11px] text-white/90 drop-shadow-md">
              ${item.date_occurred}
            </span>
          </div>
        </div>

        <!-- Body Content -->
        <div class="p-4 flex-1 flex flex-col justify-between space-y-3">
          <div>
            <h3 class="font-bold text-slate-900 text-base line-clamp-1 cursor-pointer hover:text-indigo-600" onclick="openItemDetails(${item.id})">
              ${escapeHtml(item.title)}
            </h3>
            
            <p class="text-xs text-slate-500 line-clamp-2 mt-1 leading-relaxed">
              ${escapeHtml(item.description)}
            </p>
          </div>

          <div class="space-y-2 pt-2 border-t border-slate-100 text-xs">
            <div class="flex items-center gap-1.5 text-slate-600 font-medium line-clamp-1">
              <i data-lucide="map-pin" class="w-3.5 h-3.5 text-rose-500 flex-shrink-0"></i>
              <span class="truncate">${escapeHtml(item.location_name)}</span>
            </div>

            ${item.claim_count > 0 ? `
              <div class="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md">
                <i data-lucide="shield" class="w-3 h-3"></i> ${item.claim_count} Claim${item.claim_count > 1 ? 's' : ''} submitted
              </div>
            ` : ''}
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 pt-2">
            <button onclick="openItemDetails(${item.id})" class="flex-1 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 transition-colors flex items-center justify-center gap-1">
              <i data-lucide="eye" class="w-3.5 h-3.5"></i> Details
            </button>
            ${!isLost && item.status !== 'returned' ? `
              <button onclick="openClaimModal(${item.id}, '${escapeQuote(item.title)}')" class="py-2 px-3 rounded-xl text-xs font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition-colors flex items-center justify-center gap-1">
                <i data-lucide="hand" class="w-3.5 h-3.5"></i> Claim
              </button>
            ` : ''}
          </div>

        </div>

      </div>
    `;
  }).join('');

  lucide.createIcons();
}

// Open Item Details Modal
async function openItemDetails(itemId) {
  try {
    const res = await fetch(`${API_BASE}/items/${itemId}`);
    if (!res.ok) throw new Error();
    const item = await res.json();
    currentSelectedItem = item;

    const isLost = item.type === 'lost';
    const typeBadge = document.getElementById('detailTypeBadge');
    const statusBadge = document.getElementById('detailStatusBadge');

    if (isLost) {
      typeBadge.innerText = "LOST ITEM";
      typeBadge.className = "px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500 text-white";
    } else {
      typeBadge.innerText = "FOUND ITEM";
      typeBadge.className = "px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500 text-white";
    }

    statusBadge.innerText = item.status.replace('_', ' ').toUpperCase();
    statusBadge.className = "px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-700 text-slate-200";

    document.getElementById('detailTitle').innerText = item.title;
    document.getElementById('detailCategory').innerText = item.category;
    document.getElementById('detailLocation').innerText = item.location_name;
    document.getElementById('detailDate').innerText = `${isLost ? 'Lost on' : 'Found on'}: ${item.date_occurred}`;
    document.getElementById('detailReporter').innerText = item.reporter_name;
    document.getElementById('detailContact').innerText = `${item.reporter_email} ${item.reporter_phone ? `(${item.reporter_phone})` : ''}`;
    document.getElementById('detailReportedDate').innerText = item.date_reported;
    document.getElementById('detailDescription').innerText = item.description;

    const imgEl = document.getElementById('detailImage');
    imgEl.src = item.image_url || CATEGORY_IMAGES[item.category] || CATEGORY_IMAGES["Other"];

    // Secret details
    const secretBox = document.getElementById('detailSecretBox');
    const secretText = document.getElementById('detailSecretText');
    if (item.secret_details) {
      secretBox.classList.remove('hidden');
      secretText.innerText = item.secret_details;
    } else {
      secretBox.classList.add('hidden');
    }

    // Status select
    document.getElementById('detailStatusSelect').value = item.status;

    // Claim button visibility
    const claimBtn = document.getElementById('btnClaimItem');
    if (!isLost && item.status !== 'returned' && item.status !== 'closed') {
      claimBtn.classList.remove('hidden');
    } else {
      claimBtn.classList.add('hidden');
    }

    // Render Matched suggestions
    renderDetailMatches(item.matches || [], isLost);

    // Show modal
    const modal = document.getElementById('modalItemDetails');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    lucide.createIcons();
  } catch (err) {
    console.error("Error opening details:", err);
    showToast("Failed to load item details", "error");
  }
}

function closeItemDetailsModal() {
  const modal = document.getElementById('modalItemDetails');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  currentSelectedItem = null;
}

// Render Matches inside Item Details
function renderDetailMatches(matches, isTargetLost) {
  const listEl = document.getElementById('detailMatchesList');
  const countEl = document.getElementById('detailMatchesCount');
  countEl.innerText = matches.length;

  if (!matches || matches.length === 0) {
    listEl.innerHTML = `
      <div class="text-xs text-slate-400 italic bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
        No candidate matches found in current opposite records yet.
      </div>
    `;
    return;
  }

  listEl.innerHTML = matches.map(m => {
    const cand = m.item;
    let badgeClass = 'badge-match-low';
    if (m.score >= 70) badgeClass = 'badge-match-high';
    else if (m.score >= 45) badgeClass = 'badge-match-med';

    return `
      <div class="p-3.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100/80 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="${badgeClass} px-2 py-0.5 rounded-full text-[11px] font-extrabold">
              ${m.score}% MATCH (${m.confidence})
            </span>
            <span class="text-xs font-bold text-slate-900">${escapeHtml(cand.title)}</span>
          </div>
          <div class="text-[11px] text-slate-500 flex flex-wrap gap-2">
            <span>📍 ${escapeHtml(cand.location_name)}</span>
            <span>📅 ${cand.date_occurred}</span>
            <span>🏷️ ${cand.category}</span>
          </div>
          <div class="flex flex-wrap gap-1 pt-1">
            ${(m.reasons || []).map(r => `<span class="bg-indigo-50 text-indigo-700 text-[10px] font-medium px-2 py-0.5 rounded-md border border-indigo-100">${escapeHtml(r)}</span>`).join('')}
          </div>
        </div>

        <button onclick="closeItemDetailsModal(); setTimeout(() => openItemDetails(${cand.id}), 100)" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-white hover:bg-indigo-50 border border-slate-200 text-indigo-600 shadow-sm flex items-center gap-1 flex-shrink-0">
          <i data-lucide="arrow-right" class="w-3 h-3"></i> View Match
        </button>
      </div>
    `;
  }).join('');
}

// Update Item Status from Details Modal
async function updateCurrentItemStatus() {
  if (!currentSelectedItem) return;
  const newStatus = document.getElementById('detailStatusSelect').value;

  try {
    const res = await fetch(`${API_BASE}/items/${currentSelectedItem.id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus, notes: "Updated via admin details panel" })
    });
    if (!res.ok) throw new Error();
    showToast(`Status updated to ${newStatus}`, "success");
    await fetchItems();
    await fetchStats();
  } catch (err) {
    showToast("Failed to update status", "error");
  }
}

// ==========================================
// REPORT ITEM MODAL LOGIC
// ==========================================

function openReportModal(defaultType = 'lost') {
  const form = document.getElementById('formReportItem');
  form.reset();

  const radio = form.querySelector(`input[name="itemType"][value="${defaultType}"]`);
  if (radio) radio.checked = true;

  updateReportFormLabels();
  document.getElementById('reportDate').value = new Date().toISOString().split('T')[0];
  document.getElementById('reportInstantMatchBox').classList.add('hidden');

  const modal = document.getElementById('modalReport');
  modal.classList.remove('hidden');
  modal.classList.add('flex');

  lucide.createIcons();
}

function closeReportModal() {
  const modal = document.getElementById('modalReport');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

function updateReportFormLabels() {
  const form = document.getElementById('formReportItem');
  const type = form.querySelector('input[name="itemType"]:checked').value;
  const dateLbl = document.getElementById('lblDateOccurred');
  dateLbl.innerText = type === 'lost' ? 'Date Lost *' : 'Date Found *';
  checkInstantMatchPreview();
}

// Live Match Preview as User types in Report Modal
async function checkInstantMatchPreview() {
  const form = document.getElementById('formReportItem');
  const type = form.querySelector('input[name="itemType"]:checked').value;
  const title = document.getElementById('reportTitle').value.trim();
  const description = document.getElementById('reportDescription').value.trim();
  const category = document.getElementById('reportCategory').value;
  const location = document.getElementById('reportLocation').value;

  const box = document.getElementById('reportInstantMatchBox');
  const list = document.getElementById('instantMatchList');
  const countBadge = document.getElementById('instantMatchCount');

  if (title.length < 3 && description.length < 5) {
    box.classList.add('hidden');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/match-custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: type,
        title: title || "Item",
        description: description || title,
        category: category || "Other",
        location_name: location || "",
        date_occurred: document.getElementById('reportDate').value
      })
    });
    const data = await res.json();
    const highMatches = (data.matches || []).filter(m => m.score >= 35);

    if (highMatches.length > 0) {
      box.classList.remove('hidden');
      countBadge.innerText = `${highMatches.length} candidate${highMatches.length > 1 ? 's' : ''}`;
      list.innerHTML = highMatches.slice(0, 2).map(m => `
        <div class="flex items-center justify-between p-2 rounded-lg bg-white/80 border border-indigo-100">
          <div>
            <span class="font-bold text-slate-800">${escapeHtml(m.item.title)}</span>
            <span class="text-[10px] text-slate-500 ml-1">(${m.item.location_name})</span>
          </div>
          <span class="font-extrabold text-[10px] px-1.5 py-0.5 rounded ${m.score >= 70 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
            ${m.score}% MATCH
          </span>
        </div>
      `).join('');
    } else {
      box.classList.add('hidden');
    }
  } catch (err) {
    // Non-blocking
  }
}

// Submit Report Item Form
async function submitReportItem(e) {
  e.preventDefault();
  const form = document.getElementById('formReportItem');
  const type = form.querySelector('input[name="itemType"]:checked').value;
  const title = document.getElementById('reportTitle').value.trim();
  const category = document.getElementById('reportCategory').value;
  const locationName = document.getElementById('reportLocation').value;
  const dateOccurred = document.getElementById('reportDate').value;
  const description = document.getElementById('reportDescription').value.trim();
  const secret = document.getElementById('reportSecret').value.trim();
  const imageUrl = document.getElementById('reportImageUrl').value.trim();
  const name = document.getElementById('reportName').value.trim();
  const email = document.getElementById('reportEmail').value.trim();
  const phone = document.getElementById('reportPhone').value.trim();

  // Find location ID
  const locObj = allLocations.find(l => l.name === locationName);
  const locationId = locObj ? locObj.id : null;

  const btn = document.getElementById('btnSubmitReport');
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Submitting...`;

  try {
    const res = await fetch(`${API_BASE}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type,
        title,
        description,
        category,
        location_id: locationId,
        location_name: locationName,
        date_occurred: dateOccurred,
        reporter_name: name,
        reporter_email: email,
        reporter_phone: phone,
        secret_details: secret,
        image_url: imageUrl
      })
    });

    if (!res.ok) throw new Error();
    const data = await res.json();

    closeReportModal();
    showToast(`${type.toUpperCase()} item recorded successfully!`, "success");

    await fetchItems();
    await fetchAllMatches();
    await fetchStats();

    // If immediate matches exist, notify user and open details
    if (data.matches && data.matches.length > 0) {
      showToast(`⚡ AI Engine detected ${data.matches.length} instant potential match!`, "info");
      openItemDetails(data.item.id);
    }

  } catch (err) {
    console.error("Error creating item:", err);
    showToast("Failed to create report. Please check required fields.", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="check" class="w-4 h-4"></i> Submit Report`;
    lucide.createIcons();
  }
}

// ==========================================
// CLAIMS LOGIC & VERIFICATION
// ==========================================

function openClaimModal(itemId, itemTitle) {
  document.getElementById('claimItemId').value = itemId;
  document.getElementById('claimItemTitleDisplay').innerText = itemTitle;
  document.getElementById('formSubmitClaim').reset();

  const modal = document.getElementById('modalClaim');
  modal.classList.remove('hidden');
  modal.classList.add('flex');

  lucide.createIcons();
}

function openClaimModalFromDetails() {
  if (!currentSelectedItem) return;
  const id = currentSelectedItem.id;
  const title = currentSelectedItem.title;
  closeItemDetailsModal();
  openClaimModal(id, title);
}

function closeClaimModal() {
  const modal = document.getElementById('modalClaim');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

async function submitClaimForm(e) {
  e.preventDefault();
  const itemId = parseInt(document.getElementById('claimItemId').value);
  const name = document.getElementById('claimName').value.trim();
  const studentId = document.getElementById('claimStudentId').value.trim();
  const email = document.getElementById('claimEmail').value.trim();
  const phone = document.getElementById('claimPhone').value.trim();
  const proof = document.getElementById('claimProof').value.trim();
  const proofImg = document.getElementById('claimProofImage').value.trim();

  try {
    const res = await fetch(`${API_BASE}/claims`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: itemId,
        claimant_name: name,
        claimant_student_id: studentId,
        claimant_email: email,
        claimant_phone: phone,
        proof_description: proof,
        proof_image_url: proofImg
      })
    });

    if (!res.ok) throw new Error();
    const data = await res.json();

    closeClaimModal();
    showToast("Claim filed! A campus staff administrator will verify your ownership proof.", "success");
    await fetchClaims();
    await fetchItems();
    await fetchStats();
  } catch (err) {
    showToast("Failed to file claim", "error");
  }
}

async function fetchClaims() {
  const statusFilter = document.getElementById('claimsFilterStatus').value;
  let url = `${API_BASE}/claims?`;
  if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}`;

  try {
    const res = await fetch(url);
    allClaims = await res.json();
    renderClaims(allClaims);

    // Update pending count badge
    const pendingCount = allClaims.filter(c => c.verification_status === 'pending').length;
    const badge = document.getElementById('pendingClaimsCountBadge');
    if (pendingCount > 0) {
      badge.innerText = pendingCount;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  } catch (err) {
    console.error("Error fetching claims:", err);
  }
}

function renderClaims(claims) {
  const list = document.getElementById('claimsList');

  if (!claims || claims.length === 0) {
    list.innerHTML = `
      <div class="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-300">
        <i data-lucide="shield-check" class="w-10 h-10 text-slate-300 mx-auto mb-2"></i>
        <h4 class="text-base font-bold text-slate-700">No ownership claims found</h4>
        <p class="text-xs text-slate-400 mt-1">Claims submitted by students for found items appear here for verification.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  list.innerHTML = claims.map(c => {
    let statusClass = 'bg-amber-100 text-amber-800 border-amber-200';
    if (c.verification_status === 'approved') statusClass = 'bg-emerald-100 text-emerald-800 border-emerald-200';
    if (c.verification_status === 'rejected') statusClass = 'bg-rose-100 text-rose-800 border-rose-200';

    return `
      <div class="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm space-y-4">
        
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-400 uppercase">Claim #${c.id}</span>
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase border ${statusClass}">
                ${c.verification_status}
              </span>
            </div>
            <h3 class="text-base font-extrabold text-slate-900 mt-1">
              For Found Item: "${escapeHtml(c.item_title)}"
            </h3>
            <div class="text-xs text-slate-500 mt-0.5 flex flex-wrap gap-2">
              <span>📍 ${escapeHtml(c.item_location)}</span>
              <span>🏷️ ${c.item_category}</span>
              <span>🕒 Filed: ${c.created_at}</span>
            </div>
          </div>

          <div class="text-right sm:text-right">
            <div class="font-bold text-sm text-slate-800">${escapeHtml(c.claimant_name)}</div>
            <div class="text-xs text-slate-500">ID: <span class="font-mono font-semibold text-slate-700">${escapeHtml(c.claimant_student_id)}</span></div>
            <div class="text-xs text-slate-500">${escapeHtml(c.claimant_email)} ${c.claimant_phone ? `&bull; ${escapeHtml(c.claimant_phone)}` : ''}</div>
          </div>
        </div>

        <!-- Proof Description & Verification Box -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80 space-y-1">
            <div class="font-bold text-slate-700 flex items-center gap-1.5">
              <i data-lucide="file-text" class="w-3.5 h-3.5 text-indigo-500"></i> Claimant's Proof of Ownership:
            </div>
            <p class="text-slate-600 leading-relaxed">${escapeHtml(c.proof_description)}</p>
            ${c.proof_image_url ? `
              <div class="pt-2">
                <a href="${c.proof_image_url}" target="_blank" class="text-indigo-600 font-bold underline flex items-center gap-1">
                  <i data-lucide="image" class="w-3 h-3"></i> View Submitted Proof Photo / Receipt
                </a>
              </div>
            ` : ''}
          </div>

          <div class="bg-amber-50/70 p-3.5 rounded-xl border border-amber-200/70 space-y-1">
            <div class="font-bold text-amber-900 flex items-center gap-1.5">
              <i data-lucide="shield-alert" class="w-3.5 h-3.5 text-amber-600"></i> Admin Verification &amp; Notes:
            </div>
            <p class="text-amber-800">${c.admin_notes ? escapeHtml(c.admin_notes) : 'No admin notes recorded yet.'}</p>
          </div>
        </div>

        <!-- Verification Actions (If pending) -->
        ${c.verification_status === 'pending' ? `
          <div class="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <span class="text-xs font-semibold text-slate-500 mr-2">Admin Action:</span>
            <button onclick="verifyClaim(${c.id}, 'approved')" class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm flex items-center gap-1">
              <i data-lucide="check" class="w-3.5 h-3.5"></i> Approve &amp; Mark Returned
            </button>
            <button onclick="verifyClaim(${c.id}, 'more_info_needed')" class="px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-sm flex items-center gap-1">
              <i data-lucide="help-circle" class="w-3.5 h-3.5"></i> Request More Proof
            </button>
            <button onclick="verifyClaim(${c.id}, 'rejected')" class="px-3.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs flex items-center gap-1">
              <i data-lucide="x" class="w-3.5 h-3.5"></i> Reject Claim
            </button>
          </div>
        ` : `
          <div class="text-right text-[11px] text-slate-400">
            Verification status finalized on ${c.updated_at}
          </div>
        `}

      </div>
    `;
  }).join('');

  lucide.createIcons();
}

async function verifyClaim(claimId, status) {
  let notes = prompt(`Enter admin notes / reason for marking this claim '${status}':`, status === 'approved' ? "Proof of ownership and student identity verified." : "");
  if (notes === null) return; // User cancelled

  try {
    const res = await fetch(`${API_BASE}/claims/${claimId}/verify`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        verification_status: status,
        admin_notes: notes,
        resolve_item: true
      })
    });

    if (!res.ok) throw new Error();
    showToast(`Claim #${claimId} marked as ${status.toUpperCase()}`, "success");
    await fetchClaims();
    await fetchItems();
    await fetchStats();
  } catch (err) {
    showToast("Error updating claim verification", "error");
  }
}

// ==========================================
// AI MATCH CENTER LOGIC
// ==========================================

async function fetchAllMatches() {
  try {
    const res = await fetch(`${API_BASE}/matches?min_score=30`);
    const data = await res.json();
    renderAllMatches(data.matches || []);

    const badge = document.getElementById('matchCounterBadge');
    badge.innerText = data.matches_count || 0;
  } catch (err) {
    console.error("Error fetching matches:", err);
  }
}

function renderAllMatches(matches) {
  const container = document.getElementById('allMatchesContainer');

  if (!matches || matches.length === 0) {
    container.innerHTML = `
      <div class="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-300">
        <i data-lucide="sparkles" class="w-12 h-12 text-amber-300 mx-auto mb-2"></i>
        <h4 class="text-base font-bold text-slate-700">No cross-item matches currently detected</h4>
        <p class="text-xs text-slate-400 mt-1">As more lost and found items are reported, the Python matching algorithm will compute correlations here.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = matches.map((m, idx) => {
    const lost = m.lost_item;
    const found = m.found_item;

    let scoreColor = 'from-emerald-600 to-teal-700';
    let badgeText = 'HIGH CONFIDENCE MATCH';
    if (m.score < 70 && m.score >= 45) {
      scoreColor = 'from-amber-500 to-amber-600';
      badgeText = 'POSSIBLE MATCH';
    } else if (m.score < 45) {
      scoreColor = 'from-slate-500 to-slate-600';
      badgeText = 'LOW CONFIDENCE MATCH';
    }

    const bd = m.breakdown || {};

    return `
      <div class="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden space-y-4 p-5 sm:p-6 transition-all hover:border-indigo-300">
        
        <!-- Header Match Score Bar -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div class="flex items-center gap-3">
            <div class="px-3.5 py-1.5 rounded-xl bg-gradient-to-r ${scoreColor} text-white font-extrabold text-sm shadow-md flex items-center gap-1.5">
              <i data-lucide="sparkles" class="w-4 h-4"></i> ${m.score}% MATCH
            </div>
            <span class="text-xs font-bold text-slate-500 tracking-wider">${badgeText}</span>
          </div>

          <div class="flex items-center gap-2">
            <button onclick="openClaimModal(${found.id}, '${escapeQuote(found.title)}')" class="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-bold transition-all flex items-center gap-1">
              <i data-lucide="hand" class="w-3.5 h-3.5"></i> File Claim for Found Item
            </button>
            <button onclick="openItemDetails(${found.id})" class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-all">
              Inspect Found
            </button>
          </div>
        </div>

        <!-- Side-by-Side Comparison -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          <!-- Left: Lost Item -->
          <div class="p-4 rounded-2xl bg-rose-50/40 border border-rose-100 space-y-2">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider bg-rose-500 text-white">LOST REPORT</span>
              <span class="text-xs font-semibold text-slate-400">ID #${lost.id}</span>
            </div>
            <h4 class="font-extrabold text-slate-900 text-base">${escapeHtml(lost.title)}</h4>
            <p class="text-xs text-slate-600 line-clamp-2">${escapeHtml(lost.description)}</p>
            <div class="pt-2 text-xs text-slate-500 space-y-1">
              <div>📍 <strong>Location:</strong> ${escapeHtml(lost.location_name)}</div>
              <div>📅 <strong>Date Lost:</strong> ${lost.date_occurred}</div>
              <div>👤 <strong>Reporter:</strong> ${escapeHtml(lost.reporter_name)}</div>
            </div>
          </div>

          <!-- Right: Found Item -->
          <div class="p-4 rounded-2xl bg-emerald-50/40 border border-emerald-100 space-y-2">
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider bg-emerald-600 text-white">FOUND RECORD</span>
              <span class="text-xs font-semibold text-slate-400">ID #${found.id}</span>
            </div>
            <h4 class="font-extrabold text-slate-900 text-base">${escapeHtml(found.title)}</h4>
            <p class="text-xs text-slate-600 line-clamp-2">${escapeHtml(found.description)}</p>
            <div class="pt-2 text-xs text-slate-500 space-y-1">
              <div>📍 <strong>Location:</strong> ${escapeHtml(found.location_name)}</div>
              <div>📅 <strong>Date Found:</strong> ${found.date_occurred}</div>
              <div>👤 <strong>Finder:</strong> ${escapeHtml(found.reporter_name)}</div>
            </div>
          </div>

        </div>

        <!-- Explanation Tags & Breakdown Meters -->
        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
          <div>
            <div class="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">Algorithmic Correlation Factors:</div>
            <div class="flex flex-wrap gap-1.5">
              ${(m.reasons || []).map(r => `
                <span class="inline-flex items-center gap-1 bg-white border border-slate-200 text-slate-800 text-xs font-medium px-2.5 py-1 rounded-lg shadow-2xs">
                  <i data-lucide="check" class="w-3 h-3 text-emerald-600"></i> ${escapeHtml(r)}
                </span>
              `).join('')}
            </div>
          </div>

          <!-- Mini Meters -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-200/60 text-[11px] text-slate-500">
            <div>
              <div class="flex justify-between mb-0.5"><span>Description</span><span>${Math.round((bd.description_score || 0)*100)}%</span></div>
              <div class="h-1.5 rounded-full bg-slate-200 overflow-hidden"><div class="h-full bg-indigo-500" style="width: ${(bd.description_score || 0)*100}%"></div></div>
            </div>
            <div>
              <div class="flex justify-between mb-0.5"><span>Attributes</span><span>${Math.round((bd.attribute_score || 0)*100)}%</span></div>
              <div class="h-1.5 rounded-full bg-slate-200 overflow-hidden"><div class="h-full bg-emerald-500" style="width: ${(bd.attribute_score || 0)*100}%"></div></div>
            </div>
            <div>
              <div class="flex justify-between mb-0.5"><span>Location</span><span>${Math.round((bd.location_score || 0)*100)}%</span></div>
              <div class="h-1.5 rounded-full bg-slate-200 overflow-hidden"><div class="h-full bg-blue-500" style="width: ${(bd.location_score || 0)*100}%"></div></div>
            </div>
            <div>
              <div class="flex justify-between mb-0.5"><span>Timeline</span><span>${Math.round((bd.date_score || 0)*100)}%</span></div>
              <div class="h-1.5 rounded-full bg-slate-200 overflow-hidden"><div class="h-full bg-amber-500" style="width: ${(bd.date_score || 0)*100}%"></div></div>
            </div>
          </div>
        </div>

      </div>
    `;
  }).join('');

  lucide.createIcons();
}

// Custom Matcher Simulator
function openCustomMatcherModal() {
  const modal = document.getElementById('modalCustomMatcher');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  lucide.createIcons();
}

function closeCustomMatcherModal() {
  const modal = document.getElementById('modalCustomMatcher');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

async function runCustomMatchSimulation() {
  const type = document.getElementById('simType').value;
  const category = document.getElementById('simCategory').value;
  const location = document.getElementById('simLocation').value.trim();
  const title = document.getElementById('simTitle').value.trim();
  const description = document.getElementById('simDescription').value.trim();

  const resultsList = document.getElementById('simResultsList');
  resultsList.innerHTML = `<div class="p-3 text-xs text-slate-500">Calculating semantic similarity matrix...</div>`;

  try {
    const res = await fetch(`${API_BASE}/match-custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type,
        category,
        location_name: location,
        title,
        description
      })
    });
    const data = await res.json();
    const matches = data.matches || [];

    if (matches.length === 0) {
      resultsList.innerHTML = `<div class="p-3 text-xs text-slate-400 italic">No items above similarity threshold in current database.</div>`;
      return;
    }

    resultsList.innerHTML = matches.map(m => `
      <div class="p-3 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-xs px-2 py-0.5 rounded ${m.score >= 70 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
              ${m.score}% MATCH
            </span>
            <span class="font-bold text-slate-900 text-xs">${escapeHtml(m.item.title)}</span>
          </div>
          <div class="text-[11px] text-slate-500 mt-1">
            📍 ${escapeHtml(m.item.location_name)} &bull; 🏷️ ${m.item.category}
          </div>
          <div class="text-[10px] text-indigo-600 mt-1 font-medium">
            ${(m.reasons || []).join(' &bull; ')}
          </div>
        </div>

        <button onclick="closeCustomMatcherModal(); openItemDetails(${m.item.id})" class="text-xs px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 font-bold text-slate-700 flex-shrink-0">
          Inspect
        </button>
      </div>
    `).join('');

  } catch (err) {
    resultsList.innerHTML = `<div class="p-3 text-xs text-rose-500">Error connecting to matching service.</div>`;
  }
}

// ==========================================
// CAMPUS STATS & ACTIVITY
// ==========================================

async function fetchStats() {
  try {
    const [statsRes, actRes] = await Promise.all([
      fetch(`${API_BASE}/stats`),
      fetch(`${API_BASE}/activity?limit=12`)
    ]);

    const stats = await statsRes.json();
    const activities = await actRes.json();

    document.getElementById('statTotalItems').innerText = stats.total_items || 0;
    document.getElementById('statTotalLost').innerText = stats.total_lost || 0;
    document.getElementById('statTotalFound').innerText = stats.total_found || 0;
    document.getElementById('statRecoveryRate').innerText = `${stats.recovery_rate || 0}%`;

    // Render Hotspots
    const hotspotsEl = document.getElementById('hotspotsList');
    if (stats.location_hotspots && stats.location_hotspots.length > 0) {
      const maxCount = Math.max(...stats.location_hotspots.map(h => h.count), 1);
      hotspotsEl.innerHTML = stats.location_hotspots.map(h => `
        <div class="space-y-1">
          <div class="flex justify-between text-xs font-semibold text-slate-700">
            <span class="flex items-center gap-1.5"><i data-lucide="map-pin" class="w-3.5 h-3.5 text-rose-500"></i> ${escapeHtml(h.location_name)}</span>
            <span>${h.count} items</span>
          </div>
          <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div class="h-full bg-gradient-to-r from-rose-500 to-amber-500 rounded-full" style="width: ${(h.count / maxCount) * 100}%"></div>
          </div>
        </div>
      `).join('');
    } else {
      hotspotsEl.innerHTML = `<div class="text-xs text-slate-400 italic">No hotspot data available yet.</div>`;
    }

    // Render Categories
    const categoriesEl = document.getElementById('categoriesList');
    if (stats.categories && stats.categories.length > 0) {
      const maxCount = Math.max(...stats.categories.map(c => c.count), 1);
      categoriesEl.innerHTML = stats.categories.map(c => `
        <div class="space-y-1">
          <div class="flex justify-between text-xs font-semibold text-slate-700">
            <span class="flex items-center gap-1.5"><i data-lucide="${CATEGORY_ICONS[c.category] || 'tag'}" class="w-3.5 h-3.5 text-indigo-500"></i> ${c.category}</span>
            <span>${c.count} items</span>
          </div>
          <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div class="h-full bg-indigo-600 rounded-full" style="width: ${(c.count / maxCount) * 100}%"></div>
          </div>
        </div>
      `).join('');
    } else {
      categoriesEl.innerHTML = `<div class="text-xs text-slate-400 italic">No category data available yet.</div>`;
    }

    // Render Activity stream
    const actEl = document.getElementById('activityStream');
    if (activities && activities.length > 0) {
      actEl.innerHTML = activities.map(a => `
        <div class="py-2.5 flex items-start justify-between gap-3 text-xs">
          <div class="space-y-0.5">
            <span class="font-bold text-slate-800">${escapeHtml(a.action.replace(/_/g, ' '))}</span>
            <p class="text-slate-600">${escapeHtml(a.details)}</p>
          </div>
          <span class="text-[10px] text-slate-400 whitespace-nowrap">${a.created_at.split('T')[0]}</span>
        </div>
      `).join('');
    } else {
      actEl.innerHTML = `<div class="py-3 text-xs text-slate-400 italic">No recent campus activity logged.</div>`;
    }

    lucide.createIcons();
  } catch (err) {
    console.error("Error fetching stats:", err);
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');

  let bgClass = 'bg-slate-900 text-white';
  let icon = 'info';
  if (type === 'success') {
    bgClass = 'bg-emerald-800 text-white shadow-emerald-950/20';
    icon = 'check-circle';
  } else if (type === 'error') {
    bgClass = 'bg-rose-800 text-white shadow-rose-950/20';
    icon = 'alert-circle';
  }

  toast.className = `${bgClass} px-4 py-3 rounded-2xl shadow-xl flex items-center gap-2 text-xs font-semibold animate-in slide-in-from-bottom duration-200 pointer-events-auto`;
  toast.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4 flex-shrink-0"></i> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Helpers
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeQuote(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'");
}
