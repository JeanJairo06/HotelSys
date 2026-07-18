(function () {
    const modalElement = document.getElementById('session-timeout-modal');

    if (!modalElement || !window.bootstrap) {
        return;
    }

    const countdown = modalElement.querySelector('[data-session-countdown]');
    const announcement = modalElement.querySelector('[data-session-announcement]');
    const continueButton = modalElement.querySelector('[data-session-continue]');
    const modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',
        keyboard: false,
    });
    const warningSeconds = Number(modalElement.dataset.sessionWarningSeconds);
    const debounceSeconds = Number(modalElement.dataset.sessionActivityDebounceSeconds);
    const activityUrl = modalElement.dataset.sessionActivityUrl;
    const loginUrl = modalElement.dataset.sessionLoginUrl;
    const broadcastKey = modalElement.dataset.sessionBroadcastKey;
    let expiresAt = Number(modalElement.dataset.sessionExpiresAt);
    let activityRequestInFlight = false;
    let lastActivityRequestAt = 0;
    let expired = false;
    let warningShown = false;
    const channel = 'BroadcastChannel' in window ? new BroadcastChannel(broadcastKey) : null;

    function now() {
        return Math.floor(Date.now() / 1000);
    }

    function formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainder = seconds % 60;
        return String(minutes).padStart(2, '0') + ':' + String(remainder).padStart(2, '0');
    }

    function publish(message) {
        if (channel) {
            channel.postMessage(message);
            return;
        }

        try {
            localStorage.setItem(broadcastKey, JSON.stringify(Object.assign({ timestamp: Date.now() }, message)));
        } catch (error) {
            // Session control continues in the current tab when storage is unavailable.
        }
    }

    function updateExpiration(nextExpiresAt, shouldBroadcast) {
        if (!Number.isFinite(nextExpiresAt)) {
            return;
        }

        expiresAt = nextExpiresAt;
        warningShown = false;
        if (shouldBroadcast) {
            publish({ type: 'activity', expiresAt: expiresAt });
        }
    }

    function expire(shouldBroadcast) {
        if (expired) {
            return;
        }

        expired = true;
        window.dispatchEvent(new CustomEvent('hotelsys:session-expired'));
        if (shouldBroadcast) {
            publish({ type: 'expired' });
        }
        window.location.assign(loginUrl);
    }

    function showWarning(remainingSeconds) {
        if (!warningShown) {
            warningShown = true;
            announcement.textContent = 'Tu sesión expirará en ' + formatDuration(remainingSeconds) + '.';
            modal.show();
        }

        countdown.textContent = formatDuration(remainingSeconds);
        if (remainingSeconds === 60 || remainingSeconds === 30) {
            announcement.textContent = 'Tu sesión expirará en ' + formatDuration(remainingSeconds) + '.';
        }
    }

    function updateTimer() {
        if (expired) {
            return;
        }

        const remainingSeconds = Math.max(0, expiresAt - now());
        if (remainingSeconds === 0) {
            expire(true);
            return;
        }

        if (remainingSeconds <= warningSeconds) {
            showWarning(remainingSeconds);
        }
    }

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function refreshActivity(force) {
        const currentTime = now();
        if (expired || activityRequestInFlight || (!force && currentTime - lastActivityRequestAt < debounceSeconds)) {
            return;
        }

        activityRequestInFlight = true;
        continueButton.disabled = true;
        fetch(activityUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
        })
            .then(function (response) {
                if (response.status === 401) {
                    expire(true);
                    return null;
                }
                if (!response.ok) {
                    throw new Error('No se pudo renovar la sesión.');
                }
                return response.json();
            })
            .then(function (data) {
                if (!data) {
                    return;
                }
                lastActivityRequestAt = now();
                updateExpiration(Number(data.expires_at), true);
                modal.hide();
            })
            .catch(function () {
                announcement.textContent = 'No se pudo renovar la sesión. Guarda tu trabajo e inicia sesión nuevamente.';
            })
            .finally(function () {
                activityRequestInFlight = false;
                continueButton.disabled = false;
            });
    }

    function handleBroadcast(message) {
        if (!message || message.type === 'activity') {
            if (message && message.type === 'activity') {
                updateExpiration(Number(message.expiresAt), false);
                modal.hide();
            }
            return;
        }

        if (message.type === 'expired') {
            expire(false);
        }
    }

    ['keydown', 'pointerdown', 'touchstart', 'submit'].forEach(function (eventName) {
        document.addEventListener(eventName, function () {
            refreshActivity(false);
        }, { passive: eventName !== 'submit' });
    });

    continueButton.addEventListener('click', function () {
        refreshActivity(true);
    });

    if (channel) {
        channel.addEventListener('message', function (event) {
            handleBroadcast(event.data);
        });
    } else {
        window.addEventListener('storage', function (event) {
            if (event.key !== broadcastKey || !event.newValue) {
                return;
            }
            try {
                handleBroadcast(JSON.parse(event.newValue));
            } catch (error) {
                return;
            }
        });
    }

    updateTimer();
    window.setInterval(updateTimer, 1000);
})();
