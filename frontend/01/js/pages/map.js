/**
 * Klar - Map Page
 * Placeholder - Full implementation in Phase 6
 */

(function() {
  let map = null;

  function render(container) {
    container.innerHTML = `
      <div class="h-full flex flex-col">
        <div id="map-container" class="flex-1 relative">
          <div class="absolute inset-0 flex items-center justify-center bg-secondary-50 dark:bg-secondary-600">
            <div class="text-center">
              <div class="spinner mx-auto mb-4"></div>
              <p class="text-sm text-secondary/60 dark:text-white/60">Loading map...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    // Initialize map after a brief delay to ensure container is rendered
    setTimeout(() => initMap(container), 100);
  }

  async function initMap(container) {
    const mapContainer = $('#map-container', container);
    if (!mapContainer) return;

    // Clear loading state
    mapContainer.innerHTML = '<div id="map" class="h-full w-full"></div>';

    // Initialize Leaflet map
    map = L.map('map').setView([30, 0], 2);

    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map);

    // Load cities data and add markers
    try {
      const response = await fetch('/assets/cities.json');
      const cities = await response.json();
      addMarkers(cities);
    } catch (error) {
      console.error('Failed to load cities:', error);
      Toast.error('Failed to load map data');
    }
  }

  function addMarkers(cities) {
    const records = State.get('records');

    // Group records by city
    const byCity = {};
    records.forEach(r => {
      const city = r['fund.city'];
      if (city && cities[city]) {
        if (!byCity[city]) {
          byCity[city] = [];
        }
        byCity[city].push(r);
      }
    });

    // Create custom icon
    const markerIcon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        width: 24px;
        height: 24px;
        background: #DEC26F;
        border: 2px solid #15213B;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      "></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    // Add markers
    const markers = [];
    Object.entries(byCity).forEach(([cityCode, cityRecords]) => {
      const cityData = cities[cityCode];
      if (!cityData) return;

      const marker = L.marker([cityData.lat, cityData.lng], { icon: markerIcon })
        .addTo(map);

      // Create popup content
      const fundNames = cityRecords
        .slice(0, 3)
        .map(r => r['fund.title'])
        .filter(Boolean);

      const popupContent = `
        <div style="min-width: 150px;">
          <strong>${cityData.name}</strong>
          <p style="color: #666; font-size: 12px; margin: 4px 0;">${cityRecords.length} fund${cityRecords.length > 1 ? 's' : ''}</p>
          <ul style="margin: 0; padding-left: 16px; font-size: 12px;">
            ${fundNames.map(name => `<li>${escapeHtml(name)}</li>`).join('')}
            ${cityRecords.length > 3 ? `<li style="color: #666;">+${cityRecords.length - 3} more</li>` : ''}
          </ul>
        </div>
      `;

      marker.bindPopup(popupContent);
      markers.push(marker);
    });

    // Fit bounds to markers if any exist
    if (markers.length > 0) {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.1));
    }
  }

  // Cleanup on page change
  State.subscribe((path) => {
    if (path === 'activeTab' && State.get('activeTab') !== 'map' && map) {
      map.remove();
      map = null;
    }
  });

  // Register page
  Router.registerPage('map', render);
})();
