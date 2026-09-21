/**
 * CrimeNet AI — Frontend Application
 * Criminal Network Analysis System
 */

const API = '';
let networkInstance = null;
let allNetworkData = null;
let physicsEnabled = true;
let chartInstances = {};
let lastDashboardData = null;
let currentTheme = localStorage.getItem('crimenet-theme');
if (!currentTheme || currentTheme === 'bright' || currentTheme === 'light') {
    currentTheme = 'cyber';
    localStorage.setItem('crimenet-theme', 'cyber');
}

// ═══ Initialize ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupNavigation();
    setupSearch();
    loadDashboard();
});

// ═══ Theme Management ════════════════════════════════════════
function initTheme() {
    applyTheme(currentTheme);
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            currentTheme = (currentTheme === 'cyber' || currentTheme === 'dark') ? 'light' : 'cyber';
            localStorage.setItem('crimenet-theme', currentTheme);
            applyTheme(currentTheme);
            if (lastDashboardData) {
                renderCharts(lastDashboardData);
            }
            if (networkInstance && allNetworkData) {
                renderNetwork(allNetworkData);
            }
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const icon = document.getElementById('theme-toggle-icon');
    const text = document.getElementById('theme-toggle-text');
    if (icon && text) {
        if (theme === 'cyber' || theme === 'dark') {
            icon.textContent = '☀️';
            text.textContent = 'Light Mode';
        } else {
            icon.textContent = '⚡';
            text.textContent = 'Cyber Forensics';
        }
    }
}

// ═══ Navigation ═══════════════════════════════════════════════
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab-${tab}`)?.classList.add('active');

    // Update title
    const titles = {
        dashboard: ['Dashboard', 'Overview & Analytics'],
        geomap: ['Crime Geo Map', 'Geospatial Crime Analysis & Mapping'],
        network: ['Network Graph', 'Criminal Relationship Visualization'],
        entities: ['Entity Explorer', 'Suspect & Organization Database'],
        dossier: ['Person Dossier (PDF)', 'Criminal Intelligence Dossier & Life Record Generator'],
        communities: ['Communities', 'Detected Criminal Clusters'],
        patterns: ['Patterns & Alerts', 'Suspicious Activity Detection'],
        influencers: ['Key Influencers', 'Network Centrality Analysis'],
        ingest: ['Add Intel & Records', 'Register Criminals & Log Crime Incidents'],
        predict: ['Prediction Console', 'ML-Powered Crime Prediction'],
        nlp: ['NLP Analyzer', 'Text Entity Extraction']
    };
    const [title, breadcrumb] = titles[tab] || [tab, ''];
    document.getElementById('page-title').textContent = title;
    document.getElementById('page-breadcrumb').textContent = breadcrumb;

    // Lazy-load tab data
    switch (tab) {
        case 'geomap': loadGeoMap(); break;
        case 'network': loadNetwork(); break;
        case 'entities': loadEntities(); break;
        case 'dossier': loadDossierTab(); break;
        case 'communities': loadCommunities(); break;
        case 'patterns': loadPatterns(); break;
        case 'influencers': loadInfluencers(); break;
    }
}

// ═══ Search ═══════════════════════════════════════════════════
function setupSearch() {
    const input = document.getElementById('global-search');
    let timeout;
    input.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const q = input.value.trim();
            if (q.length >= 2) {
                searchEntities(q);
            }
        }, 300);
    });
}

async function searchEntities(query) {
    try {
        const res = await fetch(`${API}/api/entities?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        if (data.results && data.results.length > 0) {
            switchTab('entities');
            renderSearchResults(data.results);
        }
    } catch (e) {
        console.error('Search error:', e);
    }
}

function renderSearchResults(results) {
    const tbody = document.getElementById('entity-table-body');
    tbody.innerHTML = results.map(r => `
        <tr onclick="showEntityDetail('${r.id}')">
            <td>${r.name}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:var(--text-muted)">${r.id}</td>
            <td><span class="badge badge-${r.risk_level?.toLowerCase() || 'low'}">${r.risk_level || r.type}</span></td>
            <td>${r.type}</td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td style="white-space:nowrap">
                ${r.type === 'PERSON' ? `
                <button class="btn-sm" style="padding:3px 8px;font-size:0.75rem;background:rgba(2,132,199,0.15);color:var(--accent-blue);border:1px solid rgba(2,132,199,0.3);border-radius:4px;cursor:pointer" onclick="event.stopPropagation(); downloadDossierDirect('${r.id}', '${escapeQuotes(r.name)}')">
                    📄 PDF
                </button>
                <button class="btn-sm" style="padding:3px 8px;font-size:0.75rem;background:rgba(16,185,129,0.15);color:var(--accent-green);border:1px solid rgba(16,185,129,0.3);border-radius:4px;cursor:pointer;margin-left:4px" onclick="event.stopPropagation(); openPersonDossier('${r.id}')">
                    🗂️ Dossier
                </button>` : '—'}
            </td>
        </tr>
    `).join('');
    document.getElementById('entity-count').textContent = `${results.length} results`;
}

// ═══ Dashboard ════════════════════════════════════════════════
async function loadDashboard() {
    try {
        const res = await fetch(`${API}/api/dashboard`);
        const data = await res.json();
        lastDashboardData = data;
        renderKPIs(data);
        renderCharts(data);

        // Update pattern badge
        const patternCount = data.patterns?.critical_count + data.patterns?.high_count || 0;
        const badge = document.getElementById('pattern-badge');
        if (badge) badge.textContent = patternCount;
    } catch (e) {
        console.error('Dashboard error:', e);
    }
}

function renderKPIs(data) {
    const s = data.stats;
    const n = data.network;
    const p = data.patterns;
    const grid = document.getElementById('kpi-grid');

    grid.innerHTML = `
        <div class="kpi-card blue">
            <div class="kpi-label">Total Incidents</div>
            <div class="kpi-value">${(s.total_incidents || 0).toLocaleString()}</div>
            <div class="kpi-subtitle">${s.arrest_rate || 0}% arrest rate</div>
            <div class="kpi-icon">📋</div>
        </div>
        <div class="kpi-card emerald">
            <div class="kpi-label">Suspects Tracked</div>
            <div class="kpi-value">${(s.total_suspects || 0).toLocaleString()}</div>
            <div class="kpi-subtitle">${s.organizations_count || 0} organizations</div>
            <div class="kpi-icon">👤</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-label">Network Nodes</div>
            <div class="kpi-value">${(n.total_nodes || 0).toLocaleString()}</div>
            <div class="kpi-subtitle">${(n.total_edges || 0).toLocaleString()} connections</div>
            <div class="kpi-icon">🕸️</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-label">Communities</div>
            <div class="kpi-value">${n.communities_detected || 0}</div>
            <div class="kpi-subtitle">Largest: ${n.largest_community_size || 0} members</div>
            <div class="kpi-icon">🏘️</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-label">Critical Alerts</div>
            <div class="kpi-value">${p.critical_count || 0}</div>
            <div class="kpi-subtitle">${p.total_patterns || 0} total patterns</div>
            <div class="kpi-icon">⚠️</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-label">Suspicious Transactions</div>
            <div class="kpi-value">${(s.suspicious_transactions || 0).toLocaleString()}</div>
            <div class="kpi-subtitle">₹${formatAmount(s.suspicious_transaction_amount)} flagged</div>
            <div class="kpi-icon">💰</div>
        </div>
    `;
}

function formatAmount(amount) {
    if (!amount) return '0';
    if (amount >= 10000000) return (amount / 10000000).toFixed(1) + 'Cr';
    if (amount >= 100000) return (amount / 100000).toFixed(1) + 'L';
    if (amount >= 1000) return (amount / 1000).toFixed(1) + 'K';
    return amount.toFixed(0);
}

function renderCharts(data) {
    const s = data.stats;
    const isBright = currentTheme === 'light' || currentTheme === 'bright';
    const chartColors = isBright ? [
        '#2563eb', '#059669', '#10b981', '#f59e0b', '#ef4444',
        '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
        '#84cc16', '#e11d48', '#0891b2', '#7c3aed', '#d946ef'
    ] : [
        '#00f0ff', '#10b981', '#ffb703', '#ff2e5b', '#a855f7',
        '#38bdf8', '#fb923c', '#f43f5e', '#34d399', '#818cf8',
        '#fbbf24', '#f87171', '#2dd4bf', '#c084fc', '#e879f9'
    ];
    const textColor = isBright ? '#334155' : '#94a3b8';
    const tickColor = isBright ? '#475569' : '#64748b';
    const gridColor = isBright ? 'rgba(0, 0, 0, 0.06)' : 'rgba(0, 240, 255, 0.07)';
    const donutBorder = isBright ? '#ffffff' : '#0b1122';

    // Destroy existing charts
    Object.values(chartInstances).forEach(c => c?.destroy());

    // Crime Type Distribution (Doughnut)
    const crimeCtx = document.getElementById('chart-crime-types');
    if (crimeCtx && s.crime_type_distribution) {
        const labels = Object.keys(s.crime_type_distribution);
        const values = Object.values(s.crime_type_distribution);
        chartInstances.crime = new Chart(crimeCtx, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: chartColors.slice(0, labels.length),
                    borderColor: donutBorder,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, font: { size: 11, family: 'Inter' }, padding: 8 }
                    }
                },
                cutout: '55%'
            }
        });
    }

    // Monthly Trend (Line)
    const monthCtx = document.getElementById('chart-monthly');
    if (monthCtx && s.monthly_trend) {
        const labels = Object.keys(s.monthly_trend);
        const values = Object.values(s.monthly_trend);
        const lineAccent = isBright ? '#2563eb' : '#00f0ff';
        const lineFill = isBright ? 'rgba(37, 99, 235, 0.08)' : 'rgba(0, 240, 255, 0.12)';
        chartInstances.monthly = new Chart(monthCtx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Incidents',
                    data: values,
                    borderColor: lineAccent,
                    backgroundColor: lineFill,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: lineAccent,
                    pointBorderColor: donutBorder,
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        ticks: { color: tickColor, font: { size: 10, family: 'Inter' } },
                        grid: { color: gridColor }
                    },
                    y: {
                        ticks: { color: tickColor, font: { size: 10, family: 'Inter' } },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    }

    // Risk Distribution (Bar)
    const riskCtx = document.getElementById('chart-risk');
    if (riskCtx && s.risk_distribution) {
        const riskColors = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b', LOW: '#10b981' };
        const labels = Object.keys(s.risk_distribution);
        const values = Object.values(s.risk_distribution);
        chartInstances.risk = new Chart(riskCtx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Suspects',
                    data: values,
                    backgroundColor: labels.map(l => riskColors[l] || '#2563eb'),
                    borderRadius: 6,
                    barThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: tickColor, font: { family: 'Inter' } }, grid: { display: false } },
                    y: { ticks: { color: tickColor, font: { family: 'Inter' } }, grid: { color: gridColor } }
                }
            }
        });
    }

    // Top Locations (Horizontal Bar)
    const locCtx = document.getElementById('chart-locations');
    if (locCtx && s.top_locations) {
        const labels = Object.keys(s.top_locations).slice(0, 8);
        const values = labels.map(l => s.top_locations[l]);
        chartInstances.locations = new Chart(locCtx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Incidents',
                    data: values,
                    backgroundColor: isBright ? 'rgba(5, 150, 105, 0.75)' : 'rgba(16, 185, 129, 0.65)',
                    borderColor: isBright ? '#059669' : '#10b981',
                    borderWidth: 1,
                    borderRadius: 4,
                    barThickness: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: tickColor, font: { family: 'Inter' } }, grid: { color: gridColor } },
                    y: {
                        ticks: {
                            color: textColor,
                            font: { size: 10, family: 'Inter' },
                            callback: function(val) {
                                const label = this.getLabelForValue(val);
                                return label.length > 25 ? label.substr(0, 22) + '...' : label;
                            }
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

// ═══ Network Graph ════════════════════════════════════════════
async function loadNetwork() {
    if (networkInstance) return;

    const container = document.getElementById('network-container');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Building network visualization...</p></div>';

    try {
        const res = await fetch(`${API}/api/network`);
        allNetworkData = await res.json();
        renderNetwork(allNetworkData);
    } catch (e) {
        container.innerHTML = '<div class="loading"><p>❌ Failed to load network data</p></div>';
        console.error('Network error:', e);
    }
}

function renderNetwork(data) {
    const container = document.getElementById('network-container');
    container.innerHTML = '';

    const isBright = currentTheme === 'light' || currentTheme === 'bright';
    const fontColor = isBright ? '#0f172a' : '#f8fafc';
    const strokeColor = isBright ? '#ffffff' : '#060a14';
    const edgeFontColor = isBright ? '#475569' : '#94a3b8';

    const nodes = new vis.DataSet(data.nodes);
    const edges = new vis.DataSet(data.edges);

    const options = {
        nodes: {
            font: { color: fontColor, size: 11, face: 'Inter', strokeWidth: 3, strokeColor: strokeColor },
            borderWidth: 2,
            shadow: { enabled: true, color: isBright ? 'rgba(15,23,42,0.12)' : 'rgba(0,0,0,0.3)', size: 6 }
        },
        edges: {
            smooth: { type: 'continuous' },
            font: { color: edgeFontColor, size: 9, strokeWidth: 2, strokeColor: strokeColor }
        },
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -3000,
                centralGravity: 0.2,
                springLength: 150,
                springConstant: 0.02,
                damping: 0.09
            },
            stabilization: { iterations: 200 }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            multiselect: true,
            navigationButtons: true,
            keyboard: true
        },
        layout: {
            improvedLayout: true
        }
    };

    networkInstance = new vis.Network(container, { nodes, edges }, options);

    // Click handler
    networkInstance.on('click', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = data.nodes.find(n => n.id === nodeId);
            if (node && node.type === 'PERSON') {
                showEntityDetail(nodeId);
            }
        }
    });
}

function filterNetwork(filter) {
    if (!allNetworkData) return;

    // Update button states
    document.querySelectorAll('.network-controls .btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    let filteredNodes, filteredEdges;

    if (filter === 'all') {
        filteredNodes = allNetworkData.nodes;
        filteredEdges = allNetworkData.edges;
    } else if (filter === 'PERSON') {
        const personIds = new Set(allNetworkData.nodes.filter(n => n.type === 'PERSON').map(n => n.id));
        filteredNodes = allNetworkData.nodes.filter(n => n.type === 'PERSON');
        filteredEdges = allNetworkData.edges.filter(e => personIds.has(e.from) && personIds.has(e.to));
    } else if (filter === 'high-risk') {
        const highRiskIds = new Set(
            allNetworkData.nodes.filter(n => n.risk_level === 'HIGH' || n.risk_level === 'CRITICAL').map(n => n.id)
        );
        filteredNodes = allNetworkData.nodes.filter(n => highRiskIds.has(n.id) || n.type === 'ORGANIZATION');
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        filteredEdges = allNetworkData.edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
    }

    if (networkInstance) {
        networkInstance.destroy();
        networkInstance = null;
    }
    renderNetwork({ nodes: filteredNodes, edges: filteredEdges });
}

function resetNetworkZoom() {
    if (networkInstance) networkInstance.fit({ animation: true });
}

function togglePhysics() {
    physicsEnabled = !physicsEnabled;
    if (networkInstance) {
        networkInstance.setOptions({ physics: { enabled: physicsEnabled } });
    }
}

// ═══ Entities ═════════════════════════════════════════════════
async function loadEntities() {
    try {
        const res = await fetch(`${API}/api/entities`);
        const data = await res.json();
        renderEntities(data);
    } catch (e) {
        console.error('Entities error:', e);
    }
}

function renderEntities(data) {
    const persons = data.persons || [];
    document.getElementById('entity-count').textContent = `${persons.length} suspects`;

    const tbody = document.getElementById('entity-table-body');
    tbody.innerHTML = persons.map(p => {
        const riskClass = (p.risk_level || 'low').toLowerCase();
        return `
        <tr onclick="showEntityDetail('${p.id}')">
            <td>${p.name || '—'}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:var(--text-muted)">${p.id}</td>
            <td><span class="badge badge-${riskClass}">${p.risk_level || 'LOW'}</span></td>
            <td>${p.organization || '—'}</td>
            <td>${(p.incidents || []).length}</td>
            <td>${(p.calls_made || 0) + (p.calls_received || 0)}</td>
            <td>${p.criminal_records || 0}</td>
            <td style="white-space:nowrap">
                <button class="btn-sm" style="padding:3px 8px;font-size:0.75rem;background:rgba(2,132,199,0.15);color:var(--accent-blue);border:1px solid rgba(2,132,199,0.3);border-radius:4px;cursor:pointer" onclick="event.stopPropagation(); downloadDossierDirect('${p.id}', '${escapeQuotes(p.name)}')">
                    📄 PDF
                </button>
                <button class="btn-sm" style="padding:3px 8px;font-size:0.75rem;background:rgba(16,185,129,0.15);color:var(--accent-green);border:1px solid rgba(16,185,129,0.3);border-radius:4px;cursor:pointer;margin-left:4px" onclick="event.stopPropagation(); openPersonDossier('${p.id}')">
                    🗂️ Dossier
                </button>
            </td>
        </tr>`;
    }).join('');
}

// ═══ Entity Detail Modal ══════════════════════════════════════
let currentModalEntityId = null;
let currentModalEntityName = null;

async function showEntityDetail(entityId) {
    try {
        const res = await fetch(`${API}/api/entity/${entityId}`);
        const data = await res.json();

        if (data.error) {
            alert('Entity not found');
            return;
        }

        const e = data.entity;
        currentModalEntityId = entityId;
        currentModalEntityName = e.name || entityId;
        const modal = document.getElementById('entity-modal');
        document.getElementById('modal-title').textContent = e.name || entityId;

        const content = document.getElementById('modal-content');
        content.innerHTML = `
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">ID</div>
                    <div class="detail-value" style="font-family:'JetBrains Mono',monospace">${e.id}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Risk Level</div>
                    <div class="detail-value"><span class="badge badge-${(e.risk_level||'low').toLowerCase()}">${e.risk_level || 'LOW'}</span></div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Phone</div>
                    <div class="detail-value">${e.phone || '—'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Organization</div>
                    <div class="detail-value">${e.organization || '—'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Age / Gender</div>
                    <div class="detail-value">${e.age || '—'} / ${e.gender || '—'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Address</div>
                    <div class="detail-value">${e.address || '—'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Incidents</div>
                    <div class="detail-value" style="color:var(--accent-amber)">${(e.incidents || []).length}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Total Calls</div>
                    <div class="detail-value" style="color:var(--accent-cyan)">${(e.calls_made||0) + (e.calls_received||0)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Money Sent</div>
                    <div class="detail-value" style="color:var(--accent-emerald)">₹${formatAmount(e.total_sent)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Money Received</div>
                    <div class="detail-value" style="color:var(--accent-emerald)">₹${formatAmount(e.total_received)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Criminal Records</div>
                    <div class="detail-value" style="color:var(--accent-red)">${e.criminal_records || 0}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Known Associates</div>
                    <div class="detail-value">${(e.known_associates || []).length}</div>
                </div>
            </div>

            ${data.incidents && data.incidents.length > 0 ? `
            <div style="margin-top:20px">
                <h4 style="margin-bottom:10px;font-size:0.9rem">📋 Recent Incidents (${data.incidents.length})</h4>
                <div style="max-height:200px;overflow-y:auto">
                    ${data.incidents.slice(0, 10).map(inc => `
                        <div class="pattern-card severity-MEDIUM" style="padding:12px;margin-bottom:8px">
                            <div style="display:flex;justify-content:space-between;align-items:center">
                                <strong>${inc.crime_type || '—'}</strong>
                                <span style="font-size:0.75rem;color:var(--text-muted)">${inc.date || '—'}</span>
                            </div>
                            <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px">${inc.location || '—'}</div>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}

            ${data.criminal_history && data.criminal_history.length > 0 ? `
            <div style="margin-top:20px">
                <h4 style="margin-bottom:10px;font-size:0.9rem">📜 Criminal History (${data.criminal_history.length})</h4>
                <div style="max-height:200px;overflow-y:auto">
                    ${data.criminal_history.map(rec => `
                        <div class="pattern-card severity-HIGH" style="padding:12px;margin-bottom:8px">
                            <div style="display:flex;justify-content:space-between;align-items:center">
                                <strong>${rec.crime_type || '—'}</strong>
                                <span class="badge badge-${rec.status === 'CONVICTED' ? 'critical' : rec.status === 'PENDING' ? 'medium' : 'low'}">${rec.status || '—'}</span>
                            </div>
                            <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px">
                                ${rec.date || '—'} • ${rec.court || '—'} • Sentence: ${rec.sentence || '—'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
        `;

        modal.classList.add('active');
    } catch (e) {
        console.error('Entity detail error:', e);
    }
}

function closeModal() {
    document.getElementById('entity-modal').classList.remove('active');
}

// Close modal on overlay click
document.getElementById('entity-modal')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
});

// ═══ Communities ═══════════════════════════════════════════════
async function loadCommunities() {
    try {
        const res = await fetch(`${API}/api/network/communities`);
        const data = await res.json();
        renderCommunities(data.communities || []);
    } catch (e) {
        console.error('Communities error:', e);
    }
}

function renderCommunities(communities) {
    const container = document.getElementById('communities-container');
    if (!communities.length) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">🏘️</div><p>No communities detected</p></div>';
        return;
    }

    container.innerHTML = communities.map((c, i) => {
        const threatClass = (c.threat_level || 'low').toLowerCase();
        return `
        <div class="community-card">
            <div class="community-header">
                <h3 style="font-size:0.95rem">Cluster #${i + 1} — ${c.size} members</h3>
                <span class="badge badge-${threatClass}">${c.threat_level || 'LOW'}</span>
            </div>
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:8px">
                ${c.organizations?.length ? `Orgs: ${c.organizations.join(', ')}` : 'No organization affiliation'}
            </div>
            <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:8px">
                Incidents: ${c.total_incidents || 0} |
                Risk profile: ${Object.entries(c.risk_profile || {}).map(([k, v]) => `${k}: ${v}`).join(', ')}
            </div>
            <div class="community-members">
                ${(c.members || []).slice(0, 12).map(m => `
                    <div class="member-chip" onclick="showEntityDetail('${m.id}')">
                        <span class="badge badge-${(m.risk_level||'low').toLowerCase()}" style="padding:1px 4px;font-size:0.6rem">●</span>
                        ${m.name}
                    </div>
                `).join('')}
                ${c.members?.length > 12 ? `<div class="member-chip">+${c.members.length - 12} more</div>` : ''}
            </div>
        </div>`;
    }).join('');
}

// ═══ Patterns & Alerts ════════════════════════════════════════
let fullPatternsList = [];
let patternFiltersInitialized = false;

async function loadPatterns() {
    try {
        const res = await fetch(`${API}/api/patterns`);
        const data = await res.json();
        fullPatternsList = data.patterns || [];
        const activeBtn = document.querySelector('.filter-btn.active');
        const activeFilter = activeBtn ? activeBtn.dataset.filter : 'all';
        applyPatternFilter(activeFilter);
        setupPatternFilters();
    } catch (e) {
        console.error('Patterns error:', e);
    }
}

function applyPatternFilter(filter) {
    if (!filter || filter === 'all') {
        renderPatterns(fullPatternsList);
    } else {
        const filtered = fullPatternsList.filter(p => (p.severity || '').toUpperCase() === filter.toUpperCase());
        renderPatterns(filtered);
    }
}

function renderPatterns(patterns) {
    const container = document.getElementById('patterns-container');
    if (!patterns || !patterns.length) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><p>No patterns detected for this filter</p></div>';
        return;
    }

    container.innerHTML = patterns.map(p => `
        <div class="pattern-card severity-${p.severity || 'LOW'}">
            <div class="pattern-header">
                <h4>${p.title || 'Unknown Pattern'}</h4>
                <span class="badge badge-${(p.severity || 'low').toLowerCase()}">${p.severity || 'LOW'}</span>
            </div>
            <div class="pattern-description">${p.description || ''}</div>
            <div class="pattern-meta">
                <span>📁 ${p.category || 'General'}</span>
                <span>🏷️ ${p.type || 'Unknown'}</span>
                ${p.entity_name ? `<span>👤 ${p.entity_name}</span>` : ''}
                ${p.location ? `<span>📍 ${p.location}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function setupPatternFilters() {
    if (patternFiltersInitialized) return;
    patternFiltersInitialized = true;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.dataset.filter;
            applyPatternFilter(filter);
        });
    });
}

// ═══ Influencers ══════════════════════════════════════════════
async function loadInfluencers() {
    try {
        const res = await fetch(`${API}/api/network/influencers?top=20`);
        const data = await res.json();
        renderInfluencers(data.influencers || []);
    } catch (e) {
        console.error('Influencers error:', e);
    }
}

function renderInfluencers(influencers) {
    const tbody = document.getElementById('influencer-table-body');
    const maxScore = influencers[0]?.composite_score || 1;

    tbody.innerHTML = influencers.map((inf, i) => {
        const rankClass = i < 3 ? 'top-3' : '';
        const riskClass = (inf.risk_level || 'low').toLowerCase();
        const scoreWidth = (inf.composite_score / maxScore * 100).toFixed(0);
        const btwWidth = (inf.betweenness_centrality * 100 / 0.15).toFixed(0);

        return `
        <tr onclick="showEntityDetail('${inf.id}')" style="cursor:pointer">
            <td><span class="influencer-rank ${rankClass}">${i + 1}</span></td>
            <td style="font-weight:600;color:var(--text-primary)">${inf.name}</td>
            <td><span class="badge badge-${riskClass}">${inf.risk_level || 'LOW'}</span></td>
            <td>${inf.organization || '—'}</td>
            <td>${inf.connections}</td>
            <td>
                <div class="metric-bar"><div class="metric-bar-fill" style="width:${Math.min(btwWidth, 100)}%"></div></div>
                ${inf.betweenness_centrality}
            </td>
            <td>${inf.pagerank}</td>
            <td>
                <div class="metric-bar"><div class="metric-bar-fill" style="width:${scoreWidth}%;background:var(--gradient-warning)"></div></div>
                <strong>${inf.composite_score}</strong>
            </td>
        </tr>`;
    }).join('');
}

// ═══ Prediction Console ═══════════════════════════════════════
async function predictCrimeType(e) {
    e.preventDefault();

    const payload = {
        hour: parseInt(document.getElementById('pred-hour').value),
        day_of_week: parseInt(document.getElementById('pred-day').value),
        month: parseInt(document.getElementById('pred-month').value),
        beat: parseInt(document.getElementById('pred-beat').value),
        district: parseInt(document.getElementById('pred-district').value),
        community_area: parseInt(document.getElementById('pred-community').value),
        location_description: document.getElementById('pred-location').value,
    };

    const container = document.getElementById('crime-prediction-result');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/api/predict/crime-type`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderCrimePrediction(data, container);
    } catch (e) {
        container.innerHTML = '<p style="color:var(--accent-red)">❌ Prediction failed</p>';
    }
}

function renderCrimePrediction(data, container) {
    if (data.error) {
        container.innerHTML = `<p style="color:var(--accent-red)">❌ ${data.error}</p>`;
        return;
    }

    container.innerHTML = `
        <div class="prediction-result">
            <div class="prediction-main">
                <div>
                    <div class="prediction-label">Predicted Crime Type</div>
                    <div class="prediction-value">${data.prediction}</div>
                </div>
                <div class="confidence">
                    <div style="font-size:0.8rem;color:var(--text-muted)">Confidence</div>
                    <div style="font-size:1.2rem;font-weight:700;color:var(--accent-cyan)">${data.confidence}%</div>
                    <div class="confidence-bar">
                        <div class="confidence-bar-fill" style="width:${data.confidence}%"></div>
                    </div>
                </div>
            </div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:12px">Model: ${data.model_used}</div>
            <h4 style="font-size:0.85rem;margin-bottom:10px">Top Predictions</h4>
            <ul class="probability-list">
                ${(data.top_predictions || []).map(p => `
                    <li class="probability-item">
                        <span class="probability-name">${p.crime_type}</span>
                        <div class="probability-bar-container">
                            <div class="probability-bar" style="width:${p.probability}%"></div>
                        </div>
                        <span class="probability-value">${p.probability}%</span>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

async function predictArrest(e) {
    e.preventDefault();

    const payload = {
        hour: parseInt(document.getElementById('arrest-hour').value),
        day_of_week: parseInt(document.getElementById('arrest-day').value),
        month: parseInt(document.getElementById('arrest-month').value),
        beat: parseInt(document.getElementById('arrest-beat').value),
        district: parseInt(document.getElementById('arrest-district').value),
        community_area: parseInt(document.getElementById('arrest-community').value),
        primary_type: document.getElementById('arrest-crime-type').value,
        location_description: document.getElementById('arrest-location').value,
    };

    const container = document.getElementById('arrest-prediction-result');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/api/predict/arrest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderArrestPrediction(data, container);
    } catch (e) {
        container.innerHTML = '<p style="color:var(--accent-red)">❌ Prediction failed</p>';
    }
}

function renderArrestPrediction(data, container) {
    if (data.error) {
        container.innerHTML = `<p style="color:var(--accent-red)">❌ ${data.error}</p>`;
        return;
    }

    const color = data.arrest_likely ? 'var(--accent-emerald)' : 'var(--accent-red)';
    const icon = data.arrest_likely ? '✅' : '❌';

    container.innerHTML = `
        <div class="prediction-result">
            <div class="prediction-main" style="border-color:${data.arrest_likely ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'};background:${data.arrest_likely ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)'}">
                <div>
                    <div class="prediction-label">Arrest Prediction</div>
                    <div class="prediction-value" style="color:${color}">${icon} ${data.arrest_likely ? 'LIKELY' : 'UNLIKELY'}</div>
                </div>
                <div class="confidence">
                    <div style="font-size:0.8rem;color:var(--text-muted)">Probability</div>
                    <div style="font-size:1.2rem;font-weight:700;color:${color}">${data.arrest_probability}%</div>
                    <div class="confidence-bar">
                        <div class="confidence-bar-fill" style="width:${data.arrest_probability}%;background:${data.arrest_likely ? 'var(--gradient-success)' : 'var(--gradient-danger)'}"></div>
                    </div>
                </div>
            </div>
            <div style="font-size:0.75rem;color:var(--text-muted)">Model: ${data.model_used}</div>
        </div>
    `;
}

// ═══ NLP Analyzer ═════════════════════════════════════════════
async function analyzeText() {
    const text = document.getElementById('nlp-input').value.trim();
    if (!text) return;

    const container = document.getElementById('nlp-results');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analyzing text...</p></div>';

    try {
        const res = await fetch(`${API}/api/analyze-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        renderNLPResults(data, container);
    } catch (e) {
        container.innerHTML = '<p style="color:var(--accent-red)">❌ Analysis failed</p>';
    }
}

function renderNLPResults(data, container) {
    const entities = data.entities || {};
    const threatColors = {
        CRITICAL: 'var(--accent-red)', HIGH: '#f97316',
        MEDIUM: 'var(--accent-amber)', LOW: 'var(--accent-emerald)'
    };

    const entityTypeConfig = {
        PERSON: { class: 'person', icon: '👤' },
        ORGANIZATION: { class: 'org', icon: '🏢' },
        LOCATION: { class: 'location', icon: '📍' },
        PHONE: { class: 'phone', icon: '📱' },
        VEHICLE_PLATE: { class: 'phone', icon: '🚗' },
        CASE_ID: { class: 'org', icon: '📁' },
        DATE: { class: 'location', icon: '📅' },
        DATE_PATTERN: { class: 'location', icon: '📅' },
        MONEY: { class: 'org', icon: '💰' },
        MONEY_INR: { class: 'org', icon: '💰' },
        GROUP: { class: 'person', icon: '👥' },
    };

    let entityHTML = '';
    for (const [type, values] of Object.entries(entities)) {
        if (!values.length) continue;
        const config = entityTypeConfig[type] || { class: '', icon: '🏷️' };
        entityHTML += `
            <div class="entity-tag-group">
                <h4>${config.icon} ${type} (${values.length})</h4>
                <div class="entity-tags">
                    ${values.map(v => `<span class="entity-tag ${config.class}">${v}</span>`).join('')}
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div style="margin-top:20px">
            <div class="threat-indicator level-${data.threat_level || 'LOW'}">
                <span style="font-size:1.5rem">${data.threat_level === 'CRITICAL' ? '🔴' : data.threat_level === 'HIGH' ? '🟠' : data.threat_level === 'MEDIUM' ? '🟡' : '🟢'}</span>
                <div>
                    <div style="font-weight:700;color:${threatColors[data.threat_level] || '#34d399'}">
                        Threat Level: ${data.threat_level || 'LOW'}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text-secondary)">
                        ${data.threat_indicators?.length ? `Keywords: ${data.threat_indicators.join(', ')}` : 'No critical keywords detected'}
                    </div>
                </div>
                <div style="margin-left:auto;text-align:right;font-size:0.8rem;color:var(--text-muted)">
                    ${data.word_count || 0} words analyzed
                </div>
            </div>

            <div class="nlp-results">
                ${entityHTML || '<div class="empty-state"><p>No entities extracted</p></div>'}
            </div>

            ${data.relationships?.length ? `
            <div style="margin-top:20px">
                <h4 style="margin-bottom:10px;font-size:0.9rem">🔗 Extracted Relationships (${data.relationships.length})</h4>
                <div style="max-height:200px;overflow-y:auto">
                    ${data.relationships.slice(0, 15).map(r => `
                        <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border-color);font-size:0.82rem">
                            <span class="entity-tag ${entityTypeConfig[r.source_type]?.class || ''}" style="font-size:0.75rem">${r.source}</span>
                            <span style="color:var(--text-muted)">→ ${r.relation} →</span>
                            <span class="entity-tag ${entityTypeConfig[r.target_type]?.class || ''}" style="font-size:0.75rem">${r.target}</span>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}

            ${data.key_sentences?.length ? `
            <div style="margin-top:20px">
                <h4 style="margin-bottom:10px;font-size:0.9rem">📌 Key Sentences</h4>
                ${data.key_sentences.map(s => `
                    <p style="font-size:0.83rem;color:var(--text-secondary);padding:8px 12px;background:var(--bg-glass);border-radius:var(--radius-sm);margin-bottom:6px;border-left:3px solid var(--accent-blue)">
                        "${s}"
                    </p>
                `).join('')}
            </div>` : ''}
        </div>
    `;
}

// ═══ Ingest Intel (Add Criminal & Crime) ══════════════════════
async function handleAddSuspect(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-submit-suspect');
    const msg = document.getElementById('suspect-status-msg');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Injecting Suspect into Graph...</span>';
    msg.innerHTML = '';

    const payload = {
        name: document.getElementById('suspect-name').value.trim(),
        risk_level: document.getElementById('suspect-risk').value,
        age: document.getElementById('suspect-age').value,
        gender: document.getElementById('suspect-gender').value,
        organization: document.getElementById('suspect-org').value.trim(),
        phone: document.getElementById('suspect-phone').value.trim(),
        known_associates: document.getElementById('suspect-associates').value.trim(),
        address: document.getElementById('suspect-address').value.trim(),
        prior_records: document.getElementById('suspect-records').value
    };

    try {
        const res = await fetch(`${API}/api/suspects/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
            msg.innerHTML = `<div style="color:var(--accent-emerald);font-weight:600;padding:10px;border-radius:6px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3)">
                ✅ ${data.message} — Node successfully active in Network Graph!
            </div>`;
            document.getElementById('form-add-suspect').reset();
            loadDashboard();
            allNetworkData = null;
        } else {
            msg.innerHTML = `<div style="color:var(--accent-red);padding:10px;border-radius:6px;background:rgba(239,68,68,0.1)">❌ ${data.error || 'Failed to add suspect'}</div>`;
        }
    } catch (err) {
        msg.innerHTML = `<div style="color:var(--accent-red);padding:10px;border-radius:6px;background:rgba(239,68,68,0.1)">❌ Network error: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>➕ Add Suspect to Graph Network</span>';
    }
}

async function handleAddIncident(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-submit-incident');
    const msg = document.getElementById('incident-status-msg');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Linking Crime to Network...</span>';
    msg.innerHTML = '';

    const dtVal = document.getElementById('incident-datetime').value;
    const datePart = dtVal ? dtVal.split('T')[0] : new Date().toISOString().split('T')[0];
    const timePart = dtVal ? dtVal.split('T')[1] : '12:00:00';

    const payload = {
        crime_type: document.getElementById('incident-type').value,
        date: datePart,
        time: timePart,
        location: document.getElementById('incident-location').value.trim(),
        suspect1_id: document.getElementById('incident-suspect1').value.trim(),
        suspect2_id: document.getElementById('incident-suspect2').value.trim(),
        narrative: document.getElementById('incident-narrative').value.trim()
    };

    try {
        const res = await fetch(`${API}/api/incidents/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
            msg.innerHTML = `<div style="color:var(--accent-cyan);font-weight:600;padding:10px;border-radius:6px;background:rgba(5,150,105,0.1);border:1px solid rgba(5,150,105,0.3)">
                ✅ ${data.message} — Incident linked to suspects and timeline updated!
            </div>`;
            document.getElementById('form-add-incident').reset();
            loadDashboard();
            allNetworkData = null;
        } else {
            msg.innerHTML = `<div style="color:var(--accent-red);padding:10px;border-radius:6px;background:rgba(239,68,68,0.1)">❌ ${data.error || 'Failed to log incident'}</div>`;
        }
    } catch (err) {
        msg.innerHTML = `<div style="color:var(--accent-red);padding:10px;border-radius:6px;background:rgba(239,68,68,0.1)">❌ Network error: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🚨 Log Crime & Link Accomplices</span>';
    }
}

// ═══════════════════════════════════════════════════════════════
// ═══ Person Dossier & PDF Generator Module ═════════════════════
// ═══════════════════════════════════════════════════════════════

let currentDossierPersonId = null;
let currentDossierData = null;
let allDossierSuspects = [];
let currentDossierRiskFilter = 'ALL';
let dossierListenersInitialized = false;

function escapeQuotes(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function formatAmount(amount) {
    const num = parseFloat(amount || 0);
    if (isNaN(num)) return '0';
    if (num >= 10000000) return (num / 10000000).toFixed(2) + ' Cr';
    if (num >= 100000) return (num / 100000).toFixed(2) + ' Lakh';
    return num.toLocaleString('en-IN');
}

function downloadCurrentModalDossier() {
    if (currentModalEntityId) {
        downloadDossierDirect(currentModalEntityId, currentModalEntityName);
    }
}

function downloadDossierDirect(personId, personName) {
    if (!personId) return;
    const cleanName = (personName || personId).replace(/[^a-zA-Z0-9]/g, '_');
    const downloadUrl = `${API}/api/dossier/pdf/${encodeURIComponent(personId)}`;

    // Create a temporary hidden link to trigger direct browser file download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `DOSSIER_${personId}_${cleanName}.pdf`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function openPersonDossier(personId) {
    switchTab('dossier');
    selectDossierPerson(personId);
}

function openDossierPrintView() {
    if (!currentDossierPersonId) return;
    const previewUrl = `${API}/api/dossier/pdf/${encodeURIComponent(currentDossierPersonId)}`;
    window.open(previewUrl, '_blank');
}

async function loadDossierTab() {
    setupDossierListeners();

    try {
        const res = await fetch(`${API}/api/dossier/search?q=`);
        const data = await res.json();
        allDossierSuspects = data.results || [];
        document.getElementById('dossier-suspect-count').textContent = allDossierSuspects.length;

        applyDossierRiskFilter();

        // If no suspect is selected, auto-select the first one so the user has immediate rich content
        if (!currentDossierPersonId && allDossierSuspects.length > 0) {
            selectDossierPerson(allDossierSuspects[0].id);
        } else if (currentDossierPersonId) {
            highlightActiveQuickCard(currentDossierPersonId);
        }
    } catch (e) {
        console.error('Failed to load dossier suspects:', e);
    }
}

function setupDossierListeners() {
    if (dossierListenersInitialized) return;
    dossierListenersInitialized = true;

    // Search input with debounce
    const searchInput = document.getElementById('dossier-search-input');
    const clearBtn = document.getElementById('dossier-search-clear');
    let searchTimeout;

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            const q = searchInput.value.trim();
            if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

            searchTimeout = setTimeout(() => {
                searchDossierSuspects(q);
            }, 250);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('dossier-autocomplete-dropdown');
            if (dropdown && !dropdown.contains(e.target) && e.target !== searchInput) {
                dropdown.style.display = 'none';
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            document.getElementById('dossier-autocomplete-dropdown').style.display = 'none';
            searchDossierSuspects('');
        });
    }

    // Risk Filter Pills
    document.querySelectorAll('#dossier-risk-pills .dossier-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('#dossier-risk-pills .dossier-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            currentDossierRiskFilter = pill.dataset.risk || 'ALL';
            applyDossierRiskFilter();
        });
    });

    // Sub-Section Navigation Tabs
    document.querySelectorAll('.dossier-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.dossier-nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const section = btn.dataset.section;
            document.querySelectorAll('.dossier-section-panel').forEach(p => p.style.display = 'none');
            const targetPanel = document.getElementById(`d-section-${section}`);
            if (targetPanel) targetPanel.style.display = 'block';
        });
    });
}

function applyDossierRiskFilter() {
    let filtered = allDossierSuspects;
    if (currentDossierRiskFilter !== 'ALL') {
        filtered = allDossierSuspects.filter(s => (s.risk_level || '').toUpperCase() === currentDossierRiskFilter);
    }
    renderDossierQuickList(filtered);
}

async function searchDossierSuspects(query) {
    const dropdown = document.getElementById('dossier-autocomplete-dropdown');
    if (!query) {
        if (dropdown) dropdown.style.display = 'none';
        applyDossierRiskFilter();
        return;
    }

    try {
        const res = await fetch(`${API}/api/dossier/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        const results = data.results || [];

        // Render quick carousel with results
        renderDossierQuickList(results);

        // Render Autocomplete Dropdown
        if (dropdown) {
            if (results.length === 0) {
                dropdown.innerHTML = '<div class="dossier-dropdown-empty">No matching suspects found</div>';
                dropdown.style.display = 'block';
            } else {
                dropdown.innerHTML = results.slice(0, 8).map(s => `
                    <div class="dossier-dropdown-item" onclick="selectDossierPerson('${s.id}')">
                        <div class="dossier-dropdown-avatar">${getInitials(s.name)}</div>
                        <div class="dossier-dropdown-info">
                            <div class="dossier-dropdown-title">
                                <strong>${s.name}</strong>
                                <span class="badge badge-${(s.risk_level || 'low').toLowerCase()}">${s.risk_level || 'LOW'}</span>
                            </div>
                            <div class="dossier-dropdown-sub">
                                <span style="font-family:'JetBrains Mono',monospace">${s.id}</span> • 
                                ${s.organization || 'Independent'} • 
                                ${s.phone || 'No phone'}
                            </div>
                        </div>
                    </div>
                `).join('');
                dropdown.style.display = 'block';
            }
        }
    } catch (e) {
        console.error('Error searching dossier suspects:', e);
    }
}

function renderDossierQuickList(suspects) {
    const container = document.getElementById('dossier-quick-list');
    if (!container) return;

    if (!suspects || suspects.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;padding:8px 0">No suspects match the selected criteria.</div>';
        return;
    }

    container.innerHTML = suspects.map(s => {
        const riskClass = (s.risk_level || 'low').toLowerCase();
        const isActive = s.id === currentDossierPersonId ? 'active' : '';
        const initials = getInitials(s.name);
        return `
            <div class="dossier-quick-card ${isActive}" id="quick-card-${s.id}" onclick="selectDossierPerson('${s.id}')">
                <div class="quick-card-top">
                    <div class="quick-avatar ${riskClass}">${initials}</div>
                    <span class="badge badge-${riskClass}">${s.risk_level || 'LOW'}</span>
                </div>
                <div class="quick-card-name" title="${s.name}">${s.name}</div>
                <div class="quick-card-meta">
                    <span style="font-family:'JetBrains Mono',monospace">${s.id}</span> • ${s.organization || 'Independent'}
                </div>
                <div class="quick-card-stats">
                    <span>🚨 ${s.incidents_count || 0} FIRs</span>
                    <span>📞 ${s.calls_count || 0} calls</span>
                </div>
            </div>
        `;
    }).join('');

    if (currentDossierPersonId) {
        highlightActiveQuickCard(currentDossierPersonId);
    }
}

function highlightActiveQuickCard(personId) {
    document.querySelectorAll('.dossier-quick-card').forEach(c => c.classList.remove('active'));
    const target = document.getElementById(`quick-card-${personId}`);
    if (target) {
        target.classList.add('active');
        target.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
}

function getInitials(name) {
    if (!name) return '??';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
}

async function selectDossierPerson(personId) {
    if (!personId) return;

    // Close autocomplete dropdown
    const dropdown = document.getElementById('dossier-autocomplete-dropdown');
    if (dropdown) dropdown.style.display = 'none';

    try {
        const res = await fetch(`${API}/api/dossier/preview/${encodeURIComponent(personId)}`);
        if (!res.ok) {
            alert(`Could not load dossier for ${personId}`);
            return;
        }

        const data = await res.json();
        currentDossierData = data;
        currentDossierPersonId = personId;

        // Reveal dossier profile and hide empty state
        document.getElementById('dossier-empty-state').style.display = 'none';
        document.getElementById('dossier-profile-card').style.display = 'block';

        highlightActiveQuickCard(personId);
        renderDossierView(data);
    } catch (e) {
        console.error('Failed to load dossier preview:', e);
    }
}

function renderDossierView(data) {
    const p = data.entity || {};
    const stats = data.stats || {};
    const riskClass = (p.risk_level || 'low').toLowerCase();

    // ── Hero Banner ──
    const avatar = document.getElementById('dossier-avatar');
    if (avatar) {
        avatar.textContent = getInitials(p.name);
        avatar.className = `dossier-avatar ${riskClass}`;
    }

    document.getElementById('dossier-hero-name').textContent = p.name || 'Unknown Subject';
    const riskBadge = document.getElementById('dossier-hero-risk');
    riskBadge.textContent = `${p.risk_level || 'LOW'} RISK`;
    riskBadge.className = `badge badge-${riskClass}`;
    document.getElementById('dossier-hero-id').textContent = p.id || '';
    document.getElementById('dossier-hero-org').textContent = p.organization ? `🏛️ ${p.organization}` : '🏛️ Independent / Unaffiliated';
    document.getElementById('dossier-hero-phone').textContent = p.phone ? `📞 ${p.phone}${p.phone2 ? ' (Alt: ' + p.phone2 + ')' : ''}` : '📞 No registered phone';
    document.getElementById('dossier-hero-age').textContent = `🎂 ${p.age || '—'} yrs / ${p.gender || '—'}`;
    document.getElementById('dossier-hero-address').textContent = p.address ? `📍 ${p.address}` : '📍 Base location unverified';

    // ── KPI Stats ──
    document.getElementById('d-stat-incidents').textContent = stats.total_incidents || 0;
    document.getElementById('d-stat-convictions').textContent = stats.total_criminal_records || 0;
    document.getElementById('d-stat-calls').textContent = `${stats.total_cdr || 0} (${stats.calls_made || 0}↑/${stats.calls_received || 0}↓)`;
    document.getElementById('d-stat-sent').textContent = `₹${formatAmount(stats.total_sent + stats.total_received)}`;
    document.getElementById('d-stat-suspicious').textContent = stats.suspicious_transactions || 0;
    document.getElementById('d-stat-associates').textContent = stats.total_associates || 0;

    // ── 1. Master Life Chronology Timeline ──
    const timeline = data.life_timeline || [];
    document.getElementById('d-timeline-count').textContent = timeline.length;
    const timelineContainer = document.getElementById('dossier-timeline-list');
    if (timeline.length === 0) {
        timelineContainer.innerHTML = '<div class="dossier-empty-sub">No chronological activity records logged for this person.</div>';
    } else {
        timelineContainer.innerHTML = timeline.map(evt => {
            let icon = '📌';
            let badgeClass = 'badge-low';
            if (evt.badge === 'FIR' || evt.type === 'CRIME_INCIDENT') {
                icon = '🚨';
                badgeClass = 'badge-critical';
            } else if (evt.badge === 'COURT' || evt.type === 'JUDICIAL_RECORD') {
                icon = '⚖️';
                badgeClass = 'badge-high';
            } else if (evt.badge === 'HAWALA') {
                icon = '⚠️';
                badgeClass = 'badge-high';
            } else if (evt.type === 'FINANCIAL_TRANSACTION') {
                icon = '💸';
                badgeClass = 'badge-medium';
            } else if (evt.badge === 'CDR' || evt.type === 'TELECOM_INTERCEPT') {
                icon = '📞';
                badgeClass = 'badge-low';
            }

            return `
                <div class="dossier-timeline-item">
                    <div class="timeline-dot ${badgeClass}"></div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="timeline-time">${evt.date} ${evt.time ? evt.time : ''}</span>
                            <span class="badge ${badgeClass}">${evt.badge || evt.type}</span>
                        </div>
                        <div class="timeline-title">${icon} ${evt.title}</div>
                        <div class="timeline-desc">${evt.description}</div>
                        ${evt.location ? `<div class="timeline-meta">📍 ${evt.location}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── 2. FIRs & Crime Incidents ──
    const incidents = data.incidents || [];
    document.getElementById('d-incidents-count').textContent = incidents.length;
    const incTbody = document.getElementById('d-incidents-table-body');
    if (incidents.length === 0) {
        incTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:16px">No FIR incident records logged.</td></tr>';
    } else {
        incTbody.innerHTML = incidents.map(inc => {
            const isArrest = inc.arrest in [true, "True", "true", 1, "1"];
            const co = [];
            if (inc.suspect1_name && String(inc.suspect1_id) !== String(p.id)) co.push(inc.suspect1_name);
            if (inc.suspect2_name && String(inc.suspect2_id) !== String(p.id)) co.push(inc.suspect2_name);
            const coStr = co.length > 0 ? co.join(', ') : 'Solo / Unidentified';

            return `
                <tr>
                    <td style="font-family:'JetBrains Mono',monospace">${inc.incident_id || '—'}</td>
                    <td><strong>${inc.crime_type || '—'}</strong></td>
                    <td>${inc.date || ''} ${inc.time || ''}</td>
                    <td>${inc.location || '—'}</td>
                    <td>${coStr}</td>
                    <td><span class="badge badge-${isArrest ? 'low' : 'critical'}">${isArrest ? 'Arrested' : 'Fled / Wanted'}</span></td>
                    <td style="max-width:280px;font-size:0.75rem;color:var(--text-secondary)">${inc.narrative ? (inc.narrative.slice(0, 140) + '...') : '—'}</td>
                </tr>
            `;
        }).join('');
    }

    // ── 3. Intercepted Communications (CDR) ──
    const cdr = data.cdr_records || [];
    document.getElementById('d-cdr-count').textContent = cdr.length;
    const cdrTbody = document.getElementById('d-cdr-table-body');
    if (cdr.length === 0) {
        cdrTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:16px">No CDR telecommunication intercepts logged.</td></tr>';
    } else {
        cdrTbody.innerHTML = cdr.slice(0, 40).map(c => {
            const isCaller = String(c.caller_id) === String(p.id);
            const dirBadge = isCaller ?
                '<span class="badge" style="background:rgba(2,132,199,0.15);color:var(--accent-blue)">Outbound ↑</span>' :
                '<span class="badge" style="background:rgba(16,185,129,0.15);color:var(--accent-green)">Inbound ↓</span>';
            const targetPhone = isCaller ? (c.receiver_phone || c.receiver_id) : (c.caller_phone || c.caller_id);

            return `
                <tr>
                    <td style="font-family:'JetBrains Mono',monospace">${c.cdr_id || '—'}</td>
                    <td>${c.date || ''} ${c.time || ''}</td>
                    <td>${dirBadge}</td>
                    <td>${c.call_type || 'VOICE'}</td>
                    <td>${targetPhone || 'Unknown'}</td>
                    <td>${c.duration_seconds ? c.duration_seconds + 's' : '0s (SMS)'}</td>
                    <td>${c.cell_tower_location || '—'}</td>
                </tr>
            `;
        }).join('');
    }

    // ── 4. Financial & Hawala Audit ──
    const txns = data.transactions || [];
    document.getElementById('d-tx-count').textContent = txns.length;
    const txTbody = document.getElementById('d-tx-table-body');
    if (txns.length === 0) {
        txTbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-muted);padding:16px">No financial transaction records found.</td></tr>';
    } else {
        txTbody.innerHTML = txns.slice(0, 40).map(tx => {
            const isSender = String(tx.sender_id) === String(p.id);
            const flow = isSender ?
                '<span class="badge badge-medium">Sent</span>' :
                '<span class="badge badge-low">Received</span>';
            const counterparty = isSender ? (tx.receiver_name || tx.receiver_id) : (tx.sender_name || tx.sender_id);
            const isSusp = tx.is_suspicious in [true, "True", "true", 1, "1"];

            return `
                <tr>
                    <td style="font-family:'JetBrains Mono',monospace">${tx.txn_id || '—'}</td>
                    <td>${tx.date || ''} ${tx.time || ''}</td>
                    <td><strong>${tx.transaction_type || '—'}</strong></td>
                    <td>${flow}</td>
                    <td style="font-weight:600;color:var(--accent-emerald)">₹${formatAmount(tx.amount)}</td>
                    <td>${counterparty || '—'}</td>
                    <td>${tx.bank || '—'} <small style="color:var(--text-muted)">(${tx.sender_account || tx.receiver_account || '—'})</small></td>
                    <td><span class="badge badge-${isSusp ? 'critical' : 'low'}">${isSusp ? 'SUSPICIOUS' : 'Normal'}</span></td>
                    <td style="font-size:0.75rem;color:var(--text-secondary)">${tx.remarks || '—'}</td>
                </tr>
            `;
        }).join('');
    }

    // ── 5. Court Convictions ──
    const history = data.criminal_history || [];
    document.getElementById('d-hist-count').textContent = history.length;
    const histTbody = document.getElementById('d-history-table-body');
    if (history.length === 0) {
        histTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:16px">No prior judicial convictions on record.</td></tr>';
    } else {
        histTbody.innerHTML = history.map(h => {
            const statusClass = h.status === 'CONVICTED' ? 'critical' : h.status === 'PENDING' ? 'medium' : 'low';
            return `
                <tr>
                    <td style="font-family:'JetBrains Mono',monospace">${h.record_id || '—'}</td>
                    <td>${h.case_id || '—'}</td>
                    <td><strong>${h.crime_type || '—'}</strong></td>
                    <td>${h.date || '—'}</td>
                    <td>${h.court || '—'}</td>
                    <td><span class="badge badge-${statusClass}">${h.status || '—'}</span></td>
                    <td>${h.sentence || 'None'}</td>
                </tr>
            `;
        }).join('');
    }

    // ── 6. Syndicate & Associates ──
    const associates = data.resolved_associates || [];
    document.getElementById('d-assoc-count').textContent = associates.length;
    const assocGrid = document.getElementById('d-associates-grid');
    if (associates.length === 0) {
        assocGrid.innerHTML = '<div class="dossier-empty-sub">No known syndicate accomplices or criminal associates recorded.</div>';
    } else {
        assocGrid.innerHTML = associates.map(a => {
            const aRiskClass = (a.risk_level || 'low').toLowerCase();
            return `
                <div class="dossier-assoc-card" onclick="openPersonDossier('${a.id}')">
                    <div class="assoc-card-top">
                        <div class="assoc-avatar ${aRiskClass}">${getInitials(a.name)}</div>
                        <span class="badge badge-${aRiskClass}">${a.risk_level || 'LOW'}</span>
                    </div>
                    <div class="assoc-name">${a.name || a.id}</div>
                    <div class="assoc-meta" style="font-family:'JetBrains Mono',monospace">${a.id}</div>
                    <div class="assoc-org">${a.organization || 'Independent Associate'}</div>
                    <button class="btn-sm" style="margin-top:8px;width:100%;background:rgba(2,132,199,0.15);color:var(--accent-blue);border:1px solid rgba(2,132,199,0.3);border-radius:4px;cursor:pointer">
                        🗂️ View Dossier
                    </button>
                </div>
            `;
        }).join('');
    }
}

async function triggerDossierPDFDownload() {
    if (!currentDossierPersonId) return;
    const btn = document.getElementById('dossier-download-btn');
    const originalText = btn ? btn.innerHTML : '';

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px"></span><span>Generating PDF Dossier...</span>';
    }

    try {
        const personName = currentDossierData?.entity?.name || currentDossierPersonId;
        downloadDossierDirect(currentDossierPersonId, personName);
    } catch (e) {
        console.error('PDF download error:', e);
        alert('Failed to initiate PDF download. Please try again.');
    } finally {
        setTimeout(() => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }, 1200);
    }
}

