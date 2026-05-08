# API Documentation — HotelSys

Este documento describe la estructura inicial de endpoints y servicios internos del sistema HotelSys.

Aunque el proyecto utiliza principalmente Django MVT, se documentan endpoints y flujos para:
- integración frontend,
- futuras APIs REST,
- AJAX,
- dashboards,
- y posibles integraciones externas.

---

# 1. Base URL

## Desarrollo

```text
http://localhost:8000
```

---

# 2. Formato General

## Convenciones

| Elemento | Convención |
|---|---|
| URLs | snake_case o kebab-case consistente |
| Métodos HTTP | RESTful |
| Respuestas | JSON |
| Fechas | ISO 8601 |
| Moneda | Decimal |

---

# 3. Autenticación

Actualmente el sistema utiliza:

- Django Authentication
- Session Authentication

---

# Roles soportados

| Rol | Descripción |
|---|---|
| ADMIN | Acceso total |
| RECEPCIONISTA | Operación hotelera |
| HOUSEKEEPING | Gestión limpieza |
| AUDITOR | Lectura de reportes |

---

# 4. Endpoints Generales

| Módulo | Base URL |
|---|---|
| Auth | `/auth/` |
| Hotels | `/hotels/` |
| Rooms | `/rooms/` |
| Guests | `/guests/` |
| Reservations | `/reservations/` |
| Stays | `/stays/` |
| Billing | `/billing/` |
| Reports | `/reports/` |

---

# 5. Auth APIs

---

## Login

### Endpoint

```http
POST /auth/login/
```

---

## Request

```json
{
  "username": "admin",
  "password": "123456"
}
```

---

## Response

```json
{
  "success": true,
  "message": "Login successful"
}
```

---

# Logout

### Endpoint

```http
POST /auth/logout/
```

---

# 6. Hotels APIs

---

## List Hotels

### Endpoint

```http
GET /hotels/
```

---

## Create Hotel

### Endpoint

```http
POST /hotels/create/
```

---

## Request

```json
{
  "nombre": "HotelSys Palace",
  "ruc": "20481234567",
  "direccion": "Av. Principal 123",
  "estrellas": 4,
  "telefono": "074555555"
}
```

---

# 7. Rooms APIs

---

## List Rooms

### Endpoint

```http
GET /rooms/
```

---

## Room Availability

### Endpoint

```http
GET /rooms/available/
```

---

## Query Params

| Parámetro | Tipo |
|---|---|
| fecha_entrada | date |
| fecha_salida | date |
| hotel_id | integer |
| tipo_id | integer |

---

## Example

```http
GET /rooms/available/?fecha_entrada=2026-05-10&fecha_salida=2026-05-12
```

---

## Response

```json
[
  {
    "id": 1,
    "numero": "101",
    "tipo": "Simple",
    "estado": "DISPONIBLE"
  }
]
```

---

# 8. Guests APIs

---

## List Guests

### Endpoint

```http
GET /guests/
```

---

## Create Guest

### Endpoint

```http
POST /guests/create/
```

---

## Request

```json
{
  "tipo_doc": "DNI",
  "num_doc": "71234567",
  "nombres": "Carlos",
  "apellidos": "Ramirez Torres",
  "email": "carlos@mail.com",
  "telefono": "987654321",
  "nacionalidad": "Peruana"
}
```

---

# 9. Reservations APIs

---

## List Reservations

### Endpoint

```http
GET /reservations/
```

---

## Create Reservation

### Endpoint

```http
POST /reservations/create/
```

---

## Request

```json
{
  "hotel": 1,
  "huesped": 1,
  "habitacion": 1,
  "fecha_entrada": "2026-05-10",
  "fecha_salida": "2026-05-12",
  "num_adultos": 2,
  "origen": "WEB"
}
```

---

## Response

```json
{
  "success": true,
  "message": "Reserva creada correctamente"
}
```

---

# Reservation Validation Rules

## Validaciones

- fecha_salida > fecha_entrada
- habitación disponible
- no solapamiento
- habitación pertenece al hotel

---

# Cancel Reservation

### Endpoint

```http
POST /reservations/{id}/cancel/
```

---

# Check Reservation Availability

### Endpoint

```http
GET /reservations/check-availability/
```

---

# Query Params

| Parámetro | Tipo |
|---|---|
| habitacion_id | integer |
| fecha_entrada | date |
| fecha_salida | date |

---

# 10. Stays APIs

---

## Check-in

### Endpoint

```http
POST /stays/checkin/
```

---

## Request

```json
{
  "reserva_id": 1
}
```

---

## Response

```json
{
  "success": true,
  "message": "Check-in realizado correctamente"
}
```

---

# Reglas de Check-in

- reserva confirmada
- habitación disponible
- habitación no mantenimiento
- habitación no limpieza

---

# Checkout

### Endpoint

```http
POST /stays/checkout/
```

---

## Request

```json
{
  "estancia_id": 1
}
```

---

## Response

```json
{
  "success": true,
  "message": "Checkout realizado correctamente"
}
```

---

# Reglas de Checkout

- folio pagado
- estancia activa
- cálculo final realizado

---

# 11. Billing APIs

---

## List Folios

### Endpoint

```http
GET /billing/folios/
```

---

## Get Folio Detail

### Endpoint

```http
GET /billing/folios/{id}/
```

---

## Add Charge

### Endpoint

```http
POST /billing/charges/create/
```

---

## Request

```json
{
  "estancia": 1,
  "concepto": "Minibar",
  "monto": 35.50,
  "tipo": "MINIBAR"
}
```

---

## Response

```json
{
  "success": true,
  "message": "Cargo registrado"
}
```

---

# Calculate Folio

### Endpoint

```http
POST /billing/folios/{id}/calculate/
```

---

## Response

```json
{
  "subtotal": 300,
  "igv": 54,
  "total": 354
}
```

---

# 12. Housekeeping APIs

---

## Rooms in Cleaning

### Endpoint

```http
GET /housekeeping/rooms/
```

---

## Mark Room as Available

### Endpoint

```http
POST /housekeeping/rooms/{id}/available/
```

---

# Reglas

- solo habitaciones LIMPIEZA
- housekeeping no modifica reservas
- housekeeping no modifica folios

---

# 13. Reports APIs

---

## Occupancy Report

### Endpoint

```http
GET /reports/occupancy/
```

---

## Revenue Report

### Endpoint

```http
GET /reports/revenue/
```

---

## Dashboard KPIs

### Endpoint

```http
GET /reports/dashboard/
```

---

## Example Response

```json
{
  "ocupacion": 72,
  "habitaciones_ocupadas": 18,
  "habitaciones_disponibles": 7,
  "revenue": 15420.50
}
```

---

# 14. HTTP Status Codes

| Código | Uso |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 500 | Internal error |

---

# 15. Error Response Format

## Ejemplo

```json
{
  "success": false,
  "errors": {
    "fecha_salida": [
      "La fecha de salida debe ser mayor."
    ]
  }
}
```

---

# 16. Reglas Técnicas API

## Recomendaciones

- Validaciones críticas en modelos
- Utilizar `clean()`
- Utilizar `full_clean()`
- Evitar lógica compleja en views
- Reutilizar servicios

---

# 17. Futuras Mejoras

El sistema fue diseñado considerando futuras integraciones:

- Django REST Framework
- JWT Authentication
- WebSockets
- Mobile apps
- APIs externas
- Payment gateways

---

# 18. Consideraciones Importantes

Actualmente:
- el sistema utiliza principalmente Django Templates,
- las APIs descritas representan endpoints internos y futura expansión REST.

---

# 19. Responsabilidad Técnica

Toda modificación de:
- endpoints,
- contratos JSON,
- validaciones,
- respuestas API,

debe coordinarse con el líder técnico antes de integrarse.