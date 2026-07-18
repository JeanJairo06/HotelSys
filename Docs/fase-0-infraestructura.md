# Fase 0 Infraestructura — HotelSys

Este documento explica cómo debe usar el equipo la infraestructura base implementada en la Fase 0.

La Fase 0 no implementa lógica funcional de reservas, estancias, facturación o reportes. Su objetivo es dejar una base común para que todos los módulos trabajen con las mismas reglas arquitectónicas.

Incluye:
- app `core`,
- `ModeloBase`,
- excepciones globales de dominio,
- Django Channels,
- Redis channel layer,
- ASGI con Daphne,
- consumer WebSocket base para el plano de habitaciones,
- publicador de eventos de habitación,
- Docker Compose con Django, PostgreSQL y Redis.

---

# 1. Regla Principal

Toda rama nueva debe salir desde la rama que contenga esta infraestructura.

Ningún integrante debe crear:
- otra clase base abstracta,
- otro sistema de excepciones globales,
- otra configuración de Channels,
- otro Redis channel layer,
- otro consumer global para habitaciones,
- otro formato de error API.

Si un módulo necesita extender esta base, debe hacerlo reutilizando `core`.

---

# 2. Archivos Agregados o Modificados

## Archivos nuevos

| Archivo | Uso |
|---|---|
| `core/models.py` | Modelo base abstracto, manager de activos y soft delete lógico |
| `core/exceptions.py` | Jerarquía global de excepciones de dominio |
| `core/consumers.py` | Consumer WebSocket base para el plano de habitaciones |
| `core/routing.py` | Rutas WebSocket del proyecto |
| `core/events.py` | Publicador de eventos backend para habitaciones |
| `core/apps.py` | Configuración de la app `core` |

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `config/settings.py` | Agrega `daphne`, `channels`, `core`, `ASGI_APPLICATION` y `CHANNEL_LAYERS` |
| `config/asgi.py` | Configura HTTP y WebSocket con Channels |
| `api/exceptions.py` | Integra `AppError` al handler DRF existente |
| `requirements.txt` | Agrega dependencias de Channels, Redis y Daphne |
| `docker-compose.yml` | Agrega Redis y ejecuta Django con Daphne |
| `.env.example` | Agrega variables de Redis |

---

# 3. Cómo Preparar El Entorno

## 3.1 Actualizar dependencias

Si se trabaja fuera de Docker:

```bash
pip install -r requirements.txt
```

Si se trabaja con Docker:

```bash
docker compose build
```

---

## 3.2 Variables de entorno requeridas

El archivo `.env.example` ahora incluye:

```env
REDIS_HOST=redis
REDIS_PORT=6379
```

Para Docker, `REDIS_HOST` debe ser:

```env
REDIS_HOST=redis
```

Para ejecución local sin Docker, si Redis corre en la máquina local:

```env
REDIS_HOST=localhost
```

---

## 3.3 Advertencia sobre SECRET_KEY

Docker Compose interpreta el carácter `$` como variable de entorno.

Si `SECRET_KEY` contiene `$`, hay dos opciones:

Escaparlo duplicando el símbolo:

```env
SECRET_KEY=django-insecure-clave-con-$$-escapado
```

O usar una clave simple para desarrollo:

```env
SECRET_KEY=django-insecure-dev-key-hotelsys-2026
```

No subir `.env` al repositorio.

---

# 4. Cómo Levantar El Proyecto

## 4.1 Con Docker

```bash
docker compose up --build
```

Servicios esperados:

| Servicio | Uso |
|---|---|
| `web` | Django ejecutado con Daphne sobre ASGI |
| `db` | PostgreSQL |
| `redis` | Channel layer para WebSockets |

El servicio `web` depende de que `db` y `redis` estén saludables.

---

## 4.2 Verificación dentro del contenedor

```bash
docker compose exec web python manage.py check
```

También se puede validar migraciones pendientes:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

---

# 5. Uso De ModeloBase

`ModeloBase` está en:

```python
from core.models import ModeloBase
```

Debe usarse como clase base para modelos nuevos y para modelos existentes cuando cada módulo haga su migración.

Ejemplo:

```python
from core.models import ModeloBase


class MiModelo(ModeloBase):
    nombre = models.CharField(max_length=100)
```

Campos heredados:

| Campo | Uso |
|---|---|
| `creado_en` | Fecha de creación automática |
| `actualizado_en` | Fecha de última actualización automática |
| `creado_por` | Usuario que creó el registro, asignado desde servicios cuando aplique |
| `activo` | Marca de soft delete |

Managers disponibles:

| Manager | Uso |
|---|---|
| `objects` | Devuelve solo registros activos |
| `todos` | Devuelve activos e inactivos |

Ejemplos:

```python
MiModelo.objects.all()
```

Devuelve solo registros con `activo=True`.

```python
MiModelo.todos.all()
```

Devuelve todos los registros.

---

## 5.1 Soft Delete

Para desactivar un registro:

```python
objeto.eliminar()
```

Esto marca:

```python
activo = False
```

Regla importante:
- No usar `delete()` para datos históricos como reservas, estancias, folios, cargos, pagos o huéspedes.
- Usar `eliminar()` cuando el registro deba quedar en historial.
- Si un modelo tiene campos `unique=True`, revisar el impacto antes de aplicar soft delete.

Ejemplo de riesgo:

```python
num_doc = models.CharField(max_length=20, unique=True)
```

Si un huésped se desactiva, el documento seguirá bloqueado por la restricción única. Ese caso debe resolverse por módulo antes de migrar.

---

## 5.2 creado_por

`creado_por` no se asigna automáticamente.

Debe asignarse desde el servicio cuando exista usuario disponible.

Ejemplo:

```python
objeto = MiModelo.objects.create(
    nombre='Dato',
    creado_por=usuario,
)
```

No agregar middleware global para esto sin aprobación del líder técnico.

---

# 6. Uso De Excepciones Globales

Las excepciones base están en:

```python
from core.exceptions import AppError, ReglaNegocioViolada, RecursoNoEncontrado
```

## 6.1 Excepciones disponibles

| Excepción | Uso |
|---|---|
| `AppError` | Base común para errores de dominio |
| `ReglaNegocioViolada` | Cuando una regla del negocio impide la operación |
| `RecursoNoEncontrado` | Cuando un recurso de dominio no existe |
| `AccesoNoAutorizado` | Cuando el usuario no tiene permisos |
| `OperacionNoPermitida` | Cuando el estado actual no permite la acción |
| `ValidacionDominioError` | Cuando los datos no son válidos para el dominio |

---

## 6.2 Cómo crear excepciones de cada módulo

Cada módulo debe crear sus propias excepciones heredando de las globales.

Ejemplo para reservas:

```python
from core.exceptions import ReglaNegocioViolada, OperacionNoPermitida


class ReservaSolapada(ReglaNegocioViolada):
    code = 'RESERVA_SOLAPADA'
    default_message = 'La habitación ya tiene una reserva en ese rango de fechas.'


class ReservaNoModificable(OperacionNoPermitida):
    code = 'RESERVA_NO_MODIFICABLE'
    default_message = 'La reserva no puede modificarse en su estado actual.'
```

Ejemplo para estancias:

```python
from core.exceptions import ReglaNegocioViolada


class HabitacionNoDisponible(ReglaNegocioViolada):
    code = 'HABITACION_NO_DISPONIBLE'
    default_message = 'La habitación no está disponible para esta operación.'
```

---

## 6.3 Cómo lanzar excepciones en servicios

```python
if habitacion.estado != EstadoHabitacion.DISPONIBLE:
    raise HabitacionNoDisponible()
```

Con mensaje personalizado:

```python
raise HabitacionNoDisponible('La habitación está en mantenimiento.')
```

Con detalle adicional:

```python
raise HabitacionNoDisponible(
    detail={
        'habitacion_id': habitacion.id,
        'estado': habitacion.estado,
    }
)
```

---

## 6.4 Respuesta automática en API

El handler `api.exceptions.standard_exception_handler` ya convierte `AppError` al formato estándar:

```json
{
  "error": true,
  "code": "HABITACION_NO_DISPONIBLE",
  "message": "La habitación no está disponible para esta operación.",
  "detail": {}
}
```

Por eso, en endpoints DRF no se debe envolver manualmente cada `AppError` si el handler global puede procesarlo.

---

## 6.5 Uso en templates Django

En views HTML se puede capturar la excepción y mostrarla con `messages`.

```python
from django.contrib import messages
from core.exceptions import AppError


try:
    servicio.ejecutar()
except AppError as error:
    messages.error(request, error.message)
```

---

# 7. Service Layer

La Fase 0 deja la infraestructura para que cada módulo mueva su lógica a servicios.

Regla general:
- La view recibe datos.
- La view valida formato básico.
- La view llama al servicio.
- El servicio decide reglas de negocio.
- El servicio lanza excepciones de dominio.
- La view devuelve respuesta o redirección.

---

## 7.1 Ejemplo correcto

```python
class RealizarCheckinAPIView(APIView):
    def post(self, request, reserva_id):
        estancia = EstanciaService.checkin(
            reserva_id=reserva_id,
            usuario=request.user,
        )
        return Response(EstanciaSerializer(estancia).data, status=201)
```

La lógica no debe quedar en la view.

---

## 7.2 Ejemplo incorrecto

```python
class RealizarCheckinAPIView(APIView):
    def post(self, request, reserva_id):
        reserva = Reserva.objects.get(pk=reserva_id)
        if reserva.habitacion.estado != EstadoHabitacion.DISPONIBLE:
            return Response({'detail': 'No disponible'}, status=400)
        reserva.habitacion.estado = EstadoHabitacion.OCUPADA
        reserva.habitacion.save()
```

Problemas:
- regla de negocio dentro de la view,
- error no usa excepción de dominio,
- no hay transacción,
- no hay evento WebSocket,
- no hay contrato reutilizable para templates.

---

# 8. Transacciones

Toda operación que modifique más de una entidad debe usar transacción.

Ejemplos:
- crear reserva con tarifa calculada,
- check-in,
- checkout,
- registrar pago y recalcular saldo,
- agregar cargo y actualizar folio,
- cambiar estado de habitación y emitir evento.

Uso:

```python
from django.db import transaction


@transaction.atomic
def ejecutar_operacion():
    ...
```

Regla:
- Si la operación falla, no debe quedar información parcial.

---

# 9. WebSockets

La infraestructura WebSocket ya está configurada con Django Channels.

Ruta disponible:

```text
/ws/hoteles/<hotel_id>/habitaciones/
```

Ejemplo:

```text
/ws/hoteles/1/habitaciones/
```

El consumer está en:

```text
core/consumers.py
```

La ruta está en:

```text
core/routing.py
```

---

## 9.1 Seguridad del WebSocket

El consumer acepta solo usuarios autenticados.

Roles permitidos:
- `admin`,
- `recepcionista`,
- `housekeeping`.

Si el usuario no está autenticado, se cierra con código:

```text
4401
```

Si no tiene rol permitido, se cierra con código:

```text
4403
```

Pendiente por dominio:
- Si luego se define relación usuario-hotel, el consumer debe validar que el usuario pertenezca al hotel solicitado.

---

## 9.2 Grupo WebSocket

Cada hotel tiene su propio grupo:

```text
hotel_<hotel_id>_habitaciones
```

Ejemplo:

```text
hotel_1_habitaciones
```

Esto evita enviar cambios de un hotel a usuarios conectados a otro hotel.

---

# 10. Publicación De Eventos De Habitación

El publicador está en:

```python
from core.events import publicar_evento_habitacion
```

Debe usarse después de cambios confirmados en habitación.

Ejemplo:

```python
from core.events import EVENTO_HABITACION_OCUPADA, publicar_evento_habitacion


estado_anterior = habitacion.estado
habitacion.estado = EstadoHabitacion.OCUPADA
habitacion.save(update_fields=['estado'])

publicar_evento_habitacion(
    habitacion,
    estado_anterior=estado_anterior,
    evento=EVENTO_HABITACION_OCUPADA,
)
```

El publicador usa internamente:

```python
transaction.on_commit(...)
```

Por eso el evento se envía solo cuando la transacción se confirma.

---

## 10.1 Eventos disponibles

Importar desde `core.events`:

```python
EVENTO_HABITACION_OCUPADA
EVENTO_HABITACION_EN_LIMPIEZA
EVENTO_HABITACION_DISPONIBLE
EVENTO_HABITACION_EN_MANTENIMIENTO
```

Uso esperado:

| Evento | Cuándo usarlo |
|---|---|
| `HABITACION_OCUPADA` | Después de check-in confirmado |
| `HABITACION_EN_LIMPIEZA` | Después de checkout confirmado |
| `HABITACION_DISPONIBLE` | Después de housekeeping confirmado |
| `HABITACION_EN_MANTENIMIENTO` | Después de enviar habitación a mantenimiento |

---

## 10.2 Payload enviado al frontend

El backend enviará al WebSocket:

```json
{
  "tipo": "HABITACION_OCUPADA",
  "hotel_id": 1,
  "habitacion_id": 10,
  "numero": "101",
  "piso": 1,
  "tipo_habitacion": "Matrimonial",
  "estado_anterior": "DISPONIBLE",
  "estado_nuevo": "OCUPADA",
  "actualizado_en": "2026-07-02T15:00:00-05:00"
}
```

Regla para frontend:
- El frontend no decide el estado.
- El frontend solo pinta el estado confirmado por backend.
- Si llega un evento repetido, debe actualizar la tarjeta de forma idempotente.

---

# 11. Cómo Debe Consumirlo El Frontend

Ejemplo base:

```javascript
const hotelId = 1;
const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${scheme}://${window.location.host}/ws/hoteles/${hotelId}/habitaciones/`);

socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    actualizarTarjetaHabitacion(payload);
};
```

Reglas:
- Usar `wss` cuando el sitio use HTTPS.
- Reconectar con espera progresiva si se corta la conexión.
- No duplicar listeners al recargar componentes.
- No cambiar estados por cuenta propia.
- Mostrar errores si la conexión no está disponible.

---

# 12. Qué Debe Hacer Cada Responsable

## 12.1 Luis — Reservas y huéspedes

Debe:
- crear `ReservaService`,
- crear `HuespedService`,
- crear excepciones específicas heredando de `core.exceptions`,
- usar disponibilidad centralizada cuando esté lista,
- evitar duplicar reglas de solapamiento en serializers y views,
- migrar modelos a `ModeloBase` cuando se planifique la migración del módulo.

No debe:
- crear otro sistema de errores,
- calcular disponibilidad por su cuenta si ya existe servicio central,
- dejar reglas críticas dentro de serializers.

---

## 12.2 Daniel — Habitaciones, estancias y housekeeping

Debe:
- crear `EstanciaService`,
- crear `HousekeepingService`,
- usar `transaction.atomic` en check-in y checkout,
- usar `publicar_evento_habitacion()` después de cambiar estados,
- lanzar excepciones de dominio para transiciones inválidas.

Eventos esperados:
- check-in: `EVENTO_HABITACION_OCUPADA`,
- checkout: `EVENTO_HABITACION_EN_LIMPIEZA`,
- housekeeping: `EVENTO_HABITACION_DISPONIBLE`,
- mantenimiento: `EVENTO_HABITACION_EN_MANTENIMIENTO`.

No debe:
- enviar eventos antes del commit,
- permitir cambios manuales que rompan estancias activas,
- calcular deuda financiera dentro de `EstanciaService`.

---

## 12.3 Carlos — Facturación

Debe:
- crear `TarifaService`,
- crear `FolioService`,
- crear `CargoService`,
- crear `PagoService`,
- exponer un método estable para checkout, por ejemplo `validar_sin_deuda(estancia)`,
- lanzar excepciones financieras heredando de `core.exceptions`.

No debe:
- duplicar cálculo de tarifa en reservas,
- cerrar folios sin validar pagos,
- permitir cargos inválidos o negativos.

---

## 12.4 Yefry — Plano, dashboard y reportes

Debe:
- consumir `/ws/hoteles/<hotel_id>/habitaciones/`,
- actualizar tarjetas del plano con el payload recibido,
- aplicar colores según `estado_nuevo`,
- implementar reconexión controlada,
- usar datos reales de servicios para dashboard y reportes.

No debe:
- inferir estados en JavaScript,
- simular cambios no confirmados por backend,
- contar reservas impagas como ingresos cobrados.

---

# 13. Orden Recomendado De Integración

Como líder técnico, integrar en este orden:

1. Fase 0 infraestructura.
2. Servicio de disponibilidad centralizado.
3. Servicios de reservas y huéspedes.
4. Servicios de estancias y housekeeping.
5. Servicios de folio, cargos y pagos.
6. Eventos WebSocket conectados a check-in, checkout y housekeeping.
7. Cliente WebSocket del plano.
8. Reportes y dashboard usando servicios.
9. Migración progresiva de modelos a `ModeloBase` por módulo.
10. Estabilización del flujo completo.

Regla importante:
- No hacer migración masiva de todos los modelos sin coordinar.
- Cada módulo debe migrar sus modelos con pruebas propias.

---

# 14. Flujo Git Para El Equipo

La rama con esta infraestructura debe integrarse primero a `develop` o quedar como base obligatoria.

Flujo recomendado:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/mi-modulo
```


Si ya está integrada en `develop`:

```bash
git checkout feature/mi-modulo
git merge origin/develop
```

Antes de abrir PR:

```bash
git status
python manage.py check
python manage.py test
```

Con Docker:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
```

---

# 15. Checklist Para Pull Requests

El líder técnico debe revisar este checklist antes de aprobar.

## 15.1 Arquitectura

- La lógica crítica está en servicios.
- Las views están delgadas.
- Los serializers no contienen reglas de negocio complejas.
- No se duplican cálculos entre API y templates.
- No se creó una infraestructura paralela a `core`.

## 15.2 Excepciones

- Las reglas de negocio lanzan excepciones de dominio.
- Las excepciones heredan de `core.exceptions`.
- No se usan `ValueError` o `Exception` genéricos para reglas nuevas.
- Los mensajes son claros para usuario final.
- La API responde con formato uniforme.

## 15.3 Transacciones

- Las operaciones multi-entidad usan `transaction.atomic`.
- No quedan estados parciales si ocurre error.
- Los eventos WebSocket se emiten después del commit.

## 15.4 ModeloBase y datos

- Los modelos nuevos heredan de `ModeloBase` cuando corresponde.
- No se usa borrado físico para datos históricos.
- Se revisaron constraints únicos antes de aplicar soft delete.
- Las migraciones son pequeñas y revisables.
- No hay migraciones conflictivas entre módulos.

## 15.5 WebSockets

- El evento se publica desde backend, no desde frontend.
- El payload respeta el contrato definido.
- El grupo usa `hotel_<hotel_id>_habitaciones`.
- El usuario debe estar autenticado.
- El rol está validado.
- El frontend no infiere estados.

## 15.6 Docker y entorno

- `docker compose config` no falla.
- `docker compose up --build` levanta `web`, `db` y `redis`.
- `python manage.py check` pasa.
- No se subió `.env`.
- `.env.example` está actualizado si se agregaron variables nuevas.

## 15.7 Pruebas funcionales mínimas

- Flujo normal probado.
- Al menos un rechazo crítico probado.
- API y template usan el mismo servicio si ambos existen.
- Los permisos se validan en backend.
- No se rompió el flujo principal del hotel.

---

# 16. Definición De Terminado Para Cada Módulo

Una tarea no está terminada solo porque la pantalla funciona.

Debe cumplir:
- servicio implementado,
- view delgada,
- excepciones de dominio,
- transacciones donde corresponde,
- permisos en backend,
- errores visibles para usuario,
- API y templates reutilizan lógica,
- pruebas manuales o automatizadas,
- sin duplicar infraestructura,
- sin romper Docker.

---

# 17. Errores Comunes A Evitar

## 17.1 Duplicar disponibilidad

Incorrecto:

```python
Habitacion.objects.filter(estado='DISPONIBLE')
```

Esto no alcanza porque ignora reservas solapadas, estancias activas y capacidad.

Correcto:
- usar el servicio central de disponibilidad cuando esté integrado.

---

## 17.2 Enviar eventos WebSocket desde la view

Incorrecto:

```python
def post(request):
    habitacion.estado = EstadoHabitacion.OCUPADA
    habitacion.save()
    enviar_websocket()
```

Correcto:
- cambiar estado dentro del servicio,
- usar transacción,
- llamar `publicar_evento_habitacion()`.

---

## 17.3 Usar errores genéricos

Incorrecto:

```python
raise Exception('No se puede')
```

Correcto:

```python
raise ReservaNoModificable()
```

---

## 17.4 Crear lógica distinta para API y templates

Incorrecto:
- API calcula una cosa,
- template calcula otra.

Correcto:
- ambos llaman al mismo servicio.

---

# 18. Contrato Mínimo Para Eventos De Habitación

Todo evento de habitación debe incluir:

| Campo | Descripción |
|---|---|
| `tipo` | Tipo de evento |
| `hotel_id` | Hotel afectado |
| `habitacion_id` | Habitación afectada |
| `numero` | Número visible de habitación |
| `piso` | Piso |
| `tipo_habitacion` | Nombre del tipo de habitación |
| `estado_anterior` | Estado antes del cambio |
| `estado_nuevo` | Estado confirmado |
| `actualizado_en` | Fecha/hora del evento |

No agregar campos al payload sin coordinar con frontend.

---

# 19. Responsabilidad Del Líder Técnico

El líder técnico debe:
- mantener esta infraestructura como fuente única,
- aprobar contratos de servicios,
- revisar migraciones,
- revisar permisos,
- validar Docker,
- evitar duplicación de reglas,
- resolver conflictos entre módulos,
- exigir checklist antes de aprobar PRs,
- asegurar que el flujo completo siga funcionando.

El líder no debe implementar todos los módulos. Cada integrante es responsable de su dominio.

---

# 20. Comandos Útiles

Validar Docker Compose:

```bash
docker compose config
```

Levantar todo:

```bash
docker compose up --build
```

Ejecutar checks:

```bash
docker compose exec web python manage.py check
```

Ver migraciones pendientes:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

Ejecutar tests:

```bash
docker compose exec web python manage.py test
```

Ver logs del backend:

```bash
docker compose logs -f web
```

Ver logs de Redis:

```bash
docker compose logs -f redis
```

---

# 21. Resumen Para Compartir Al Equipo

Mensaje sugerido:

```text
Equipo, la Fase 0 de infraestructura ya está lista.

Desde ahora toda rama debe basarse en esta infraestructura.

Puntos obligatorios:
- usar core.ModeloBase para modelos nuevos o migrados,
- usar core.exceptions para errores de dominio,
- mover reglas de negocio a services.py,
- usar transaction.atomic en operaciones multi-entidad,
- emitir eventos de habitación con core.events.publicar_evento_habitacion,
- no duplicar disponibilidad, tarifas, saldo ni WebSockets,
- validar con docker compose y manage.py check antes de PR.

No se aceptarán PRs que creen infraestructura paralela o dejen reglas críticas dentro de views.
```
