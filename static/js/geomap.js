/**
 * CrimeNet AI — Geospatial Crime Map Module
 * Interactive choropleth map of India with CSV upload and crime analysis
 */

/* global L */

const GeoMap = (() => {
    // ── State ────────────────────────────────────────────────────
    let map = null;
    let geojsonLayer = null;
    let markersLayer = null;
    let heatLayer = null;
    let indiaGeoJSON = null;
    let currentData = null;
    let currentSource = 'existing'; // 'existing' or 'uploaded'
    let uploadedResult = null;
    let searchTimeout = null;
    let initialized = false;

    // MapmyIndia (Mappls) SDK State
    let mapplsApiKey = '';
    let mapplsLoaded = false;
    let mapplsSearchInstance = null;

    const COLOR_SCALE = [
        '#f7f7f7', // 0 - no data (neutral grey)
        '#fee5d9', // 1 - very low
        '#fcbba1', // 2 - low
        '#fc9272', // 3 - medium-low
        '#fb6a4a', // 4 - medium
        '#ef3b2c', // 5 - medium-high
        '#cb181d', // 6 - high
        '#a50f15', // 7 - very high
        '#67000d', // 8 - extreme
    ];

    // ── Initialize ───────────────────────────────────────────────
    async function init() {
        if (initialized && map) {
            map.invalidateSize();
            return;
        }

        const container = document.getElementById('geomap-container');
        if (!container) return;

        container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading Crime Geospatial Map...</p></div>';

        try {
            // Load GeoJSON
            const geoRes = await fetch('/data/india_states.geojson');
            indiaGeoJSON = await geoRes.json();

            // Init map
            container.innerHTML = '';
            initMap(container);

            // Load existing data
            await loadExistingData();

            // Setup event listeners
            setupEventListeners();

            // Initialize MapmyIndia SDK
            await initMapplsSDK();

            initialized = true;
        } catch (e) {
            container.innerHTML = '<div class="loading"><p style="color:var(--accent-red)">❌ Failed to load map data</p></div>';
            console.error('GeoMap init error:', e);
        }
    }

    function initMap(container) {
        map = L.map(container, {
            center: [22.5, 82],
            zoom: 5,
            minZoom: 4,
            maxZoom: 12,
            zoomControl: true,
            scrollWheelZoom: true,
        });

        // Tile layer — use CartoDB dark/light based on theme
        const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
        const tileUrl = isDark
            ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
            : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

        L.tileLayer(tileUrl, {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19,
        }).addTo(map);

        // Init layer groups
        markersLayer = L.layerGroup().addTo(map);
    }

    // ── Data Loading ─────────────────────────────────────────────
    async function loadExistingData(crimeType, year, location) {
        showMapLoading('Loading existing crime data...');
        try {
            let url = '/api/geo/existing?';
            if (crimeType && crimeType !== 'All') url += `crime_type=${encodeURIComponent(crimeType)}&`;
            if (year && year !== 'All') url += `year=${encodeURIComponent(year)}&`;
            if (location) url += `location=${encodeURIComponent(location)}&`;

            const res = await fetch(url);
            currentData = await res.json();
            currentSource = 'existing';

            updateMap(currentData);
            updateStats(currentData.stats);
            updateFilters(currentData.filters);
            updateDataSourceIndicator();
        } catch (e) {
            console.error('Failed to load existing data:', e);
        } finally {
            hideMapLoading();
        }
    }

    async function loadUploadedFiltered(crimeType, year, location) {
        showMapLoading('Filtering uploaded data...');
        try {
            let url = '/api/geo/uploaded/filter?';
            if (crimeType && crimeType !== 'All') url += `crime_type=${encodeURIComponent(crimeType)}&`;
            if (year && year !== 'All') url += `year=${encodeURIComponent(year)}&`;
            if (location) url += `location=${encodeURIComponent(location)}&`;

            const res = await fetch(url);
            const data = await res.json();
            if (data.status === 'error') {
                console.error(data.message);
                return;
            }
            currentData = data;
            updateMap(data);
            updateStats(data.stats);
        } catch (e) {
            console.error('Failed to filter uploaded data:', e);
        } finally {
            hideMapLoading();
        }
    }

    // ── Map Rendering ────────────────────────────────────────────
    function updateMap(data) {
        if (!map || !indiaGeoJSON) return;

        // Clear existing layers
        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
            geojsonLayer = null;
        }
        markersLayer.clearLayers();
        if (heatLayer) {
            map.removeLayer(heatLayer);
            heatLayer = null;
        }

        const stateData = data.state_data || {};
        const geodata = data.geodata || [];

        // Find max crime count for color scaling
        let maxCount = 1;
        for (const sd of Object.values(stateData)) {
            if (sd.crime_count > maxCount) maxCount = sd.crime_count;
        }

        // Render choropleth
        geojsonLayer = L.geoJSON(indiaGeoJSON, {
            style: (feature) => {
                const stateName = feature.properties.ST_NM;
                const sd = stateData[stateName];
                const count = sd ? sd.crime_count : 0;
                return {
                    fillColor: getColor(count, maxCount),
                    weight: 1.5,
                    opacity: 1,
                    color: getStrokColor(),
                    fillOpacity: 0.75,
                };
            },
            onEachFeature: (feature, layer) => {
                const stateName = feature.properties.ST_NM;
                const sd = stateData[stateName];
                const count = sd ? sd.crime_count : 0;

                // Tooltip
                let tooltipContent = `<div class="geo-tooltip">
                    <div class="geo-tooltip-title">${sanitize(stateName)}</div>
                    <div class="geo-tooltip-value">Total Crimes: ${count.toLocaleString()}</div>`;

                if (sd && sd.crime_types) {
                    const topCrimes = Object.entries(sd.crime_types)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3);
                    if (topCrimes.length > 0) {
                        tooltipContent += '<div class="geo-tooltip-breakdown">';
                        topCrimes.forEach(([type, cnt]) => {
                            tooltipContent += `<span>${sanitize(type)}: ${cnt}</span>`;
                        });
                        tooltipContent += '</div>';
                    }
                }
                tooltipContent += '</div>';

                layer.bindTooltip(tooltipContent, {
                    sticky: true,
                    className: 'geo-tooltip-container',
                });

                // Click — zoom in
                layer.on('click', () => {
                    map.fitBounds(layer.getBounds(), { padding: [30, 30], maxZoom: 8 });
                });

                // Hover highlight
                layer.on('mouseover', () => {
                    layer.setStyle({ weight: 3, fillOpacity: 0.9 });
                    layer.bringToFront();
                });
                layer.on('mouseout', () => {
                    geojsonLayer.resetStyle(layer);
                });
            },
        }).addTo(map);

        // Add city/location markers
        if (geodata.length > 0 && geodata.length <= 1000) {
            geodata.forEach((point) => {
                if (!point.lat || !point.lng || point.lat === 0) return;

                const radius = Math.max(5, Math.min(25, Math.sqrt(point.crime_count) * 2));
                const marker = L.circleMarker([point.lat, point.lng], {
                    radius: radius,
                    fillColor: getColor(point.crime_count, maxCount),
                    color: '#fff',
                    weight: 1.5,
                    opacity: 0.9,
                    fillOpacity: 0.8,
                });

                let popupContent = `<div class="geo-tooltip">
                    <div class="geo-tooltip-title">${sanitize(point.location || point.city || '')}</div>
                    <div class="geo-tooltip-subtitle">${sanitize(point.state || '')}</div>
                    <div class="geo-tooltip-value">Crimes: ${point.crime_count.toLocaleString()}</div>`;

                if (point.crime_types && Object.keys(point.crime_types).length > 0) {
                    popupContent += '<div class="geo-tooltip-breakdown">';
                    Object.entries(point.crime_types)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 5)
                        .forEach(([type, cnt]) => {
                            popupContent += `<span>${sanitize(type)}: ${cnt}</span>`;
                        });
                    popupContent += '</div>';
                }
                popupContent += '</div>';

                marker.bindPopup(popupContent, { className: 'geo-popup-container' });
                marker.bindTooltip(`${sanitize(point.location || '')}: ${point.crime_count}`, {
                    className: 'geo-tooltip-container',
                });
                markersLayer.addLayer(marker);
            });
        } else if (geodata.length > 1000) {
            // Too many points — use heat-like approach with larger circles
            const heatPoints = [];
            geodata.forEach((point) => {
                if (point.lat && point.lng && point.lat !== 0) {
                    heatPoints.push([point.lat, point.lng, point.crime_count]);
                }
            });
            // Render as aggregated circle markers
            const gridSize = 0.5; // degrees
            const grid = {};
            heatPoints.forEach(([lat, lng, count]) => {
                const key = `${Math.round(lat / gridSize) * gridSize}_${Math.round(lng / gridSize) * gridSize}`;
                if (!grid[key]) grid[key] = { lat: 0, lng: 0, count: 0, n: 0 };
                grid[key].lat += lat;
                grid[key].lng += lng;
                grid[key].count += count;
                grid[key].n += 1;
            });

            let gridMax = 1;
            Object.values(grid).forEach(g => { if (g.count > gridMax) gridMax = g.count; });

            Object.values(grid).forEach((g) => {
                const avgLat = g.lat / g.n;
                const avgLng = g.lng / g.n;
                const radius = Math.max(8, Math.min(35, Math.sqrt(g.count / gridMax) * 35));
                const marker = L.circleMarker([avgLat, avgLng], {
                    radius: radius,
                    fillColor: getColor(g.count, gridMax),
                    color: 'rgba(255,255,255,0.6)',
                    weight: 1,
                    fillOpacity: 0.7,
                });
                marker.bindTooltip(`Crimes: ${g.count.toLocaleString()} (${g.n} locations)`, {
                    className: 'geo-tooltip-container',
                });
                markersLayer.addLayer(marker);
            });
        }

        // Update legend
        updateLegend(maxCount);
    }

    function getColor(count, maxCount) {
        if (count === 0) return COLOR_SCALE[0];
        const ratio = count / maxCount;
        if (ratio < 0.05) return COLOR_SCALE[1];
        if (ratio < 0.1) return COLOR_SCALE[2];
        if (ratio < 0.2) return COLOR_SCALE[3];
        if (ratio < 0.35) return COLOR_SCALE[4];
        if (ratio < 0.5) return COLOR_SCALE[5];
        if (ratio < 0.7) return COLOR_SCALE[6];
        if (ratio < 0.9) return COLOR_SCALE[7];
        return COLOR_SCALE[8];
    }

    function getStrokColor() {
        const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
        return isDark ? 'rgba(148, 163, 184, 0.4)' : 'rgba(71, 85, 105, 0.4)';
    }

    // ── Statistics ────────────────────────────────────────────────
    function updateStats(stats) {
        if (!stats) return;
        const el = (id, val) => {
            const e = document.getElementById(id);
            if (e) e.textContent = val;
        };
        el('geo-stat-total', (stats.total_crimes || 0).toLocaleString());
        el('geo-stat-locations', stats.states_affected || 0);
        el('geo-stat-cities', stats.cities_districts || 0);
        el('geo-stat-common', stats.most_common_crime || '—');
        el('geo-stat-highest', stats.highest_crime_location || '—');
    }

    function updateFilters(filters) {
        if (!filters) return;

        // Crime type dropdown
        const crimeSelect = document.getElementById('geo-filter-crime');
        if (crimeSelect && filters.crime_types) {
            const currentVal = crimeSelect.value;
            crimeSelect.innerHTML = '<option value="All">All Crimes</option>';
            filters.crime_types.forEach((ct) => {
                const opt = document.createElement('option');
                opt.value = ct;
                opt.textContent = ct;
                crimeSelect.appendChild(opt);
            });
            if (currentVal) crimeSelect.value = currentVal;
        }

        // Year dropdown
        const yearSelect = document.getElementById('geo-filter-year');
        const yearContainer = document.getElementById('geo-year-filter-group');
        if (yearSelect && filters.years && filters.years.length > 0) {
            if (yearContainer) yearContainer.style.display = 'flex';
            const currentVal = yearSelect.value;
            yearSelect.innerHTML = '<option value="All">All Years</option>';
            filters.years.forEach((y) => {
                const opt = document.createElement('option');
                opt.value = y;
                opt.textContent = y;
                yearSelect.appendChild(opt);
            });
            if (currentVal) yearSelect.value = currentVal;
        } else {
            if (yearContainer) yearContainer.style.display = 'none';
        }
    }

    function updateLegend(maxCount) {
        const legendBar = document.getElementById('geo-legend-bar');
        if (!legendBar) return;

        const steps = [0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0];
        let gradient = 'linear-gradient(to right';
        steps.forEach((s, i) => {
            gradient += `, ${COLOR_SCALE[i]} ${(s * 100).toFixed(0)}%`;
        });
        gradient += ')';
        legendBar.style.background = gradient;

        const minEl = document.getElementById('geo-legend-min');
        const maxEl = document.getElementById('geo-legend-max');
        if (minEl) minEl.textContent = '0';
        if (maxEl) maxEl.textContent = maxCount.toLocaleString();
    }

    function updateDataSourceIndicator() {
        const existingRadio = document.getElementById('geo-source-existing');
        const uploadedRadio = document.getElementById('geo-source-uploaded');
        if (existingRadio) existingRadio.checked = currentSource === 'existing';
        if (uploadedRadio) uploadedRadio.checked = currentSource === 'uploaded';
    }

    // ── Search ───────────────────────────────────────────────────
    function setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('geo-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const q = e.target.value.trim();
                if (q.length >= 2) {
                    searchTimeout = setTimeout(() => searchLocations(q), 300);
                } else {
                    hideSearchResults();
                    if (q.length === 0) {
                        // Reset — reload current data without location filter
                        applyFilters();
                    }
                }
            });

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const q = searchInput.value.trim();
                    if (q) {
                        hideSearchResults();
                        applyFilters(q);
                    }
                }
            });
        }

        // Search button
        const searchBtn = document.getElementById('geo-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const q = document.getElementById('geo-search-input')?.value?.trim();
                if (q) {
                    hideSearchResults();
                    applyFilters(q);
                }
            });
        }

        // Crime type filter
        const crimeFilter = document.getElementById('geo-filter-crime');
        if (crimeFilter) {
            crimeFilter.addEventListener('change', () => applyFilters());
        }

        // Year filter
        const yearFilter = document.getElementById('geo-filter-year');
        if (yearFilter) {
            yearFilter.addEventListener('change', () => applyFilters());
        }

        // CSV Upload
        const uploadBtn = document.getElementById('geo-upload-btn');
        const fileInput = document.getElementById('geo-csv-input');
        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', handleFileUpload);
        }

        // Data source toggle
        const srcExisting = document.getElementById('geo-source-existing');
        const srcUploaded = document.getElementById('geo-source-uploaded');
        if (srcExisting) {
            srcExisting.addEventListener('change', () => {
                if (srcExisting.checked) {
                    currentSource = 'existing';
                    applyFilters();
                }
            });
        }
        if (srcUploaded) {
            srcUploaded.addEventListener('change', () => {
                if (srcUploaded.checked && uploadedResult) {
                    currentSource = 'uploaded';
                    currentData = uploadedResult;
                    updateMap(uploadedResult);
                    updateStats(uploadedResult.stats);
                    updateFilters(uploadedResult.filters);
                }
            });
        }

        // Use Dataset button (in preview modal)
        const useDatasetBtn = document.getElementById('geo-use-dataset-btn');
        if (useDatasetBtn) {
            useDatasetBtn.addEventListener('click', () => {
                if (uploadedResult) {
                    currentSource = 'uploaded';
                    currentData = uploadedResult;
                    updateMap(uploadedResult);
                    updateStats(uploadedResult.stats);
                    updateFilters(uploadedResult.filters);
                    updateDataSourceIndicator();
                    closePreviewModal();
                }
            });
        }

        // Close preview modal
        const closePreviewBtn = document.getElementById('geo-preview-close');
        if (closePreviewBtn) {
            closePreviewBtn.addEventListener('click', closePreviewModal);
        }
        const previewOverlay = document.getElementById('geo-preview-modal');
        if (previewOverlay) {
            previewOverlay.addEventListener('click', (e) => {
                if (e.target === previewOverlay) closePreviewModal();
            });
        }

        // MapmyIndia (Mappls) Modal listeners
        const mapplsBtn = document.getElementById('geo-mappls-btn');
        if (mapplsBtn) {
            mapplsBtn.addEventListener('click', openMapplsModal);
        }
        const closeMapplsBtn = document.getElementById('geo-mappls-close');
        if (closeMapplsBtn) {
            closeMapplsBtn.addEventListener('click', closeMapplsModal);
        }
        const mapplsOverlay = document.getElementById('geo-mappls-modal');
        if (mapplsOverlay) {
            mapplsOverlay.addEventListener('click', (e) => {
                if (e.target === mapplsOverlay) closeMapplsModal();
            });
        }
        const saveMapplsBtn = document.getElementById('geo-mappls-save-btn');
        if (saveMapplsBtn) {
            saveMapplsBtn.addEventListener('click', () => {
                const keyInput = document.getElementById('geo-mappls-key-input');
                const key = keyInput ? keyInput.value.trim() : '';
                saveMapplsKey(key);
            });
        }
        const clearMapplsBtn = document.getElementById('geo-mappls-clear-btn');
        if (clearMapplsBtn) {
            clearMapplsBtn.addEventListener('click', clearMapplsKey);
        }
    }

    async function searchLocations(query) {
        try {
            const res = await fetch(`/api/geo/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            showSearchResults(data.results || []);
        } catch (e) {
            console.error('Search error:', e);
        }
    }

    function showSearchResults(results) {
        const dropdown = document.getElementById('geo-search-results');
        if (!dropdown) return;

        if (results.length === 0) {
            dropdown.innerHTML = '<div class="geo-search-item geo-search-empty">No locations found</div>';
            dropdown.classList.add('active');
            return;
        }

        dropdown.innerHTML = results.map((r) => `
            <div class="geo-search-item" data-lat="${r.lat}" data-lng="${r.lng}" data-name="${sanitize(r.name)}">
                <span class="geo-search-type">${r.type === 'State' ? '🏛️' : '🏙️'}</span>
                <span class="geo-search-name">${sanitize(r.name)}</span>
                <span class="geo-search-badge">${sanitize(r.type)}</span>
            </div>
        `).join('');

        dropdown.classList.add('active');

        // Click handlers for results
        dropdown.querySelectorAll('.geo-search-item[data-lat]').forEach((item) => {
            item.addEventListener('click', () => {
                const lat = parseFloat(item.dataset.lat);
                const lng = parseFloat(item.dataset.lng);
                const name = item.dataset.name;

                document.getElementById('geo-search-input').value = name;
                hideSearchResults();

                // Fly to location and filter
                if (map && lat && lng) {
                    map.flyTo([lat, lng], 7, { duration: 1.2 });
                }
                applyFilters(name);
            });
        });
    }

    function hideSearchResults() {
        const dropdown = document.getElementById('geo-search-results');
        if (dropdown) dropdown.classList.remove('active');
    }

    // Close search results on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.geo-search-wrapper')) {
            hideSearchResults();
        }
    });

    function applyFilters(locationOverride) {
        const crimeType = document.getElementById('geo-filter-crime')?.value || 'All';
        const year = document.getElementById('geo-filter-year')?.value || 'All';
        const location = locationOverride !== undefined
            ? locationOverride
            : document.getElementById('geo-search-input')?.value?.trim() || '';

        if (currentSource === 'existing') {
            loadExistingData(crimeType, year, location);
        } else if (currentSource === 'uploaded') {
            loadUploadedFiltered(crimeType, year, location);
        }
    }

    // ── CSV Upload ───────────────────────────────────────────────
    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Client-side validation
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showUploadError('Invalid file type. Please upload a .csv file.');
            return;
        }
        if (file.size > 50 * 1024 * 1024) {
            showUploadError('File too large. Maximum allowed: 50 MB.');
            return;
        }

        showMapLoading(`Processing ${sanitize(file.name)}...`);
        const uploadBtn = document.getElementById('geo-upload-btn');
        if (uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="geo-upload-icon">⏳</span> Processing...';
        }

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/geo/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await res.json();

            if (result.status === 'error') {
                showUploadError(result.message);
                return;
            }

            uploadedResult = result;
            showPreviewModal(result);

        } catch (err) {
            showUploadError(`Upload failed: ${err.message}`);
        } finally {
            hideMapLoading();
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<span class="geo-upload-icon">📁</span> Upload Crime CSV';
            }
            // Reset file input
            e.target.value = '';
        }
    }

    function showPreviewModal(result) {
        const modal = document.getElementById('geo-preview-modal');
        if (!modal) return;

        const preview = result.preview;
        const stats = result.stats;

        // File info
        document.getElementById('geo-preview-filename').textContent = result.filename || 'Unknown';
        document.getElementById('geo-preview-rows').textContent = (preview.rows || 0).toLocaleString();
        document.getElementById('geo-preview-cols').textContent = preview.columns || 0;

        // Detected columns
        const detectedEl = document.getElementById('geo-preview-detected');
        if (detectedEl) {
            const detected = preview.detected_columns || {};
            detectedEl.innerHTML = Object.entries(detected).map(([role, col]) => `
                <div class="geo-detected-item">
                    <span class="geo-detected-check">✓</span>
                    <span class="geo-detected-role">${sanitize(role.replace('_', ' '))}</span>
                    <span class="geo-detected-col">${sanitize(col)}</span>
                </div>
            `).join('');
        }

        // Mapped / Unmatched counts
        document.getElementById('geo-preview-mapped').textContent =
            (result.mapped_count || 0).toLocaleString();
        document.getElementById('geo-preview-unmatched').textContent =
            (result.unmatched_count || 0).toLocaleString();

        // Warnings
        const warningsEl = document.getElementById('geo-preview-warnings');
        if (warningsEl) {
            if (result.warnings && result.warnings.length > 0) {
                warningsEl.innerHTML = result.warnings.map(w =>
                    `<div class="geo-warning-item">⚠️ ${sanitize(w)}</div>`
                ).join('');
                warningsEl.style.display = 'block';
            } else {
                warningsEl.style.display = 'none';
            }
        }

        // Unmatched locations
        const unmatchedEl = document.getElementById('geo-preview-unmatched-list');
        if (unmatchedEl) {
            if (result.unmatched && result.unmatched.length > 0) {
                unmatchedEl.innerHTML = `
                    <div class="geo-unmatched-header" onclick="this.parentElement.classList.toggle('expanded')">
                        📋 Unmatched Locations (${result.unmatched_count}) — Click to expand
                    </div>
                    <div class="geo-unmatched-body">
                        ${result.unmatched.slice(0, 50).map(u => `
                            <div class="geo-unmatched-item">
                                <span>${sanitize(u.location || '—')}</span>
                                <span class="geo-unmatched-reason">${sanitize(u.reason || '')}</span>
                            </div>
                        `).join('')}
                        ${result.unmatched_count > 50 ? `<div class="geo-unmatched-item">... and ${result.unmatched_count - 50} more</div>` : ''}
                    </div>
                `;
                unmatchedEl.style.display = 'block';
            } else {
                unmatchedEl.style.display = 'none';
            }
        }

        // Preview table
        const tableEl = document.getElementById('geo-preview-table');
        if (tableEl && preview.first_rows && preview.first_rows.length > 0) {
            const cols = preview.column_names || Object.keys(preview.first_rows[0]);
            tableEl.innerHTML = `
                <table class="entity-table">
                    <thead><tr>${cols.map(c => `<th>${sanitize(c)}</th>`).join('')}</tr></thead>
                    <tbody>
                        ${preview.first_rows.map(row => `
                            <tr>${cols.map(c => `<td>${sanitize(String(row[c] || ''))}</td>`).join('')}</tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        // Enable uploaded radio
        const uploadedRadio = document.getElementById('geo-source-uploaded');
        if (uploadedRadio) uploadedRadio.disabled = false;

        modal.classList.add('active');
    }

    function closePreviewModal() {
        const modal = document.getElementById('geo-preview-modal');
        if (modal) modal.classList.remove('active');
    }

    function showUploadError(message) {
        const errorEl = document.getElementById('geo-upload-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => { errorEl.style.display = 'none'; }, 8000);
        }
    }

    // ── Loading ──────────────────────────────────────────────────
    function showMapLoading(message) {
        const overlay = document.getElementById('geo-loading-overlay');
        if (overlay) {
            overlay.querySelector('.geo-loading-text').textContent = message || 'Loading...';
            overlay.classList.add('active');
        }
    }

    function hideMapLoading() {
        const overlay = document.getElementById('geo-loading-overlay');
        if (overlay) overlay.classList.remove('active');
    }

    // ── MapmyIndia (Mappls) SDK Integration ────────────────────
    async function initMapplsSDK() {
        let key = localStorage.getItem('mappls_api_key') || '';
        if (!key) {
            try {
                const res = await fetch('/api/geo/config');
                const cfg = await res.json();
                if (cfg && cfg.mappls_api_key) {
                    key = cfg.mappls_api_key;
                }
            } catch (e) {
                // Ignore backend config fetch errors
            }
        }
        if (!key) {
            key = '17bb1b3a5395fece49cb440e65590f22';
        }
        localStorage.setItem('mappls_api_key', key);

        mapplsApiKey = key;
        updateMapplsUI(key, true);

        if (key) {
            loadMapplsScript(key);
        }
    }

    function loadMapplsScript(key) {
        if (!key) return;

        // Clean up any previously injected script
        const existingScript = document.getElementById('mappls-sdk-script');
        if (existingScript) existingScript.remove();

        const script = document.createElement('script');
        script.id = 'mappls-sdk-script';
        // MapmyIndia Places & Directions Web SDK plugin URL
        script.src = `https://apis.mapmyindia.com/advancedmaps/api/${encodeURIComponent(key)}/map_sdk_plugins`;
        script.async = true;

        script.onload = () => {
            mapplsLoaded = true;
            updateMapplsUI(key, true);
            setupMapplsSearchPlugin();
            console.log('📍 MapmyIndia Places & Directions Web SDK loaded successfully.');
        };

        script.onerror = () => {
            console.warn('MapmyIndia SDK failed to authenticate or load. Falling back to built-in geocoding.');
            updateMapplsUI(key, false, 'Invalid or unauthorized API key');
        };

        document.head.appendChild(script);
    }

    function setupMapplsSearchPlugin() {
        const input = document.getElementById('geo-search-input');
        if (!input) return;

        if (window.MapmyIndia && typeof MapmyIndia.search === 'function') {
            try {
                // Initialize MapmyIndia Places Search plugin from the Places & Directions SDK
                const placeOptions = {
                    location: [22.5, 82.0],
                    bridge: true,
                    hyperLocal: false
                };
                mapplsSearchInstance = new MapmyIndia.search(input, placeOptions, function(data) {
                    if (data) {
                        handleMapplsPlaceSelect(data);
                    }
                });
                console.log('✅ MapmyIndia Place Search plugin activated on search input.');
            } catch (err) {
                console.warn('MapmyIndia Search plugin initialization notice:', err);
            }
        }
    }

    function handleMapplsPlaceSelect(data) {
        if (!data) return;
        const lat = data.latitude || (data.location && data.location.latitude) || data.lat;
        const lng = data.longitude || (data.location && data.location.longitude) || data.lng;
        const name = data.placeName || data.placeAddress || data.formatted_address || data.name || '';

        if (name) {
            const input = document.getElementById('geo-search-input');
            if (input) input.value = name;
        }

        if (lat && lng && map) {
            map.flyTo([parseFloat(lat), parseFloat(lng)], 8, { duration: 1.2 });
        }

        if (name) {
            applyFilters(name);
        }
    }

    function saveMapplsKey(key) {
        mapplsApiKey = key;
        if (key) {
            localStorage.setItem('mappls_api_key', key);
            updateMapplsUI(key);
            loadMapplsScript(key);
            fetch('/api/geo/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mappls_api_key: key })
            }).catch(() => {});
        } else {
            clearMapplsKey();
        }
        closeMapplsModal();
    }

    function clearMapplsKey() {
        mapplsApiKey = '';
        mapplsLoaded = false;
        mapplsSearchInstance = null;
        localStorage.removeItem('mappls_api_key');
        const keyInput = document.getElementById('geo-mappls-key-input');
        if (keyInput) keyInput.value = '';
        updateMapplsUI('');

        const script = document.getElementById('mappls-sdk-script');
        if (script) script.remove();

        fetch('/api/geo/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mappls_api_key: '' })
        }).catch(() => {});
    }

    function updateMapplsUI(key, isConnected, errorMsg) {
        const badge = document.getElementById('geo-mappls-badge');
        const statusDot = document.getElementById('geo-status-dot');
        const statusText = document.getElementById('geo-status-text');
        const keyInput = document.getElementById('geo-mappls-key-input');

        if (keyInput && key && !keyInput.value) {
            keyInput.value = key;
        }

        if (key) {
            if (isConnected) {
                if (badge) {
                    badge.textContent = 'Active';
                    badge.classList.add('connected');
                }
                if (statusDot) statusDot.classList.add('connected');
                if (statusText) statusText.textContent = `Status: Connected to MapmyIndia SDK (${key.substring(0, 8)}...)`;
            } else if (errorMsg) {
                if (badge) {
                    badge.textContent = 'Auth Error';
                    badge.classList.remove('connected');
                }
                if (statusDot) statusDot.classList.remove('connected');
                if (statusText) statusText.textContent = `Status: ${errorMsg}`;
            } else {
                if (badge) {
                    badge.textContent = 'Connecting';
                    badge.classList.remove('connected');
                }
                if (statusDot) statusDot.classList.remove('connected');
                if (statusText) statusText.textContent = 'Status: Connecting to MapmyIndia SDK...';
            }
        } else {
            if (badge) {
                badge.textContent = 'Configure Key';
                badge.classList.remove('connected');
            }
            if (statusDot) statusDot.classList.remove('connected');
            if (statusText) statusText.textContent = 'Status: Fallback mode active (No MapmyIndia key configured)';
        }
    }

    function openMapplsModal() {
        const modal = document.getElementById('geo-mappls-modal');
        if (modal) {
            const keyInput = document.getElementById('geo-mappls-key-input');
            if (keyInput) keyInput.value = mapplsApiKey || '';
            modal.classList.add('active');
        }
    }

    function closeMapplsModal() {
        const modal = document.getElementById('geo-mappls-modal');
        if (modal) modal.classList.remove('active');
    }

    // ── Utilities ────────────────────────────────────────────────
    function sanitize(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ── Public API ───────────────────────────────────────────────
    return { init };
})();

// Global function for tab loading
function loadGeoMap() {
    GeoMap.init();
}
