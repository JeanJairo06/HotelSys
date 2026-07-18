(function () {
    const toggle = document.querySelector('[data-password-toggle]');

    if (!toggle) {
        return;
    }

    const passwordInput = document.getElementById(toggle.getAttribute('aria-controls'));
    const label = toggle.querySelector('[data-password-toggle-label]');
    const icon = toggle.querySelector('[data-password-toggle-icon]');

    if (!passwordInput || !label || !icon) {
        return;
    }

    toggle.hidden = false;

    toggle.addEventListener('click', function () {
        const passwordIsVisible = passwordInput.type === 'text';
        const action = passwordIsVisible ? 'Mostrar contraseña' : 'Ocultar contraseña';

        passwordInput.type = passwordIsVisible ? 'password' : 'text';
        toggle.setAttribute('aria-pressed', String(!passwordIsVisible));
        toggle.setAttribute('aria-label', action);
        label.textContent = action;
        icon.classList.toggle('bi-eye', passwordIsVisible);
        icon.classList.toggle('bi-eye-slash', !passwordIsVisible);
        passwordInput.focus({ preventScroll: true });
    });
})();
