(function () {
    const searchInput = document.querySelector('[data-room-search]');
    const cards = document.querySelectorAll('[data-room-card]');
    const page = document.querySelector('[data-hotel-id]');

    if (searchInput && cards.length) {
        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim().toLowerCase();

            cards.forEach(function (card) {
                const text = [
                    card.dataset.numero,
                    card.dataset.tipoNombre,
                    card.dataset.piso,
                    card.dataset.estado,
                    card.dataset.estadoLabel,
                ].join(' ').toLowerCase();
                card.hidden = query !== '' && !text.includes(query);
            });

            document.querySelectorAll('[data-room-floor]').forEach(function (floor) {
                const visibleCards = floor.querySelectorAll('[data-room-card]:not([hidden])');
                floor.hidden = visibleCards.length === 0;
            });
        });
    }

    document.querySelectorAll('[data-auto-submit]').forEach(function (field) {
        field.addEventListener('change', function () {
            field.form.requestSubmit();
        });
    });

    const drawer = document.querySelector('[data-room-drawer]');
    const backdrop = document.querySelector('[data-room-drawer-backdrop]');
    const closeButton = document.querySelector('[data-room-drawer-close]');

    if (!drawer || !backdrop) {
        return;
    }

    const drawerNumber = drawer.querySelector('[data-drawer-room-number]');
    const drawerDetail = drawer.querySelector('[data-drawer-room-detail]');
    const drawerStatus = drawer.querySelector('[data-drawer-status]');
    const editForm = drawer.querySelector('[data-room-edit-form]');
    const statusForm = drawer.querySelector('[data-room-status-form]');
    const numeroInput = drawer.querySelector('[data-drawer-numero-input]');
    const tipoInput = drawer.querySelector('[data-drawer-tipo-input]');
    const pisoInput = drawer.querySelector('[data-drawer-piso-input]');
    const statusOptions = drawer.querySelectorAll('[data-status-option]');

    function setStatusBadge(estado, label) {
        drawerStatus.className = 'status-badge status-' + estado.toLowerCase();
        drawerStatus.textContent = label;
    }

    function updateStatusOptions(estado) {
        statusOptions.forEach(function (option) {
            option.classList.toggle('active', option.dataset.statusOption === estado);
        });
    }

    function openDrawer(card) {
        const numero = card.dataset.numero;
        const tipoNombre = card.dataset.tipoNombre;
        const piso = card.dataset.piso;
        const estado = card.dataset.estado;

        drawerNumber.textContent = numero;
        drawerDetail.textContent = 'Piso ' + piso + ' - ' + tipoNombre;
        setStatusBadge(estado, card.dataset.estadoLabel);

        if (editForm) {
            editForm.action = card.dataset.editarUrl;
            numeroInput.value = numero;
            tipoInput.value = card.dataset.tipoId;
            pisoInput.value = piso;
        }

        statusForm.action = card.dataset.estadoUrl;
        updateStatusOptions(estado);

        backdrop.hidden = false;
        drawer.classList.add('active');
        drawer.setAttribute('aria-hidden', 'false');
        document.body.classList.add('room-drawer-open');
    }

    function closeDrawer() {
        drawer.classList.remove('active');
        drawer.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('room-drawer-open');
        window.setTimeout(function () {
            if (!drawer.classList.contains('active')) {
                backdrop.hidden = true;
            }
        }, 180);
    }

    cards.forEach(function (card) {
        card.addEventListener('click', function () {
            openDrawer(card);
        });
        card.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                openDrawer(card);
            }
        });
    });

    backdrop.addEventListener('click', closeDrawer);
    closeButton.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && drawer.classList.contains('active')) {
            closeDrawer();
        }
    });

    function estadoLabel(estado) {
        const labels = {
            DISPONIBLE: 'Disponible',
            OCUPADA: 'Ocupada',
            LIMPIEZA: 'Limpieza',
            MANTENIMIENTO: 'Mantenimiento',
        };
        return labels[estado] || estado;
    }

    function applyRoomUpdate(payload, options) {
        const card = document.querySelector('[data-room-card][data-habitacion-id="' + payload.habitacion_id + '"]');
        if (!card) {
            return;
        }

        const settings = options || {};
        const estado = payload.estado_nuevo;
        const label = estadoLabel(estado);
        const estadoAnterior = card.dataset.estado;

        if (!settings.skipCounters && estadoAnterior !== estado) {
            updateStatusCount(estadoAnterior, -1);
            updateStatusCount(estado, 1);
        }

        card.classList.remove('room-tile-' + estadoAnterior.toLowerCase());
        card.classList.add('room-tile-' + estado.toLowerCase());
        card.dataset.estado = estado;
        card.dataset.estadoLabel = label;
        card.dataset.tipoNombre = payload.tipo_habitacion || card.dataset.tipoNombre;
        card.dataset.piso = payload.piso || card.dataset.piso;
        card.dataset.numero = payload.numero || card.dataset.numero;
        card.setAttribute('aria-label', 'Abrir habitacion ' + card.dataset.numero + ' - ' + label);

        if (drawer.classList.contains('active') && drawerNumber.textContent === card.dataset.numero) {
            drawerDetail.textContent = 'Piso ' + card.dataset.piso + ' - ' + card.dataset.tipoNombre;
            setStatusBadge(estado, label);
            updateStatusOptions(estado);
        }
    }

    function updateStatusCount(estado, delta) {
        const counter = document.querySelector('[data-status-count="' + estado + '"] strong');
        if (!counter || !delta) {
            return;
        }

        const value = Number.parseInt(counter.textContent, 10) || 0;
        counter.textContent = Math.max(0, value + delta);
    }

    function setStatusCounts(contadores) {
        Object.keys(contadores || {}).forEach(function (estado) {
            const counter = document.querySelector('[data-status-count="' + estado + '"] strong');
            if (counter) {
                counter.textContent = contadores[estado];
            }
        });
    }

    function syncRooms() {
        if (!page || !page.dataset.roomSyncUrl) {
            return;
        }

        const url = new URL(page.dataset.roomSyncUrl, window.location.origin);
        if (page.dataset.hotelId) {
            url.searchParams.set('hotel_id', page.dataset.hotelId);
        }

        fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('No se pudo sincronizar habitaciones');
                }
                return response.json();
            })
            .then(function (data) {
                (data.habitaciones || []).forEach(function (habitacion) {
                    applyRoomUpdate(habitacion, {skipCounters: true});
                });
                setStatusCounts(data.contadores);
            })
            .catch(function (error) {
                console.error(error);
            });
    }

    function connectRoomSocket() {
        if (!page || !page.dataset.hotelId || !window.WebSocket) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const socket = new WebSocket(protocol + '://' + window.location.host + '/ws/hoteles/' + page.dataset.hotelId + '/habitaciones/');

        socket.addEventListener('message', function (event) {
            try {
                applyRoomUpdate(JSON.parse(event.data));
            } catch (error) {
                console.error('No se pudo procesar evento de habitacion', error);
            }
        });

        socket.addEventListener('close', function () {
            window.setTimeout(connectRoomSocket, 3000);
        });
    }

    connectRoomSocket();
    syncRooms();
    window.setInterval(syncRooms, 10000);
    window.addEventListener('focus', syncRooms);
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) {
            syncRooms();
        }
    });
})();
