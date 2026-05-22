(function () {
    const searchInput = document.querySelector('[data-room-search]');
    const cards = document.querySelectorAll('[data-room-card]');

    if (searchInput && cards.length) {
        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim().toLowerCase();

            cards.forEach(function (card) {
                const text = card.textContent.toLowerCase();
                card.hidden = query !== '' && !text.includes(query);
            });
        });
    }

    document.querySelectorAll('[data-auto-submit]').forEach(function (field) {
        field.addEventListener('change', function () {
            field.form.requestSubmit();
        });
    });
})();
