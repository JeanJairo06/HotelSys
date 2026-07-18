# HotelSys

Sistema de Gestión Hotelera desarrollado con Django, PostgreSQL y Docker.

HotelSys permite administrar:
- reservas,
- huéspedes,
- habitaciones,
- check-in/check-out,
- housekeeping,
- facturación,
- dashboards,
- y reportes operacionales.

---

# Tecnologías Utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje backend |
| Django | Framework principal |
| PostgreSQL | Base de datos |
| Docker | Contenedores |
| Docker Compose | Orquestación |
| Bootstrap 5 | Interfaz |
| Chart.js | Gráficos y dashboards |
| python-decouple | Variables de entorno |

---

# Arquitectura del Proyecto

El proyecto está organizado bajo arquitectura modular utilizando aplicaciones Django independientes.

## Estructura General

```text
HotelSys/
├── accounts/
├── hotels/
├── rooms/
├── guests/
├── reservations/
├── stays/
├── billing/
├── housekeeping/
├── reports/
├── config/
├── templates/
├── static/
├── media/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .env.example
└── manage.py
```

---

# Aplicaciones del Sistema

| Aplicación | Responsabilidad |
|---|---|
| Cuentas | Usuarios, autenticación y roles |
| hoteles | Gestión de hoteles |
| habitaciones | Habitaciones y tipos |
| Húespedes | Datos de clientes/huéspedes |
| reservaciones | Reservas y disponibilidad |
| Estancias | Check-in y check-out |
| Facturación | Folios, tarifas y facturación |
| Limpieza | Limpieza y mantenimiento |
| Reportes | Dashboard y reportes |

---

# Requisitos Previos

Antes de ejecutar el proyecto debes tener instalado:

- Docker Desktop
- Git
- Python 3.11+ (opcional para desarrollo local)

---

# Instalación del Proyecto

## 1. Clonar repositorio

```bash
git clone https://github.com/JeanJairo06/HotelSys.git
cd HotelSys
```

---

## 2. Crear archivo `.env`

Copiar:

```bash
cp .env.example .env
```

Completar variables:

```env
SECRET_KEY=tu-clave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=hotelsys_db
DB_USER=hotelsys_user
DB_PASSWORD=hotelsys_pass_2026
DB_HOST=db
DB_PORT=5432
```

---

# Ejecución con Docker

## Construir contenedores

```bash
docker compose up --build -d
```

---

## Ver logs

```bash
docker compose logs -f
```

---

# Migraciones

## Crear migraciones

```bash
docker compose exec web python manage.py makemigrations
```

## Ejecutar migraciones

```bash
docker compose exec web python manage.py migrate
```
## Ejecutar seed

```bash
docker compose exec web python manage.py seed_hotelsys
```

---
---

# Crear Superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

---

# Acceso al Sistema

| Servicio | URL |
|---|---|
| Aplicación | http://localhost:8000 |
| Admin Django | http://localhost:8000/admin |

---

# Variables de Entorno

| Variable | Descripción |
|---|---|
| SECRET_KEY | Clave secreta Django |
| DEBUG | Modo debug |
| ALLOWED_HOSTS | Hosts permitidos |
| DB_NAME | Nombre BD |
| DB_USER | Usuario PostgreSQL |
| DB_PASSWORD | Password PostgreSQL |
| DB_HOST | Host BD |
| DB_PORT | Puerto PostgreSQL |

---

## Seguridad de Sesión

Las sesiones se cierran al cerrar el navegador y se controlan en backend por inactividad y duración absoluta según el rol. La pantalla muestra un aviso dos minutos antes de expirar y sincroniza su estado entre pestañas.

| Rol | Inactividad | Máximo absoluto |
|---|---:|---:|
| Admin | 15 min | 8 h |
| Recepcionista | 20 min | 12 h |
| Housekeeping | 15 min | 8 h |

Los eventos de expiración se registran sin almacenar identificadores de sesión, credenciales ni parámetros de URL.

### Despliegue Seguro

En producción deben configurarse HTTPS y cookies seguras:

```env
DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_REFERRER_POLICY=same-origin
```

Si TLS termina en un proxy inverso confiable, añadir `USE_X_FORWARDED_PROTO=True`. No habilitar esa variable si el proxy no elimina cabeceras `X-Forwarded-Proto` enviadas por clientes.

Antes de desplegar, ejecutar:

```bash
docker compose exec web python manage.py check --deploy
docker compose exec web python manage.py test
```

Verificación manual entre pestañas:

1. Iniciar sesión y abrir dos pestañas del sistema.
2. Esperar el aviso o reducir temporalmente el timeout en desarrollo.
3. Presionar “Continuar sesión” en una pestaña y confirmar que la otra oculta el aviso.
4. Dejar expirar la sesión y confirmar que ambas pestañas vuelven al login.

---

# Flujo Operacional del Sistema

```text
Reserva
↓
Check-in
↓
Estancia
↓
Cargos/Folio
↓
Checkout
↓
Limpieza
↓
Disponible
```

---

# Estados del Sistema

## Estado de Habitación

| Estado | Código |
|---|---|
| Disponible | DI |
| Ocupada | OC |
| Limpieza | LI |
| Mantenimiento | MA |

---

## Estado de Reserva

| Estado | Código |
|---|---|
| Pendiente | PE |
| Confirmada | CO |
| Cancelada | CA |
| Check-In | CI |
| Finalizada | FI |

---

# Reglas de Negocio

## Reservas
- No puede existir solapamiento de reservas.
- La fecha de salida debe ser mayor a la fecha de entrada.

## Habitaciones
- No se puede hacer check-in en habitaciones:
  - en limpieza,
  - en mantenimiento,
  - ocupadas.

## Facturación
- No se puede realizar checkout con deuda pendiente.

## Housekeeping
- Checkout cambia automáticamente habitación a estado limpieza.

---

# Convenciones del Proyecto

## Python
- snake_case para variables y funciones.
- PascalCase para clases y modelos.

## Templates

```text
app/template.html
```

## URLs

```text
/reservas/
/habitaciones/
/checkin/
```

---

# Flujo Git

## Branches principales

| Branch | Uso |
|---|---|
| main | Producción |
| develop | Integración |
| feature/* | Desarrollo individual |

---

# Flujo de Trabajo

```text
feature/* → develop → main
```

---

# Reglas Git

## NO trabajar directamente sobre:
- main
- develop

## Siempre:
1. Crear branch feature
2. Hacer commits
3. Crear Pull Request
4. Esperar revisión

---

# Instalación para Desarrollo Local (Opcional)

## Crear entorno virtual

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```



## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Dependencias Principales

```text
Django
python-decouple
psycopg2-binary
gunicorn
```

---

# Comandos Útiles

## Ejecutar servidor

```bash
python manage.py runserver
```

## Crear app

```bash
python manage.py startapp nombre_app
```

## Acceder al contenedor

```bash
docker compose exec web bash
```


# Organización del Equipo

| Integrante|Rol | Módulo |
|---|---|--|
|Senador Torres Jean Jairo| Líder Técnico | Arquitectura y Core |
| Guerrero Montenegro Luis Agusto|Dev 2 | Reservas y Huéspedes |
| Escribano Macalopu Daniel|Dev 3 | Habitaciones y Estancias |
| Julcahuca Fernandez Carlos German|Dev 4 | Billing y Facturación |
|Pupuche Cabrera Yefry Paul| Dev 5 | Dashboard y Reportes |

---

# Responsabilidades del Líder Técnico

- Arquitectura del sistema
- Integración de módulos
- Revisión de Pull Requests
- Control de migraciones
- Configuración Docker
- Gestión de despliegue

---

# Buenas Prácticas

- Mantener código limpio y modular.
- Utilizar validaciones en modelos.
- Evitar lógica compleja en vistas.
- Utilizar métodos de negocio en modelos.
- Documentar cambios importantes.
- Crear commits descriptivos.

---

# Documentación Adicional

| Documento | Descripción |
|---|---|
| docs/database.md | Modelos y relaciones |
| docs/api.md | Endpoints |
| docs/business-rules.md | Reglas del negocio |
| docs/git-workflow.md | Flujo Git |

---

# Integrantes del Proyecto

Proyecto desarrollado por el equipo de Sistemas para el curso de Taller de Lenguaje de Programación.

- Senador Torres Jean Jairo
- Guerrero Montenegro Luis Agusto
- Escribano Macalopu Daniel
- Julcahuca Fernandez Carlos German
- Pupuche Cabrera Yefry Paul
---

# Licencia

Proyecto académico.
