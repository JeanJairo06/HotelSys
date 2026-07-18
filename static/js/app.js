(function () {
    document.addEventListener('submit', function (event) {
        const form = event.target.closest('form[data-submit-lock]');
        if (!form || form.dataset.submitting) {
            if (form) {
                event.preventDefault();
            }
            return;
        }
        form.dataset.submitting = 'true';
        form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (control) {
            control.disabled = true;
        });
    });

    window.addEventListener('pageshow', function () {
        document.querySelectorAll('form[data-submit-lock]').forEach(function (form) {
            delete form.dataset.submitting;
            form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (control) {
                control.disabled = false;
            });
        });
    });
})();
