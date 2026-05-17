from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from api.throttles import LoginRateThrottle


class HotelSysTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['roles'] = list(user.groups.values_list('name', flat=True))

        perfil = getattr(user, 'perfil_empleado', None)
        if perfil:
            empleado = perfil.empleado
            token['empleado_id'] = empleado.id
            token['empleado_codigo'] = empleado.codigo
            token['cargo'] = empleado.cargo

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'roles': list(user.groups.values_list('name', flat=True)),
        }

        perfil = getattr(user, 'perfil_empleado', None)
        if perfil:
            empleado = perfil.empleado
            data['empleado'] = {
                'id': empleado.id,
                'codigo': empleado.codigo,
                'nombre_completo': empleado.nombre_completo,
                'cargo': empleado.cargo,
            }

        return data


class HotelSysTokenObtainPairView(TokenObtainPairView):
    serializer_class = HotelSysTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]
