(function () {
    const STATE_LABELS = {
        DISPONIBLE: 'Disponible',
        OCUPADA: 'Ocupada',
        LIMPIEZA: 'Limpieza',
        MANTENIMIENTO: 'Mantenimiento',
    };
    const MAX_SEEN_EVENTS = 200;

    function setStatus(root, status, text) {
        const container = root.querySelector('[data-realtime-status]');
        const label = root.querySelector('[data-realtime-status-text]');
        if (container) {
            container.dataset.status = status;
        }
        if (label) {
            label.textContent = text;
        }
    }

    function parseHotelIds(root) {
        const scriptId = root.dataset.hotelsScriptId;
        const script = scriptId ? document.getElementById(scriptId) : null;
        if (!script) {
            return [];
        }
        try {
            const values = JSON.parse(script.textContent);
            return Array.from(new Set(values.map(String).filter(Boolean)));
        } catch (error) {
            return [];
        }
    }

    function buildSocketUrl(template, hotelId) {
        const configured = template.replace('{hotel_id}', hotelId);
        if (/^wss?:\/\//i.test(configured)) {
            return configured;
        }
        if (/^https?:\/\//i.test(configured)) {
            return configured.replace(/^http/i, 'ws');
        }
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const path = configured.startsWith('/') ? configured : `/${configured}`;
        return `${protocol}//${window.location.host}${path}`;
    }

    function normalizePayload(message) {
        const candidate = message && (message.data || message.payload || message);
        if (!candidate || !candidate.habitacion_id || !candidate.estado_nuevo) {
            return null;
        }
        return candidate;
    }

    function changeCounter(root, state, amount) {
        if (!state || !Object.prototype.hasOwnProperty.call(STATE_LABELS, state)) {
            return;
        }
        root.querySelectorAll(`[data-room-state-count="${state}"]`).forEach(function (element) {
            const current = Number.parseInt(element.textContent, 10) || 0;
            element.textContent = String(Math.max(0, current + amount));
        });
    }

    function updateRoomCard(root, payload) {
        const card = root.querySelector(`[data-room-card][data-room-id="${payload.habitacion_id}"]`);
        if (!card) {
            return;
        }

        const previous = String(card.dataset.roomState || payload.estado_anterior || '').toUpperCase();
        const next = String(payload.estado_nuevo).toUpperCase();
        card.classList.remove(`room-card-${previous.toLowerCase()}`);
        card.classList.add(`room-card-${next.toLowerCase()}`);
        card.dataset.roomState = next;

        const badge = card.querySelector('.status-badge');
        if (badge) {
            Object.keys(STATE_LABELS).forEach(function (state) {
                badge.classList.remove(`status-${state.toLowerCase()}`);
            });
            badge.classList.add(`status-${next.toLowerCase()}`);
            badge.textContent = STATE_LABELS[next] || next;
        }

        card.querySelectorAll('.room-state-button').forEach(function (button) {
            button.classList.toggle('active', button.value === next);
        });
    }

    function applyPayload(root, payload) {
        const previous = String(payload.estado_anterior || '').toUpperCase();
        const next = String(payload.estado_nuevo || '').toUpperCase();
        if (previous && previous !== next) {
            changeCounter(root, previous, -1);
            changeCounter(root, next, 1);
        }
        updateRoomCard(root, payload);
        root.dispatchEvent(new CustomEvent('hotelsys:habitacion-actualizada', {
            bubbles: true,
            detail: payload,
        }));
    }

    function initialize(root) {
        const template = (root.dataset.websocketUrlTemplate || '').trim();
        const hotelIds = parseHotelIds(root);
        const seen = new Set();
        const seenOrder = [];
        let connectedSockets = 0;

        if (!template || !template.includes('{hotel_id}')) {
            setStatus(root, 'idle', 'Tiempo real listo; pendiente del backend Channels');
            return;
        }
        if (!hotelIds.length) {
            setStatus(root, 'idle', 'Sin hoteles para conectar en tiempo real');
            return;
        }

        function rememberEvent(key) {
            if (seen.has(key)) {
                return false;
            }
            seen.add(key);
            seenOrder.push(key);
            if (seenOrder.length > MAX_SEEN_EVENTS) {
                seen.delete(seenOrder.shift());
            }
            return true;
        }

        function connect(hotelId, attempt) {
            setStatus(root, 'connecting', 'Conectando actualizacion en tiempo real...');
            const socket = new WebSocket(buildSocketUrl(template, hotelId));

            socket.addEventListener('open', function () {
                connectedSockets += 1;
                setStatus(root, 'connected', 'Plano conectado en tiempo real');
            });

            socket.addEventListener('message', function (event) {
                let message;
                try {
                    message = JSON.parse(event.data);
                } catch (error) {
                    return;
                }
                const payload = normalizePayload(message);
                if (!payload) {
                    return;
                }
                const key = String(
                    payload.evento_id
                    || payload.event_id
                    || `${payload.hotel_id}:${payload.habitacion_id}:${payload.estado_nuevo}:${payload.actualizado_en || ''}`
                );
                if (rememberEvent(key)) {
                    applyPayload(root, payload);
                }
            });

            socket.addEventListener('close', function () {
                connectedSockets = Math.max(0, connectedSockets - 1);
                if (!connectedSockets) {
                    setStatus(root, 'error', 'Conexion interrumpida; reintentando...');
                }
                const nextAttempt = Math.min(attempt + 1, 6);
                const delay = Math.min(30000, 1000 * (2 ** nextAttempt)) + Math.floor(Math.random() * 500);
                window.setTimeout(function () {
                    connect(hotelId, nextAttempt);
                }, delay);
            });

            socket.addEventListener('error', function () {
                socket.close();
            });
        }

        hotelIds.forEach(function (hotelId) {
            connect(hotelId, 0);
        });
    }

    document.querySelectorAll('[data-room-realtime]').forEach(initialize);
})();
