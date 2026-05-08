# Estándares de Desarrollo — HotelSys

Este documento define las convenciones técnicas y estándares obligatorios del proyecto HotelSys.

Todos los desarrolladores deben respetar estas reglas para mantener consistencia, mantenibilidad y calidad del código.

---

# 1. Convenciones Generales

## Idioma

- Los comentarios y documentación pueden escribirse en español.

## Framework Principal

- Django
- Django ORM
- Django Templates
- Bootstrap 5

---

# 2. Convenciones de Naming

## 2.1 Clases

Las clases deben usar:

```text
PascalCase
```

### Correcto

```python
class Hotel(models.Model):
```

```python
class TipoHabitacion(models.Model):
```

### Incorrecto

```python
class hotel(models.Model):
```

```python
class tipo_habitacion(models.Model):
```

---

## 2.2 Variables y funciones

Las variables y funciones deben usar:

```text
snake_case
```

### Correcto

```python
fecha_entrada
precio_total
calcular_tarifa()
```

### Incorrecto

```python
fechaEntrada
PrecioTotal
```

---

## 2.3 Constantes

Las constantes deben usar:

```text
UPPER_CASE
```

### Ejemplo

```python
IGV_PERCENTAGE = 0.18
```

---

## 2.4 Archivos

Los archivos deben usar:

```text
snake_case.py
```

### Correcto

```text
hotel_service.py
reservation_validator.py
```

### Incorrecto

```text
HotelService.py
ReservationValidator.py
```

---

# 3. Convenciones Django

## 3.1 Apps

Cada app debe representar un dominio funcional.

### Apps oficiales

```text
accounts
hotels
rooms
guests
reservations
stays
billing
housekeeping
reports
```

---

## 3.2 Modelos

- Los modelos deben estar en singular.
- Deben heredar de `models.Model`.

### Correcto

```python
class Reserva(models.Model):
```

---

## 3.3 Tablas

Usar `db_table`.

### Ejemplo

```python
class Meta:
    db_table = 'reservas'
```

---

## 3.4 Related names

Toda relación debe definir `related_name`.

### Correcto

```python
habitacion = models.ForeignKey(
    Habitacion,
    on_delete=models.PROTECT,
    related_name='reservas'
)
```

---

## 3.5 on_delete

### Relaciones críticas

Usar:

```python
models.PROTECT
```

### Relaciones históricas/dependientes

Usar:

```python
models.CASCADE
```

---

# 4. Validaciones

## Reglas críticas

Las reglas del negocio deben implementarse en:

```python
clean()
```

---

## save()

Cuando existan validaciones críticas:

```python
def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)
```

---

# 5. Templates

## Ubicación

```text
templates/app/
```

### Ejemplo

```text
templates/reservations/list.html
```

---

## Naming

Usar:

```text
snake_case.html
```

---

# 6. URLs

Las URLs deben:

- estar en español,
- usar kebab-case o snake_case consistente.

### Correcto

```text
/reservas/
/checkin/
/checkout/
/habitaciones/
```

---

# 7. Bootstrap

- Utilizar Bootstrap 5.
- No usar estilos inline excesivos.
- Centralizar estilos personalizados en `static/css/`.

---

# 8. Git Workflow

## Branches oficiales

| Branch | Uso |
|---|---|
| main | Producción |
| develop | Integración |
| feature/* | Desarrollo individual |

---

## Flujo

```text
feature/* → develop → main
```

---

## Reglas Git

### Prohibido

- trabajar directamente en `main`
- trabajar directamente en `develop`

---

## Obligatorio

1. Crear branch feature
2. Realizar commits descriptivos
3. Crear Pull Request
4. Esperar revisión del líder técnico

---

# 9. Convención de Commits

## Formato

```text
tipo: descripcion
```

### Ejemplos

```text
feat: add reservation validation
fix: solve overlapping booking bug
refactor: improve folio calculation
docs: update README
```

---

# 10. Migraciones

## Reglas

- Solo el líder técnico modifica modelos críticos.
- No eliminar migraciones antiguas.
- No modificar migraciones ya ejecutadas.
- Toda migración debe probarse antes de subir.

---

# 11. Imports

Orden obligatorio:

1. Librerías estándar
2. Django
3. Terceros
4. Apps internas

### Ejemplo

```python
from decimal import Decimal

from django.db import models

from config.choices import EstadoReserva

from rooms.models import Habitacion
```

---

# 12. Admin Django

Todos los modelos deben:

- registrarse en admin,
- incluir:
  - list_display
  - search_fields
  - list_filter

---

# 13. Testing

Toda funcionalidad crítica debe tener tests:

- disponibilidad,
- reservas,
- checkin,
- checkout,
- folio,
- cálculo tarifario.

---

# 14. Código Limpio

## Evitar

- lógica compleja en views,
- duplicación de código,
- queries N+1,
- variables ambiguas.

---

## Preferir

- métodos de negocio,
- managers personalizados,
- propiedades,
- servicios reutilizables.

---

# 15. Responsabilidad del Equipo

Todo desarrollador debe revisar este documento antes de:

- crear modelos,
- modificar lógica,
- crear migraciones,
- implementar vistas,
- subir código al repositorio.

El incumplimiento de estos estándares puede generar conflictos de integración y rechazo del Pull Request.