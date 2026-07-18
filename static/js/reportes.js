(function () {
    const button = document.querySelector('[data-report-pdf]');
    const desde = document.getElementById('fecha_desde');
    const hasta = document.getElementById('fecha_hasta');
    const errorBox = document.getElementById('report-range-error');

    if (!button || !desde || !hasta || !errorBox) {
        return;
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove('d-none');
        errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    button.addEventListener('click', async function () {
        if (!desde.value || !hasta.value) {
            showError('Debes seleccionar la fecha inicial y la fecha final.');
            return;
        }
        if (desde.value > hasta.value) {
            showError('La fecha inicial no puede ser mayor que la fecha final.');
            return;
        }

        const originalHtml = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Generando PDF...';

        try {
            const params = new URLSearchParams({
                fecha_desde: desde.value,
                fecha_hasta: hasta.value,
            });
            const response = await fetch(`${button.dataset.pdfUrl}?${params}`, {
                credentials: 'same-origin',
                headers: { Accept: 'application/pdf' },
            });
            if (!response.ok || !response.headers.get('Content-Type').includes('application/pdf')) {
                const data = await response.json().catch(function () { return {}; });
                throw new Error(data.message || 'No fue posible generar el PDF. Intenta nuevamente.');
            }
            const link = document.createElement('a');
            const url = URL.createObjectURL(await response.blob());
            link.href = url;
            link.download = 'reporte_mincetur.pdf';
            link.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            showError(error.message);
        } finally {
            button.disabled = false;
            button.innerHTML = originalHtml;
        }
    });
})();
