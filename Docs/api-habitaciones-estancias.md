# API de Habitaciones y Estancias

Responsable: Daniel Erick Escribano Macalopu

Este documento define las APIs principales del modulo de Habitaciones y Estancias, alineadas con la guia minima del proyecto de Gestion Hotelera.

El enfoque del modulo no es exponer CRUD completo de habitaciones o tipos de habitacion, sino cubrir el flujo operativo del hotel:

```text
disponibilidad
↓
check-in
↓
estancia activa
↓
checkout
↓
housekeeping
↓
habitacion disponible
```

Los endpoints de administracion como creacion de tipos de habitacion, edicion de habitaciones o listados generales no se exponen en esta API para evitar duplicidad y mantener el modulo enfocado en el flujo requerido.

---

## Base URL

```text
http://localhost:8000/api/v1/
```

Todos los endpoints requieren autenticacion mediante JWT o sesion Django, segun el consumidor.

Roles principales:

```text
ADMIN
RECEPCIONISTA
HOUSEKEEPING
```

---

## APIs Principales Del Modulo

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/v1/habitaciones/disponibles/` | Consultar habitaciones disponibles por fechas y tipo |
| `POST` | `/api/v1/reservas/<reserva_id>/checkin/` | Realizar check-in de una reserva confirmada |
| `GET` | `/api/v1/estancias/<estancia_id>/` | Consultar detalle operativo de una estancia |
| `POST` | `/api/v1/estancias/<estancia_id>/checkout/` | Realizar checkout de una estancia activa |
| `PATCH` | `/api/v1/habitaciones/<habitacion_id>/housekeeping/` | Actualizar estado de limpieza de una habitacion |

---

## 1. Habitaciones Disponibles

```text
GET /api/v1/habitaciones/disponibles/?fecha_entrada=&fecha_salida=&tipo=
```

### Uso

Permite consultar que habitaciones estan libres para un rango de fechas.

Se utiliza principalmente en:

- Nueva reserva.
- Calendario de reservas.
- Plano del hotel.

### Flujo Esperado

```text
Recepcionista selecciona fechas y tipo de habitacion
↓
Frontend consulta habitaciones disponibles
↓
Sistema excluye habitaciones ocupadas, en mantenimiento o con reservas solapadas
↓
Frontend muestra solo habitaciones asignables
```

### Parametros

| Parametro | Descripcion |
|---|---|
| `fecha_entrada` | Fecha inicial de la reserva |
| `fecha_salida` | Fecha final de la reserva |
| `tipo` | Tipo de habitacion opcional |

### Validaciones Principales

- `fecha_salida` debe ser mayor a `fecha_entrada`.
- No debe existir reserva activa solapada.
- La habitacion no debe estar en `OCUPADA`, `LIMPIEZA` o `MANTENIMIENTO`.

### Resultado Esperado

Lista de habitaciones disponibles para ser asignadas a una reserva.

---

## 2. Check-In De Reserva

```text
POST /api/v1/reservas/<reserva_id>/checkin/
```

### Uso

Convierte una reserva confirmada en una estancia activa.

Se utiliza principalmente en:

- Pantalla de check-in.
- Panel de reservas del dia.
- Detalle de reserva.

### Flujo Esperado

```text
Reserva CONFIRMADA
↓
Recepcionista confirma check-in
↓
Sistema crea Estancia ACTIVA
↓
Sistema crea Folio ABIERTO
↓
Reserva pasa a CHECKIN
↓
Habitacion pasa a OCUPADA
```

### Validaciones Principales

- La reserva debe estar `CONFIRMADA`.
- La reserva no debe tener estancia previa.
- La fecha actual debe estar dentro del rango de la reserva.
- La habitacion debe estar `DISPONIBLE`.
- No se permite check-in en habitaciones en `LIMPIEZA` o `MANTENIMIENTO`.

### Resultado Esperado

Se crea una estancia activa y se abre el folio asociado para la cuenta del huesped.

---

## 3. Detalle De Estancia

```text
GET /api/v1/estancias/<estancia_id>/
```

### Uso

Permite consultar la informacion operativa de una estancia especifica.

Se utiliza principalmente en:

- Detalle de estancia.
- Folio del huesped.
- Pantalla de checkout.
- Panel de estancias activas.

### Informacion Esperada

```text
id de estancia
reserva asociada
huesped
habitacion
hotel
fecha_checkin
fecha_checkout
precio_final
estado
```

### Resultado Esperado

El frontend puede mostrar el estado actual de la estancia y usar esa informacion para continuar con folio, cargos o checkout.

---

## 4. Checkout De Estancia

```text
POST /api/v1/estancias/<estancia_id>/checkout/
```

### Uso

Finaliza una estancia activa cuando el huesped termina su estadia.

Se utiliza principalmente en:

- Folio del huesped.
- Panel de salidas del dia.
- Detalle de estancia.

### Flujo Esperado

```text
Estancia ACTIVA
↓
Sistema valida folio pagado o cerrado
↓
Recepcionista realiza checkout
↓
Estancia pasa a FINALIZADA
↓
Reserva pasa a FINALIZADA
↓
Habitacion pasa a LIMPIEZA
```

### Validaciones Principales

- La estancia debe estar `ACTIVA`.
- El folio debe estar `PAGADO` o `CERRADO`.
- No se permite checkout con deuda pendiente.

### Resultado Esperado

La estancia queda finalizada y la habitacion pasa a limpieza para continuar con housekeeping.

---

## 5. Housekeeping De Habitacion

```text
PATCH /api/v1/habitaciones/<habitacion_id>/housekeeping/
```

### Uso

Permite actualizar el estado operativo de una habitacion desde housekeeping.

Se utiliza principalmente en:

- Pantalla de housekeeping.
- Plano del hotel.
- Panel de limpieza por piso.

### Payload Esperado

Marcar habitacion como disponible:

```json
{
  "estado": "DISPONIBLE"
}
```

Enviar habitacion a mantenimiento:

```json
{
  "estado": "MANTENIMIENTO"
}
```

### Flujo Esperado

```text
Checkout realizado
↓
Habitacion queda en LIMPIEZA
↓
Housekeeping realiza limpieza
↓
Sistema actualiza estado
↓
Habitacion queda DISPONIBLE
```

### Validaciones Principales

- Solo se puede liberar una habitacion en `LIMPIEZA` o `MANTENIMIENTO`.
- No se puede enviar a mantenimiento una habitacion `OCUPADA`.
- Housekeeping no modifica reservas, folios ni tarifas.

### Resultado Esperado

La habitacion vuelve al inventario disponible o queda marcada como mantenimiento segun corresponda.

---

## Relacion Con Las Pantallas Del Sistema

| API | Pantalla donde se usa |
|---|---|
| `GET /api/v1/habitaciones/disponibles/` | Nueva reserva, calendario, plano del hotel |
| `POST /api/v1/reservas/<reserva_id>/checkin/` | Check-in, panel de reservas, detalle de reserva |
| `GET /api/v1/estancias/<estancia_id>/` | Detalle de estancia, folio, checkout |
| `POST /api/v1/estancias/<estancia_id>/checkout/` | Folio, salidas del dia, detalle de estancia |
| `PATCH /api/v1/habitaciones/<habitacion_id>/housekeeping/` | Housekeeping, plano del hotel |

---

## Flujo Completo Cubierto

```text
1. Nueva reserva consulta habitaciones disponibles.
2. La reserva se confirma desde el modulo de reservas.
3. Recepcion realiza check-in.
4. El sistema crea estancia activa y folio abierto.
5. Se consulta la estancia para seguimiento operativo.
6. Facturacion gestiona cargos y pago del folio.
7. Recepcion realiza checkout.
8. La habitacion pasa a limpieza.
9. Housekeeping marca la habitacion como disponible.
```

---

## Validaciones Realizadas

Comandos recomendados antes de entregar cambios:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test estancias facturacion
docker compose exec web python manage.py spectacular --file NUL --validate
```

Resultado esperado:

- `manage.py check` sin errores.
- Tests del flujo de estancia y folio aprobados.
- Schema OpenAPI sin errores.
- Pueden persistir warnings `W042` de `DEFAULT_AUTO_FIELD`, existentes en el proyecto.
