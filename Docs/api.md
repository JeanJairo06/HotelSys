# API Documentation - HotelSys

Este documento define la estructura actual de APIs en HotelSys y las reglas que deben seguir los desarrolladores al crear nuevos endpoints.

La API vive bajo `api/` y funciona como una capa común para contratos JSON, autenticación, permisos, paginación, throttling, filtros, manejo de errores y documentación OpenAPI.

## Base URL

Desarrollo:

```text
http://localhost:8000/api/v1/
```

Documentación interactiva:

| Recurso | URL |
|---|---|
| OpenAPI schema | `/api/v1/schema/` |
| Swagger UI | `/api/v1/docs/` |
| Redoc | `/api/v1/redoc/` |

## Estructura Core API

La carpeta `api/` centraliza piezas reutilizables. No dupliques estas responsabilidades en apps como `empleados`, `cuentas`, `reservas`, etc.

| Archivo | Responsabilidad |
|---|---|
| `api/urls.py` | Registro de rutas públicas bajo `/api/v1/` |
| `api/views.py` | Vistas API transversales o endpoints internos compartidos |
| `api/serializers.py` | Serializers para contratos JSON actuales |
| `api/auth.py` | Login JWT y claims personalizados |
| `api/permissions.py` | Permisos por rol y empleado activo |
| `api/pagination.py` | Formato estándar de respuestas paginadas |
| `api/filters.py` | Mixins reutilizables de filtros comunes |
| `api/throttles.py` | Límites de consumo por tipo de endpoint |
| `api/exceptions.py` | Formato estándar de errores API |

## Configuración Global DRF

La configuración está en `config/settings.py` dentro de `REST_FRAMEWORK`.

Valores principales:

| Configuración | Valor |
|---|---|
| Autenticación global | `JWTAuthentication` |
| Permiso global | `IsAuthenticated` |
| Paginación global | `api.pagination.StandardResultsSetPagination` |
| Filtros globales | `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter` |
| Schema | `drf_spectacular.openapi.AutoSchema` |
| Errores | `api.exceptions.standard_exception_handler` |

Cuando un endpoint se consume desde templates/AJAX usando sesión Django, agrega explícitamente `SessionAuthentication` en la vista.

Ejemplo:

```python
authentication_classes = [SessionAuthentication, JWTAuthentication]
```

## Autenticación

HotelSys soporta JWT para API y sesión Django cuando un endpoint se consume desde vistas internas.

### Obtener Token

```http
POST /api/v1/auth/token/
```

Request:

```json
{
  "username": "admin",
  "password": "123456"
}
```

Response:

```json
{
  "refresh": "...",
  "access": "...",
  "user": {
    "id": 1,
    "username": "admin",
    "roles": ["ADMIN"]
  },
  "empleado": {
    "id": 1,
    "codigo": "EMP001",
    "nombre_completo": "Admin Principal",
    "cargo": "ADMIN"
  }
}
```

El access token incluye claims adicionales:

| Claim | Descripción |
|---|---|
| `username` | Username Django |
| `roles` | Grupos asignados al usuario |
| `empleado_id` | ID del empleado vinculado, si existe |
| `empleado_codigo` | Código del empleado vinculado |
| `cargo` | Cargo del empleado vinculado |

### Refrescar Token

```http
POST /api/v1/auth/token/refresh/
```

Request:

```json
{
  "refresh": "..."
}
```

### Uso del Token

Enviar el token en cada request externa:

```http
Authorization: Bearer <access_token>
```

## Roles y Permisos

Los roles se basan en grupos Django y helpers de `cuentas.roles`.

Roles soportados actualmente:

| Rol | Uso |
|---|---|
| `ADMIN` | Administración del sistema |
| `RECEPCIONISTA` | Operación hotelera |
| `HOUSEKEEPING` | Limpieza y estado operativo |

Permisos disponibles en `api/permissions.py`:

| Permiso | Uso |
|---|---|
| `IsEmpleadoActivo` | Requiere usuario autenticado con empleado vinculado activo |
| `IsAdminRole` | Requiere rol `ADMIN` |
| `IsRecepcionistaRole` | Requiere rol `RECEPCIONISTA` |
| `IsHousekeepingRole` | Requiere rol `HOUSEKEEPING` |
| `HasAnyRole` | Lee `allowed_roles` desde la vista |

Ejemplo con un rol específico:

```python
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsAdminRole


permission_classes = [IsAuthenticated, IsAdminRole]
```

Ejemplo con varios roles:

```python
from cuentas.roles import ROLE_ADMIN, ROLE_RECEPCIONISTA
from api.permissions import HasAnyRole


class ReservasAPIView(generics.ListAPIView):
    permission_classes = [HasAnyRole]
    allowed_roles = [ROLE_ADMIN, ROLE_RECEPCIONISTA]
```

## Paginación

La paginación estándar está en `api.pagination.StandardResultsSetPagination`.

Parámetros soportados:

| Parámetro | Descripción |
|---|---|
| `page` | Número de página |
| `page_size` | Tamaño de página solicitado |

Límites:

| Valor | Configuración |
|---|---|
| Tamaño por defecto de clase | `20` |
| Tamaño global DRF | `15` |
| Máximo permitido | `100` |

Formato de respuesta paginada:

```json
{
  "count": 120,
  "next": "http://localhost:8000/api/v1/recurso/?page=2",
  "previous": null,
  "results": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_pages": 6
  }
}
```

Los endpoints nuevos deben usar la paginación global salvo que exista una razón funcional para cambiarla.

## Filtros, Search y Ordering

Los backends globales ya están habilitados:

```python
filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
```

Define campos explícitos en cada vista:

```python
search_fields = ['codigo', 'nombres', 'apellidos', 'email']
ordering_fields = ['codigo', 'apellidos', 'nombres']
ordering = ['apellidos', 'nombres']
```

Mixins disponibles:

| Mixin | Campos |
|---|---|
| `EstadoFilterMixin` | `estado` con comparación `iexact` |
| `FechaRangoFilterMixin` | `desde` y `hasta` sobre `fecha_registro__date` |

Usa `search` para búsquedas de texto compatibles con DRF:

```http
GET /api/v1/empleados/disponibles-para-usuario/?search=ana
```

## Throttling

Los límites están centralizados en `api/throttles.py` y configurados en `settings.py`.

| Clase | Scope | Rate |
|---|---|---|
| `LoginRateThrottle` | `login` | `5/min` |
| `UserApiRateThrottle` | `user` | `500/hour` |
| `WriteRateThrottle` | `write` | `100/hour` |
| `AutocompleteRateThrottle` | `autocomplete` | `60/min` |

Reglas:

- Endpoints de login deben usar `LoginRateThrottle`.
- Autocompletados o búsquedas rápidas deben usar `AutocompleteRateThrottle`.
- Operaciones de escritura expuestas a clientes externos deben usar `WriteRateThrottle` o un scope más específico.

Ejemplo:

```python
from api.throttles import AutocompleteRateThrottle


throttle_classes = [AutocompleteRateThrottle]
throttle_scope = 'autocomplete'
```

## Manejo Estándar de Errores

Las excepciones pasan por `api.exceptions.standard_exception_handler`.

Formato:

```json
{
  "error": true,
  "code": "PERMISSION_DENIED",
  "message": "No tiene permisos para acceder a este recurso.",
  "detail": {
    "detail": "No tiene permisos para acceder a este recurso."
  }
}
```

Códigos estándar:

| HTTP | Code |
|---|---|
| `400` | `VALIDATION_ERROR` |
| `401` | `AUTHENTICATION_FAILED` |
| `403` | `PERMISSION_DENIED` |
| `404` | `NOT_FOUND` |
| `405` | `METHOD_NOT_ALLOWED` |
| `429` | `THROTTLED` |
| `500` | `SERVER_ERROR` |

No devuelvas errores manuales con formatos distintos salvo que exista un contrato explícito.

## Cómo Crear un Nuevo Endpoint

Sigue este flujo para mantener consistencia.

### 1. Crear o reutilizar serializer

Ubicación recomendada:

- Si el contrato es transversal o usado por varias apps: `api/serializers.py`.
- Si el contrato pertenece solo a una app grande: `app/serializers.py`, importándolo desde la vista API correspondiente.

Ejemplo:

```python
from rest_framework import serializers

from empleados.models import Empleado


class EmpleadoResumenSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='nombre_completo', read_only=True)

    class Meta:
        model = Empleado
        fields = ['id', 'text', 'codigo', 'email']
```

### 2. Crear vista DRF

Usa genéricos de DRF cuando sea posible.

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.permissions import IsAdminRole
from api.throttles import AutocompleteRateThrottle


class RecursoAPIView(generics.ListAPIView):
    serializer_class = RecursoSerializer
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]
    throttle_classes = [AutocompleteRateThrottle]
    throttle_scope = 'autocomplete'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    ordering = ['nombre']

    def get_queryset(self):
        return Recurso.objects.all()
```

### 3. Documentar con drf-spectacular

Cada endpoint nuevo debe tener `extend_schema` o `extend_schema_view`.

```python
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    get=extend_schema(
        tags=['Empleados'],
        summary='Lista empleados disponibles',
        description='Endpoint paginado y filtrable para autocompletados.',
    )
)
class RecursoAPIView(generics.ListAPIView):
    ...
```

### 4. Registrar ruta

Agregar en `api/urls.py`:

```python
path('recurso/', RecursoAPIView.as_view(), name='recurso_list'),
```

Reglas de nombres:

- Usar URLs en español si el módulo de negocio ya está en español.
- Usar kebab-case para segmentos compuestos: `disponibles-para-usuario`.
- Usar nombres de ruta claros: `empleados_disponibles_usuario`.

### 5. Verificar schema y checks

Antes de abrir PR o entregar cambios:

```bash
python manage.py check
```

También revisar:

```text
/api/v1/docs/
```

## Reglas de Diseño de Contratos

- Mantener respuestas JSON estables.
- No cambiar nombres de campos sin coordinar con consumidores.
- Usar `id` como identificador primario en payloads.
- Para labels de autocompletado, usar `text`.
- Para displays de choices, usar sufijo `_display`.
- Para fechas, usar ISO 8601.
- Para dinero, usar decimal como string o number según serializer DRF, evitando floats calculados manualmente.
- No incluir datos sensibles en serializers.
- No exponer usuarios o empleados inactivos salvo requerimiento explícito.

## Consumo Desde Templates

Cuando un endpoint se consume desde una plantilla con `fetch`, usar sesión Django y credenciales same-origin.

Ejemplo:

```javascript
fetch(endpoint, {
    credentials: 'same-origin',
    headers: { 'Accept': 'application/json' },
})
```

El endpoint debe incluir:

```python
authentication_classes = [SessionAuthentication, JWTAuthentication]
```

## Estado Actual

Endpoints reales disponibles:

| Método | Endpoint | Uso |
|---|---|---|
| `POST` | `/api/v1/auth/token/` | Obtener JWT |
| `POST` | `/api/v1/auth/token/refresh/` | Refrescar JWT |
| `GET` | `/api/v1/empleados/disponibles-para-usuario/` | Autocompletado de empleados activos sin usuario |

Los endpoints de habitaciones, reservas, huéspedes, estancias, facturación y reportes todavía no están expuestos como API REST en esta implementación. Cuando se agreguen, deben seguir las reglas de este documento.
