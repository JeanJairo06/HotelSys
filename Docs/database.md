# Base de Datos — HotelSys

Este documento describe la estructura de la base de datos del sistema HotelSys.

Incluye:
- entidades,
- relaciones,
- restricciones,
- reglas de integridad,
- y organización ORM utilizada en Django.

---

# 1. Motor de Base de Datos

| Tecnología | Uso |
|---|---|
| PostgreSQL | Base de datos principal |
| Django ORM | Capa ORM |

---

# 2. Arquitectura ORM

El proyecto utiliza:
- Django ORM,
- relaciones normalizadas,
- validaciones en modelos,
- constraints de integridad.

---

# 3. Convenciones de Base de Datos

## Naming

| Elemento | Convención |
|---|---|
| Tablas | snake_case plural |
| Campos | snake_case |
| Foreign Keys | nombre_modelo |
| Primary Keys | id |
| Constraints | snake_case descriptivo |

---

# 4. Diagrama General de Relaciones

```text
Hotel
│
├── Habitacion
│   └── TipoHabitacion
│       └── Tarifa
│
├── Reserva
│   ├── Huesped
│   └── Habitacion
│
└── Estancia
    ├── Reserva
    ├── Habitacion
    ├── CargoEstancia
    └── Folio
```

---

# 5. Entidades del Sistema

---

# 5.1 Hotel

## Tabla

```text
hoteles
```

---

## Descripción

Representa un hotel administrado por el sistema.

---

## Campos

| Campo | Tipo | Restricciones |
|---|---|---|
| id | PK | Auto |
| nombre | CharField(150) | Obligatorio |
| ruc | CharField(11) | Unique |
| direccion | TextField | Obligatorio |
| estrellas | PositiveSmallIntegerField | Obligatorio |
| telefono | CharField(20) | Obligatorio |

---

## Relaciones

| Relación | Tipo |
|---|---|
| habitaciones | OneToMany |
| reservas | OneToMany |

---

# 5.2 TipoHabitacion

## Tabla

```text
tipos_habitacion
```

---

## Descripción

Define categorías de habitaciones.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| nombre | CharField(100) |
| capacidad | PositiveIntegerField |
| precio_base | DecimalField |
| amenidades | JSONField |

---

## Relaciones

| Relación | Tipo |
|---|---|
| habitaciones | OneToMany |
| tarifas | OneToMany |

---

# 5.3 Habitacion

## Tabla

```text
habitaciones
```

---

## Descripción

Representa habitaciones físicas del hotel.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| hotel | FK → Hotel |
| tipo | FK → TipoHabitacion |
| numero | CharField(10) |
| piso | PositiveSmallIntegerField |
| estado | CharField |

---

## Estados

| Estado |
|---|
| DISPONIBLE |
| OCUPADA |
| LIMPIEZA |
| MANTENIMIENTO |

---

## Constraints

```text
UNIQUE(hotel, numero)
```

---

## Relaciones

| Relación | Tipo |
|---|---|
| reservas | OneToMany |
| estancias | OneToMany |

---

# 5.4 Huesped

## Tabla

```text
huespedes
```

---

## Descripción

Representa clientes/huéspedes del hotel.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| tipo_doc | CharField |
| num_doc | CharField |
| nombres | CharField |
| apellidos | CharField |
| email | EmailField |
| telefono | CharField |
| nacionalidad | CharField |

---

## Constraints

```text
UNIQUE(num_doc)
```

---

## Relaciones

| Relación | Tipo |
|---|---|
| reservas | OneToMany |

---

# 5.5 Tarifa

## Tabla

```text
tarifas
```

---

## Descripción

Define tarifas por tipo de habitación y rango de fechas.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| tipo_habitacion | FK → TipoHabitacion |
| nombre | CharField |
| precio_noche | DecimalField |
| fecha_inicio | DateField |
| fecha_fin | DateField |

---

## Relaciones

| Relación | Tipo |
|---|---|
| tipo_habitacion | ManyToOne |

---

# 5.6 Reserva

## Tabla

```text
reservas
```

---

## Descripción

Representa reservas realizadas por huéspedes.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| hotel | FK → Hotel |
| huesped | FK → Huesped |
| habitacion | FK → Habitacion |
| fecha_entrada | DateField |
| fecha_salida | DateField |
| num_adultos | PositiveIntegerField |
| estado | CharField |
| precio_total | DecimalField |
| origen | CharField |

---

## Estados

| Estado |
|---|
| PENDIENTE |
| CONFIRMADA |
| CANCELADA |
| CHECKIN |
| FINALIZADA |

---

## Relaciones

| Relación | Tipo |
|---|---|
| estancia | OneToOne |

---

## Validaciones

- fecha_salida > fecha_entrada
- No solapamiento de reservas
- Habitación pertenece al hotel

---

# 5.7 Estancia

## Tabla

```text
estancias
```

---

## Descripción

Representa ocupación real de una habitación.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| reserva | OneToOne → Reserva |
| habitacion | FK → Habitacion |
| fecha_checkin | DateTimeField |
| fecha_checkout | DateTimeField |
| precio_final | DecimalField |
| estado | CharField |

---

## Estados

| Estado |
|---|
| ACTIVA |
| FINALIZADA |
| CANCELADA |

---

## Relaciones

| Relación | Tipo |
|---|---|
| cargos | OneToMany |
| folio | OneToOne |

---

# 5.8 CargoEstancia

## Tabla

```text
cargos_estancia
```

---

## Descripción

Representa cargos asociados a una estancia.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| estancia | FK → Estancia |
| concepto | CharField |
| monto | DecimalField |
| fecha | DateTimeField |
| tipo | CharField |

---

## Tipos

| Tipo |
|---|
| HABITACION |
| RESTAURANTE |
| LAVANDERIA |
| MINIBAR |
| PENALIDAD |
| OTRO |

---

# 5.9 Folio

## Tabla

```text
folios
```

---

## Descripción

Representa consolidación financiera de una estancia.

---

## Campos

| Campo | Tipo |
|---|---|
| id | PK |
| estancia | OneToOne → Estancia |
| subtotal | DecimalField |
| igv | DecimalField |
| total | DecimalField |
| estado | CharField |

---

## Estados

| Estado |
|---|
| ABIERTO |
| PENDIENTE |
| PAGADO |
| CERRADO |
| ANULADO |

---

# 6. Relaciones ORM Utilizadas

## ForeignKey

Usado en:
- Habitacion → Hotel
- Habitacion → TipoHabitacion
- Reserva → Huesped
- Reserva → Habitacion
- Reserva → Hotel
- Tarifa → TipoHabitacion
- CargoEstancia → Estancia

---

## OneToOneField

Usado en:
- Estancia → Reserva
- Folio → Estancia

---

# 7. Reglas de Integridad

## Habitaciones

- No puede existir el mismo número de habitación dentro del mismo hotel.

---

## Huéspedes

- No puede existir duplicidad de documento.

---

## Reservas

- No puede existir solapamiento de reservas activas.

---

## Estancias

- Una reserva solo puede tener una estancia.

---

## Folios

- Una estancia solo puede tener un folio.

---

# 8. Estrategia de Eliminación

## Relaciones críticas

Usan:

```python
models.PROTECT
```

Ejemplos:
- reservas,
- habitaciones,
- hoteles,
- tarifas,
- folios.

---

## Relaciones dependientes

Usan:

```python
models.CASCADE
```

Ejemplos:
- cargos de estancia.

---

# 9. Validaciones ORM

Las reglas críticas deben implementarse usando:

```python
clean()
```

---

## Ejemplo

```python
def clean(self):

    if self.fecha_salida <= self.fecha_entrada:
        raise ValidationError(
            'La fecha de salida debe ser mayor.'
        )
```

---

# 10. Recomendaciones ORM

## Utilizar

- related_name
- constraints
- properties
- managers personalizados
- full_clean()

---

## Evitar

- lógica compleja en views,
- queries duplicadas,
- relaciones innecesarias,
- eliminación física de registros históricos.

---

# 11. Migraciones

## Reglas

- No modificar migraciones ya ejecutadas.
- No eliminar migraciones existentes.
- Toda modificación estructural debe probarse localmente.

---

## Comandos

```bash
docker compose exec web python manage.py makemigrations
```

```bash
docker compose exec web python manage.py migrate
```

---

# 12. Datos Iniciales

El sistema incluye un comando seed:

```bash
docker compose exec web python manage.py seed_hotelsys
```

---

# 13. Consideraciones Futuras

El modelo fue diseñado considerando futura escalabilidad:

- múltiples hoteles,
- dashboards,
- housekeeping,
- reportes financieros,
- tarifas dinámicas,
- posibles integraciones futuras.

---

# 14. Responsabilidad Técnica

Las modificaciones de:
- relaciones,
- migraciones,
- constraints,
- estructura de tablas,

deben ser aprobadas por el líder técnico antes de integrarse.