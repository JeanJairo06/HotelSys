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

    const stateLabels = {
        DISPONIBLE: 'Disponible',
        OCUPADA: 'Ocupada',
        LIMPIEZA: 'Limpieza',
        MANTENIMIENTO: 'Mantenimiento',
    };
    const modal = document.getElementById('roomDetailModal');
    let activeRoomId = null;

    function setText(selector, value, fallback) {
        const target = modal ? modal.querySelector(selector) : null;
        if (target) {
            target.textContent = value || fallback || 'No registrado';
        }
    }

    function setLink(selector, href) {
        const target = modal ? modal.querySelector(selector) : null;
        if (!target) {
            return;
        }
        target.classList.toggle('d-none', !href);
        target.href = href || '#';
    }

    function fillDetail(card) {
        if (!modal || !card) {
            return;
        }
        activeRoomId = card.dataset.roomId;
        const state = String(card.dataset.roomState || '').toUpperCase();
        setText('[data-detail-number]', card.dataset.roomNumber);
        setText('[data-detail-hotel]', card.dataset.roomHotel);
        setText('[data-detail-location]', `Piso ${card.dataset.roomFloor}`);
        setText(
            '[data-detail-type]',
            `${card.dataset.roomType} · ${card.dataset.roomCapacity} persona(s)`
        );
        setText('[data-detail-guest]', card.dataset.roomGuest, 'Sin huesped alojado');
        setText(
            '[data-detail-operation]',
            [card.dataset.roomReservation, card.dataset.roomStay].filter(Boolean).join(' · '),
            'Sin operacion activa'
        );
        setText('[data-detail-checkin]', card.dataset.roomCheckin, 'Sin check-in activo');
        setLink('[data-detail-reservation-link]', card.dataset.roomReservationUrl);
        setLink('[data-detail-folio-link]', card.dataset.roomFolioUrl);

        const status = modal.querySelector('[data-detail-status]');
        if (status) {
            status.dataset.state = state;
            status.textContent = stateLabels[state] || state;
        }
    }

    document.querySelectorAll('[data-room-detail]').forEach(function (button) {
        button.addEventListener('click', function () {
            fillDetail(button.closest('[data-room-card]'));
        });
    });

    document.addEventListener('hotelsys:habitacion-actualizada', function (event) {
        const payload = event.detail || {};
        if (!activeRoomId || String(payload.habitacion_id) !== String(activeRoomId)) {
            return;
        }
        fillDetail(document.querySelector(`[data-room-card][data-room-id="${activeRoomId}"]`));
    });
})();
