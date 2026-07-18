(function () {
    function restoreForm(form) {
        form.classList.remove('is-submitting');
        form.removeAttribute('aria-busy');
        form.querySelectorAll('[data-submit-lock-disabled]').forEach(function (control) {
            control.disabled = false;
            control.removeAttribute('data-submit-lock-disabled');
            if (control.dataset.originalHtml) {
                control.innerHTML = control.dataset.originalHtml;
                delete control.dataset.originalHtml;
            }
        });
        form.querySelectorAll('[data-submit-lock-value]').forEach(function (input) {
            input.remove();
        });
    }

    document.addEventListener('submit', function (event) {
        const form = event.target.closest('form[data-submit-lock]');
        if (!form || form.classList.contains('is-submitting')) {
            if (form) {
                event.preventDefault();
            }
            return;
        }

        const confirmation = form.dataset.confirm;
        if (confirmation && !window.confirm(confirmation)) {
            event.preventDefault();
            return;
        }

        const submitter = event.submitter;
        if (submitter && submitter.name) {
            const value = document.createElement('input');
            value.type = 'hidden';
            value.name = submitter.name;
            value.value = submitter.value;
            value.dataset.submitLockValue = 'true';
            form.appendChild(value);
        }

        form.classList.add('is-submitting');
        form.setAttribute('aria-busy', 'true');
        form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (control) {
            control.dataset.submitLockDisabled = 'true';
            control.disabled = true;
            if (control.tagName === 'BUTTON') {
                control.dataset.originalHtml = control.innerHTML;
                control.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Procesando...';
            }
        });
    });

    window.addEventListener('pageshow', function () {
        document.querySelectorAll('form[data-submit-lock].is-submitting').forEach(restoreForm);
    });
})();
