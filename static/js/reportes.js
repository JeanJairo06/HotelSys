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

    function clearError() {
        errorBox.textContent = '';
        errorBox.classList.add('d-none');
    }

    function getFilename(response) {
        const disposition = response.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^";]+)"?/i);
        return match ? match[1] : 'reporte_hotelsys.pdf';
    }

    button.addEventListener('click', async function () {
        if (button.disabled) {
            return;
        }

        clearError();
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
        button.setAttribute('aria-busy', 'true');
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Generando PDF...';

        const params = new URLSearchParams({
            fecha_desde: desde.value,
            fecha_hasta: hasta.value,
        });

        try {
            const response = await fetch(`${button.dataset.pdfUrl}?${params.toString()}`, {
                credentials: 'same-origin',
                headers: { Accept: 'application/pdf' },
            });
            const contentType = response.headers.get('Content-Type') || '';

            if (!response.ok || !contentType.includes('application/pdf')) {
                let message = 'No fue posible generar el PDF. Intenta nuevamente.';
                if (contentType.includes('application/json')) {
                    const data = await response.json();
                    message = data.message || message;
                }
                throw new Error(message);
            }

            const blob = await response.blob();
            const objectUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = objectUrl;
            link.download = getFilename(response);
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(objectUrl);
        } catch (error) {
            showError(error.message || 'No fue posible generar el PDF. Intenta nuevamente.');
        } finally {
            button.disabled = false;
            button.removeAttribute('aria-busy');
            button.innerHTML = originalHtml;
        }
    });
})();
