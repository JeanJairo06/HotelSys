from channels.generic.websocket import AsyncJsonWebsocketConsumer

from cuentas.roles import ROLE_ADMIN, ROLE_HOUSEKEEPING, ROLE_RECEPCIONISTA


class HabitacionesPlanoConsumer(AsyncJsonWebsocketConsumer):
    roles_permitidos = {ROLE_ADMIN, ROLE_RECEPCIONISTA, ROLE_HOUSEKEEPING}

    async def connect(self):
        self.hotel_id = self.scope['url_route']['kwargs']['hotel_id']
        self.group_name = f'hotel_{self.hotel_id}_habitaciones'
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self._usuario_tiene_rol_permitido(user):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def habitacion_estado(self, event):
        await self.send_json(event['payload'])

    async def _usuario_tiene_rol_permitido(self, user):
        if user.is_superuser:
            return True

        return await user.groups.filter(name__in=self.roles_permitidos).aexists()
