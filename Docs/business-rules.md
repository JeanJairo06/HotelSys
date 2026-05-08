# Reglas de Negocio — HotelSys

Este documento define las reglas funcionales obligatorias del Sistema de Gestión Hotelera.  
Toda funcionalidad desarrollada debe respetar estas reglas.

---

# 1. Flujo Principal del Sistema

El flujo operativo principal del sistema es:

```text
Reserva
↓
Check-in
↓
Estancia
↓
Cargos / Folio
↓
Checkout
↓
Limpieza
↓
Disponible
```

---

# 2. Reglas de Habitaciones

## 2.1 Estados válidos

Una habitación solo puede tener uno de los siguientes estados:

| Estado | Descripción |
|---|---|
| DISPONIBLE | Puede ser reservada o asignada |
| OCUPADA | Tiene una estancia activa |
| LIMPIEZA | Requiere limpieza después del checkout |
| MANTENIMIENTO | No puede usarse temporalmente |

## 2.2 Restricciones

- No se puede hacer check-in en una habitación en estado `LIMPIEZA`.
- No se puede hacer check-in en una habitación en estado `MANTENIMIENTO`.
- No se puede asignar una habitación `OCUPADA`.
- Al realizar checkout, la habitación debe pasar automáticamente a `LIMPIEZA`.
- Cuando housekeeping termina la limpieza, la habitación pasa de `LIMPIEZA` a `DISPONIBLE`.

---

# 3. Reglas de Reservas

## 3.1 Fechas

- La fecha de salida debe ser mayor que la fecha de entrada.
- Una reserva debe tener fecha de entrada y fecha de salida.
- El número de noches se calcula como:

```text
fecha_salida - fecha_entrada
```

## 3.2 Solapamiento

Una habitación no puede tener dos reservas activas con fechas solapadas.

Existe solapamiento cuando:

```text
reserva_existente.fecha_entrada < nueva_reserva.fecha_salida
AND
reserva_existente.fecha_salida > nueva_reserva.fecha_entrada
```

No deben considerarse como conflicto las reservas en estado:

- `CANCELADA`
- `FINALIZADA`

## 3.3 Estado de reserva

Estados permitidos:

| Estado | Descripción |
|---|---|
| PENDIENTE | Reserva registrada, aún no confirmada |
| CONFIRMADA | Reserva validada |
| CANCELADA | Reserva anulada |
| CHECKIN | Reserva convertida en estancia |
| FINALIZADA | Reserva cerrada después del checkout |

---

# 4. Reglas de Tarifas

- El precio de una reserva debe calcularse usando la tarifa vigente.
- La tarifa se determina por:
  - tipo de habitación,
  - fecha de entrada,
  - fecha de salida.
- Si una reserva cubre varios días, debe calcularse el precio por noche.
- Si existen tarifas por temporada, debe aplicarse la tarifa correspondiente a cada noche.
- Si no existe tarifa vigente, debe usarse el `precio_base` del tipo de habitación.

---

# 5. Reglas de Check-In

Para realizar check-in:

- La reserva debe estar `CONFIRMADA`.
- La habitación debe estar `DISPONIBLE`.
- La habitación no debe estar en `LIMPIEZA`.
- La habitación no debe estar en `MANTENIMIENTO`.
- Se debe crear una `Estancia`.
- La reserva cambia a estado `CHECKIN`.
- La habitación cambia a estado `OCUPADA`.

---

# 6. Reglas de Estancia

- Una estancia se crea únicamente a partir de una reserva válida.
- Una reserva solo puede tener una estancia.
- Una estancia activa representa ocupación real.
- Una estancia finalizada ya no debe permitir nuevos cargos.
- La estancia debe registrar:
  - fecha de check-in,
  - fecha de checkout,
  - precio final,
  - estado.

---

# 7. Reglas de Cargos

- Los cargos pertenecen a una estancia.
- Todo cargo debe tener:
  - concepto,
  - monto,
  - fecha,
  - tipo.
- El monto de un cargo no puede ser negativo.
- Los tipos de cargo permitidos son:
  - HABITACION
  - RESTAURANTE
  - LAVANDERIA
  - MINIBAR
  - PENALIDAD
  - OTRO

---

# 8. Reglas de Folio

- Cada estancia debe tener un folio.
- El folio consolida todos los cargos de la estancia.
- El subtotal es la suma de los cargos.
- El IGV se calcula sobre el subtotal.
- El total se calcula como:

```text
total = subtotal + igv
```

- No se puede realizar checkout si el folio tiene deuda pendiente.
- Un folio pagado puede cerrarse.
- Un folio cerrado no debe modificarse.

---

# 9. Reglas de Checkout

Para realizar checkout:

- La estancia debe estar `ACTIVA`.
- El folio debe estar `PAGADO` o sin deuda pendiente.
- Se calcula el folio final.
- La estancia cambia a `FINALIZADA`.
- La reserva cambia a `FINALIZADA`.
- La habitación cambia automáticamente a `LIMPIEZA`.

---

# 10. Reglas de Housekeeping

- Solo habitaciones en estado `LIMPIEZA` pueden marcarse como listas.
- Al marcar una habitación como lista, cambia a `DISPONIBLE`.
- Las habitaciones en `MANTENIMIENTO` no pueden pasar directamente a `DISPONIBLE` sin intervención administrativa.
- Housekeeping no debe modificar reservas, folios ni tarifas.

---

# 11. Reglas de Reportes

## 11.1 Ocupación diaria

La tasa de ocupación se calcula como:

```text
habitaciones_ocupadas / total_habitaciones * 100
```

## 11.2 Revenue

El revenue se calcula considerando:

- cargos de habitación,
- cargos adicionales,
- folios pagados.

## 11.3 Reporte por tipo de habitación

Debe agrupar:

- número de habitaciones,
- habitaciones ocupadas,
- habitaciones disponibles,
- ingresos por tipo.

---

# 12. Reglas de Seguridad y Roles

## Roles permitidos

| Rol | Permisos |
|---|---|
| ADMIN | Acceso total |
| RECEPCIONISTA | Reservas, check-in, checkout y huéspedes |
| HOUSEKEEPING | Gestión de limpieza |
| AUDITOR | Solo lectura de reportes |

## Restricciones

- Solo `ADMIN` puede gestionar usuarios, hoteles, tarifas y configuración.
- `RECEPCIONISTA` no debe modificar tarifas.
- `HOUSEKEEPING` solo debe cambiar habitaciones de `LIMPIEZA` a `DISPONIBLE`.
- Ningún usuario sin autenticación debe acceder al sistema.

---

# 13. Reglas Técnicas

- Las validaciones críticas deben implementarse en los modelos usando `clean()`.
- Los modelos deben ejecutar `full_clean()` antes de guardar cuando corresponda.
- Las relaciones críticas deben usar `on_delete=models.PROTECT`.
- Los registros históricos o dependientes pueden usar `CASCADE`.
- No se debe eliminar información crítica como reservas, estancias o folios.
- Se recomienda manejar cancelaciones mediante estados, no eliminando registros.

---

# 14. Reglas de Integridad de Datos

- No debe existir una habitación con el mismo número dentro del mismo hotel.
- No debe existir un huésped duplicado con el mismo documento.
- No debe existir más de una estancia por reserva.
- No debe existir más de un folio por estancia.
- No debe existir reserva con fechas inválidas.
- No debe existir cargo con monto negativo.
- No debe existir tarifa con fecha final menor o igual a fecha inicial.

---

# 15. Criterios de Aceptación Relacionados

El sistema debe cumplir como mínimo:

- Plano del hotel con colores por estado.
- Reserva con cálculo de tarifa vigente.
- Check-in y checkout con folio consolidado.
- Validación de deuda antes del checkout.
- Flujo visible: `CHECKOUT → LIMPIEZA → DISPONIBLE`.
- Reporte de ocupación.
- Revenue por tipo de habitación.

---

# 16. Responsabilidad del Equipo

Todo desarrollador debe revisar este documento antes de modificar:

- modelos,
- vistas,
- formularios,
- servicios,
- endpoints,
- lógica de negocio.

Si una nueva funcionalidad contradice estas reglas, debe consultarse con el líder técnico antes de implementarla.