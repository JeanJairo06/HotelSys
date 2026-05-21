# API de Habitaciones y Estancias

Responsable: Daniel Erick Escribano Macalopu

Este documento resume los endpoints REST agregados para el modulo de:

- tipos de habitacion,
- habitaciones,
- estancias,
- check-in,
- checkout,
- limpieza / housekeeping.

La documentacion general de la API se mantiene en `Docs/api.md`. Este archivo separa el detalle de habitaciones y estancias para evitar conflictos mientras otros integrantes agregan sus propios endpoints.

---

## Base URL

```text
http://localhost:8000/api/v1/
```

Todos los endpoints requieren autenticacion mediante JWT o sesion Django, segun el consumidor.

---

## Tipos de Habitacion

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/v1/habitaciones/tipos/` | Listar tipos de habitacion |
| `POST` | `/api/v1/habitaciones/tipos/` | Crear tipo de habitacion |
| `GET` | `/api/v1/habitaciones/tipos/<id>/` | Detalle de tipo de habitacion |
| `PUT/PATCH` | `/api/v1/habitaciones/tipos/<id>/` | Actualizar tipo de habitacion |

Permisos:

```text
GET: ADMIN, RECEPCIONISTA
POST/PUT/PATCH: ADMIN
```

---

## Habitaciones

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/v1/habitaciones/` | Listar habitaciones |
| `POST` | `/api/v1/habitaciones/` | Crear habitacion |
| `GET` | `/api/v1/habitaciones/<id>/` | Detalle de habitacion |
| `PUT/PATCH` | `/api/v1/habitaciones/<id>/` | Actualizar habitacion |
| `POST` | `/api/v1/habitaciones/<id>/estado/` | Cambiar estado manual de habitacion |

Filtros disponibles en listado:

```text
hotel
tipo
estado
piso
```

Busqueda:

```text
numero
hotel__nombre
tipo__nombre
```

Permisos:

```text
GET: ADMIN, RECEPCIONISTA
POST/PUT/PATCH: ADMIN
cambio de estado: ADMIN, RECEPCIONISTA
```

El cambio manual de estado usa el servicio:

```text
cambiar_estado_manual()
```

Este servicio evita liberar manualmente habitaciones ocupadas o con estancia activa.

---

## Estancias

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/v1/estancias/` | Listar estancias |
| `GET` | `/api/v1/estancias/<id>/` | Detalle de estancia |

Filtros disponibles:

```text
estado
habitacion
reserva
```

Permisos:

```text
ADMIN, RECEPCIONISTA
```

---

## Check-in

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/v1/estancias/checkin/` | Listar reservas confirmadas disponibles para check-in |
| `POST` | `/api/v1/estancias/checkin/<reserva_id>/` | Realizar check-in |

El endpoint de listado consulta reservas confirmadas solo para ejecutar el flujo operativo de check-in. No implementa CRUD de reservas.

El check-in usa el servicio:

```text
registrar_checkin()
```

Validaciones principales:

- La reserva debe estar `CONFIRMADA`.
- La reserva no debe tener estancia previa.
- La fecha actual debe estar dentro del rango de la reserva.
- La habitacion debe estar `DISPONIBLE`.

Al realizar check-in:

- Se crea una estancia.
- La reserva pasa a `CHECKIN`.
- La habitacion pasa a `OCUPADA`.

---

## Checkout

| Metodo | Endpoint | Uso |
|---|---|---|
| `POST` | `/api/v1/estancias/<estancia_id>/checkout/` | Realizar checkout |

El checkout usa el servicio:

```text
registrar_checkout()
```

Validaciones principales:

- La estancia debe estar `ACTIVA`.
- Si existe folio, debe estar `PAGADO` o `CERRADO`.

Al realizar checkout:

- La estancia pasa a `FINALIZADA`.
- La reserva pasa a `FINALIZADA`.
- La habitacion pasa a `LIMPIEZA`.

---

## Limpieza / Housekeeping

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/v1/limpieza/` | Listar habitaciones en limpieza o mantenimiento |
| `POST` | `/api/v1/limpieza/<habitacion_id>/disponible/` | Marcar habitacion como disponible |
| `POST` | `/api/v1/limpieza/<habitacion_id>/mantenimiento/` | Enviar habitacion a mantenimiento |

Filtros disponibles:

```text
piso
estado
```

Permisos:

```text
ADMIN, HOUSEKEEPING
```

Servicios utilizados:

```text
marcar_disponible()
marcar_mantenimiento()
```

Reglas principales:

- Solo habitaciones en limpieza o mantenimiento aparecen en el panel.
- Una habitacion ocupada no puede enviarse a mantenimiento.
- Housekeeping no modifica reservas, folios ni tarifas.

---

## Archivos Modificados

```text
api/serializers.py
api/views.py
api/urls.py
```

Archivo de documentacion:

```text
Docs/api-habitaciones-estancias.md
```

---

## Validaciones Realizadas

Comandos ejecutados:

```bash
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py spectacular --file NUL --validate
```

Resultado:

- `manage.py check` sin errores.
- Schema OpenAPI sin errores.
- Persisten warnings `W042` de `DEFAULT_AUTO_FIELD`, existentes en el proyecto.

Prueba con Docker y usuario autenticado:

```text
/api/v1/habitaciones/tipos/ -> 200 application/json
/api/v1/habitaciones/       -> 200 application/json
/api/v1/estancias/          -> 200 application/json
/api/v1/estancias/checkin/  -> 200 application/json
/api/v1/limpieza/           -> 200 application/json
```
