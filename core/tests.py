from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from core.consumers import HabitacionesPlanoConsumer


class HabitacionesPlanoConsumerTests(IsolatedAsyncioTestCase):
    async def test_cierra_el_socket_cuando_expira_la_sesion(self):
        consumer = HabitacionesPlanoConsumer()
        consumer.close = AsyncMock()

        await consumer.session_expired({})

        consumer.close.assert_awaited_once_with(code=4401)
