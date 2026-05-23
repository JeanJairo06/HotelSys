(function () {
    const piso = document.querySelector('[data-housekeeping-piso]');

    if (!piso) {
        return;
    }

    piso.addEventListener('change', function () {
        piso.form.requestSubmit();
    });
})();
