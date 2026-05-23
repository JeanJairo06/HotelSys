(function () {
    const estado = document.querySelector('[data-estancia-estado]');

    if (!estado) {
        return;
    }

    estado.addEventListener('change', function () {
        estado.form.requestSubmit();
    });
})();
