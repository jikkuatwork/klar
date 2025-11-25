/**
 * Klar - Charts Page
 * Placeholder - Full implementation in Phase 7
 */

(function() {
  let charts = [];

  function render(container) {
    container.innerHTML = `
      <div class="p-4 sm:p-6">
        <h1 class="text-2xl font-semibold mb-6">Charts</h1>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Fund Types Chart -->
          <div class="card">
            <h3 class="font-medium mb-4">By Fund Type</h3>
            <div class="h-64">
              <canvas id="chart-fund-types"></canvas>
            </div>
          </div>

          <!-- Countries Chart -->
          <div class="card">
            <h3 class="font-medium mb-4">By Country (Top 10)</h3>
            <div class="h-64">
              <canvas id="chart-countries"></canvas>
            </div>
          </div>

          <!-- AUM Distribution -->
          <div class="card">
            <h3 class="font-medium mb-4">AUM Distribution</h3>
            <div class="h-64">
              <canvas id="chart-aum"></canvas>
            </div>
          </div>

          <!-- Sectors Chart -->
          <div class="card">
            <h3 class="font-medium mb-4">Top Sectors</h3>
            <div class="h-64">
              <canvas id="chart-sectors"></canvas>
            </div>
          </div>
        </div>
      </div>
    `;

    // Render charts after DOM is ready
    setTimeout(() => renderCharts(), 100);
  }

  function renderCharts() {
    const records = State.get('records');

    // Destroy existing charts
    charts.forEach(chart => chart.destroy());
    charts = [];

    // Chart.js default config
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.color = document.documentElement.classList.contains('dark') ? '#ffffff99' : '#15213B99';

    // Fund Types Chart
    const fundTypes = groupBy(records, 'fund.type');
    const fundTypeLabels = Object.keys(fundTypes).filter(Boolean).sort((a, b) => fundTypes[b].length - fundTypes[a].length);
    const fundTypeData = fundTypeLabels.map(t => fundTypes[t].length);

    charts.push(new Chart($('#chart-fund-types'), {
      type: 'doughnut',
      data: {
        labels: fundTypeLabels,
        datasets: [{
          data: fundTypeData,
          backgroundColor: generateColors(fundTypeLabels.length)
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right' }
        }
      }
    }));

    // Countries Chart
    const countries = groupBy(records.filter(r => r['fund.country']), 'fund.country');
    const countryLabels = Object.keys(countries)
      .sort((a, b) => countries[b].length - countries[a].length)
      .slice(0, 10);
    const countryData = countryLabels.map(c => countries[c].length);

    charts.push(new Chart($('#chart-countries'), {
      type: 'bar',
      data: {
        labels: countryLabels.map(c => Format.countryName(c)),
        datasets: [{
          label: 'Funds',
          data: countryData,
          backgroundColor: '#DEC26F'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false }
        }
      }
    }));

    // AUM Distribution
    const aumBuckets = {
      'Unknown': 0,
      '< $100M': 0,
      '$100M - $500M': 0,
      '$500M - $1B': 0,
      '$1B - $10B': 0,
      '> $10B': 0
    };

    records.forEach(r => {
      const aum = parseFloat(r['fund.aum.value']);
      if (isNaN(aum)) {
        aumBuckets['Unknown']++;
      } else if (aum < 100000000) {
        aumBuckets['< $100M']++;
      } else if (aum < 500000000) {
        aumBuckets['$100M - $500M']++;
      } else if (aum < 1000000000) {
        aumBuckets['$500M - $1B']++;
      } else if (aum < 10000000000) {
        aumBuckets['$1B - $10B']++;
      } else {
        aumBuckets['> $10B']++;
      }
    });

    charts.push(new Chart($('#chart-aum'), {
      type: 'bar',
      data: {
        labels: Object.keys(aumBuckets),
        datasets: [{
          label: 'Funds',
          data: Object.values(aumBuckets),
          backgroundColor: '#15213B'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        }
      }
    }));

    // Sectors Chart
    const sectorCounts = {};
    records.forEach(r => {
      const sectors = Format.toArray(r['fund.sectors']);
      sectors.forEach(s => {
        sectorCounts[s] = (sectorCounts[s] || 0) + 1;
      });
    });

    const sectorLabels = Object.keys(sectorCounts)
      .sort((a, b) => sectorCounts[b] - sectorCounts[a])
      .slice(0, 10);
    const sectorData = sectorLabels.map(s => sectorCounts[s]);

    charts.push(new Chart($('#chart-sectors'), {
      type: 'bar',
      data: {
        labels: sectorLabels.map(s => Format.sectorName(s)),
        datasets: [{
          label: 'Funds',
          data: sectorData,
          backgroundColor: '#DEC26F'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false }
        }
      }
    }));
  }

  function generateColors(count) {
    const baseColors = [
      '#DEC26F', '#15213B', '#4A5682', '#A98B2C', '#7580A5',
      '#534516', '#D4AF37', '#1E2D4D', '#F2E3B7', '#A3ABC3'
    ];

    const colors = [];
    for (let i = 0; i < count; i++) {
      colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
  }

  // Cleanup on page change
  State.subscribe((path) => {
    if (path === 'activeTab' && State.get('activeTab') !== 'charts') {
      charts.forEach(chart => chart.destroy());
      charts = [];
    }
  });

  // Register page
  Router.registerPage('charts', render);
})();
