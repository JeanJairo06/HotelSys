(function () {
    const root = document.querySelector('[data-room-realtime][data-report-date]');
    if (!root) {
        return;
    }

    function localDateString() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    root.addEventListener('hotelsys:habitacion-actualizada', function (event) {
        if (root.dataset.reportDate !== localDateString()) {
            return;
        }
        const payload = event.detail || {};
        const previous = String(payload.estado_anterior || '').toUpperCase();
        const next = String(payload.estado_nuevo || '').toUpperCase();
        if ((previous === 'OCUPADA') === (next === 'OCUPADA')) {
            return;
        }

        const count = root.querySelector('[data-occupancy-count]');
        const percentage = root.querySelector('[data-occupancy-percentage]');
        const donut = root.querySelector('[data-occupancy-donut] .donut-value');
        const total = Number.parseInt(root.dataset.totalRooms, 10) || 0;
        const current = Number.parseInt(count ? count.textContent : '0', 10) || 0;
        const nextCount = Math.max(0, current + (next === 'OCUPADA' ? 1 : -1));
        const nextPercentage = total ? Math.round((nextCount / total) * 100) : 0;

        if (count) {
            count.textContent = String(nextCount);
        }
        if (percentage) {
            percentage.textContent = `${nextPercentage}%`;
        }
        if (donut) {
            donut.setAttribute('stroke-dasharray', `${nextPercentage} 100`);
        }
    });
})();
