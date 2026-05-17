# Templates Globales

Este documento explica cómo usar los templates globales de HotelSys para construir vistas consistentes en todo el sistema.

La estructura base está en `templates/base.html` y se complementa con partials reutilizables en `templates/partials/`.

## Archivos Globales

| Archivo | Uso |
|---|---|
| `templates/base.html` | Layout principal de vistas autenticadas |
| `templates/partials/navbar.html` | Sidebar, navegación y logout |
| `templates/partials/messages.html` | Toasts para `django.contrib.messages` |
| `templates/partials/pagination.html` | Footer de paginación integrado con tablas |
| `templates/partials/footer.html` | Footer global, actualmente desactivado en `base.html` |
| `templates/cuentas/login.html` | Layout independiente para login |

## Layout Base

Todas las vistas internas deben extender `base.html`.

```django
{% extends 'base.html' %}
```

`base.html` incluye:

- Bootstrap 5.3.3 por CDN.
- Bootstrap Icons 1.11.3 por CDN.
- `static/css/styles.css`.
- Sidebar global.
- Header de página.
- Contenedor principal.
- Toasts de mensajes.
- JS global para sidebar y toasts.

## Bloques Disponibles

| Bloque | Uso |
|---|---|
| `title` | Título HTML del documento |
| `extra_css` | CSS adicional por vista |
| `page_header` | Reemplaza completamente el header de página |
| `page_title` | Título visible de la página |
| `page_subtitle` | Descripción corta bajo el título |
| `page_actions` | Botones de acción del header |
| `content` | Contenido principal |
| `extra_js` | JS adicional por vista |

Ejemplo mínimo:

```django
{% extends 'base.html' %}

{% block title %}Empleados | HotelSys{% endblock %}
{% block page_title %}Empleados{% endblock %}
{% block page_subtitle %}Gestiona el personal operativo y administrativo del hotel.{% endblock %}

{% block page_actions %}
<a class="btn btn-primary" href="{% url 'empleados:create' %}">
    <i class="bi bi-plus-lg me-2" aria-hidden="true"></i>Nuevo empleado
</a>
{% endblock %}

{% block content %}
    Contenido de la vista
{% endblock %}
```

## Header de Página

El header global renderiza:

- Eyebrow fijo: `Gestión hotelera`.
- `page_title`.
- `page_subtitle`.
- `page_actions` alineado a la derecha en escritorio.

Usa `page_actions` para acciones principales como crear, volver, editar o nueva reserva.

Ejemplo:

```django
{% block page_actions %}
<a class="btn btn-outline-primary" href="{% url 'usuarios:list' %}">
    <i class="bi bi-arrow-left me-2" aria-hidden="true"></i>Volver
</a>
<a class="btn btn-primary" href="{% url 'usuarios:update' usuario.pk %}">
    <i class="bi bi-pencil-square me-2" aria-hidden="true"></i>Editar
</a>
{% endblock %}
```

Si una vista necesita un header completamente distinto, sobrescribir `page_header`. Evitar hacerlo salvo que el diseño lo justifique.

## Sidebar Global

El sidebar se incluye desde `partials/navbar.html`.

Características:

- Brand `HotelSys`.
- Navegación principal con Bootstrap Icons.
- Links visibles según variables de contexto de rol.
- Estado activo basado en `request.path`.
- Logout por formulario POST con CSRF.
- Toggle responsive para escritorio y móvil.

Variables esperadas en contexto:

| Variable | Uso |
|---|---|
| `user_is_admin` | Muestra módulos administrativos |
| `user_is_recepcionista` | Muestra módulos operativos de recepción |
| `user_is_housekeeping` | Muestra módulo de housekeeping |

Reglas:

- No cerrar sesión con un enlace GET.
- No duplicar navegación dentro de cada vista.
- Al agregar un módulo, añadir el link en `partials/navbar.html` y controlar visibilidad por rol.
- Usar iconos Bootstrap Icons dentro de `.sidebar-icon`.

## Mensajes Globales

`partials/messages.html` renderiza mensajes Django como toasts Bootstrap.

Se incluye automáticamente en `base.html`.

Tipos soportados:

| Tag | Icono |
|---|---|
| `success` | `bi-check-circle` |
| `warning` | `bi-exclamation-triangle` |
| `error`, `danger` | `bi-x-circle` |
| Otros | `bi-info-circle` |

Uso en views:

```python
from django.contrib import messages

messages.success(request, 'Registro creado correctamente.')
messages.error(request, 'No se pudo completar la operación.')
```

No crear alerts manuales para mensajes globales si la vista extiende `base.html`.

## Paginación Global

`partials/pagination.html` se usa como footer integrado de tablas.

Debe incluirse dentro de la card que contiene la tabla, justo después de `.table-responsive`.

Ejemplo:

```django
<div class="card border-0 shadow-sm">
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table align-middle mb-0 app-table">
                ...
            </table>
        </div>
        {% include 'partials/pagination.html' %}
    </div>
</div>
```

Requisitos de la vista:

- Usar una vista paginada de Django como `ListView` con `paginate_by`.
- Exponer `page_obj`, `paginator` e `is_paginated`, que `ListView` ya agrega automáticamente.

El parcial muestra:

- `Mostrando X-Y de Z registros`.
- Números de página cercanos a la página actual.
- Acciones anterior/siguiente con iconos.

Limitación actual:

- Preserva el query param `q` si existe.
- Si una vista usa más filtros, actualizar el parcial o pasar una querystring preparada.

## Tablas

Usar el patrón estándar:

```django
<div class="card border-0 shadow-sm">
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table align-middle mb-0 app-table">
                ...
            </table>
        </div>
        {% include 'partials/pagination.html' %}
    </div>
</div>
```

Acciones CRUD en tablas:

```django
<div class="btn-group btn-group-sm" role="group" aria-label="Acciones">
    <a class="btn btn-outline-primary" href="..." title="Ver" aria-label="Ver registro">
        <i class="bi bi-eye" aria-hidden="true"></i>
    </a>
    <a class="btn btn-outline-primary" href="..." title="Editar" aria-label="Editar registro">
        <i class="bi bi-pencil-square" aria-hidden="true"></i>
    </a>
    <a class="btn btn-outline-danger" href="..." title="Eliminar" aria-label="Eliminar registro">
        <i class="bi bi-trash" aria-hidden="true"></i>
    </a>
</div>
```

Reglas:

- En CRUD de tabla, usar iconos en vez de texto.
- Mantener `title` y `aria-label`.
- Usar `.text-end` para la columna de acciones.
- Usar estado vacío con icono `bi-inbox`.

## Formularios

Patrón recomendado:

```django
<form method="post" class="card border-0 shadow-sm app-form" novalidate>
    {% csrf_token %}
    <div class="card-body p-4">
        ... campos ...
    </div>
    <div class="card-footer bg-white border-0 p-4 pt-0 d-flex gap-2 justify-content-end">
        <a class="btn btn-light" href="...">
            <i class="bi bi-x-lg me-2" aria-hidden="true"></i>Cancelar
        </a>
        <button class="btn btn-primary" type="submit">
            <i class="bi bi-save me-2" aria-hidden="true"></i>Guardar
        </button>
    </div>
</form>
```

Reglas:

- Siempre incluir `{% csrf_token %}`.
- Usar `novalidate` para mostrar errores del servidor con estilo consistente.
- Mostrar errores con `.invalid-feedback.d-block`.
- Usar `app-form` para estilos de controles.
- Cargar librerías específicas de la vista con `extra_css` y `extra_js`.

## Detalles

Para vistas de detalle, usar cards y definition lists.

```django
<div class="card border-0 shadow-sm">
    <div class="card-body p-4">
        <h2 class="h5 mb-4">
            <i class="bi bi-person-vcard me-2" aria-hidden="true"></i>Información
        </h2>
        <dl class="row mb-0 app-dl">
            <dt class="col-sm-4">Campo</dt>
            <dd class="col-sm-8">Valor</dd>
        </dl>
    </div>
</div>
```

## Confirmaciones de Eliminación

Usar `error-card` para confirmaciones destructivas.

```django
<div class="error-card">
    <span class="error-code"><i class="bi bi-exclamation-triangle" aria-hidden="true"></i></span>
    <h2 class="h4 mb-3">¿Eliminar registro?</h2>
    <p class="text-secondary mb-4">Esta acción no se puede deshacer.</p>
    <form method="post" class="d-flex gap-2">
        {% csrf_token %}
        <a class="btn btn-light" href="...">
            <i class="bi bi-x-lg me-2" aria-hidden="true"></i>Cancelar
        </a>
        <button class="btn btn-danger" type="submit">
            <i class="bi bi-trash me-2" aria-hidden="true"></i>Eliminar
        </button>
    </form>
</div>
```

## Iconos

Bootstrap Icons está disponible globalmente desde `base.html`.

Convenciones:

| Acción | Icono |
|---|---|
| Crear | `bi-plus-lg` |
| Ver | `bi-eye` |
| Editar | `bi-pencil-square` |
| Eliminar | `bi-trash` |
| Guardar | `bi-save` |
| Cancelar | `bi-x-lg` |
| Volver | `bi-arrow-left` |
| Buscar | `bi-search` |
| Activo | `bi-check-circle` |
| Inactivo | `bi-dash-circle` |
| Advertencia | `bi-exclamation-triangle` |

Reglas:

- Iconos decorativos deben tener `aria-hidden="true"`.
- Botones de solo icono deben tener `aria-label`.
- Botones de texto con icono deben conservar texto visible.

## CSS y JS Por Vista

Usar `extra_css` para librerías o estilos específicos.

```django
{% block extra_css %}
<link href="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/css/tom-select.bootstrap5.min.css" rel="stylesheet">
{% endblock %}
```

Usar `extra_js` para scripts específicos.

```django
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/js/tom-select.complete.min.js"></script>
<script>
    ...
</script>
{% endblock %}
```

Reglas:

- No agregar librerías globales a `base.html` salvo que se usen en la mayoría del sistema.
- Mantener scripts específicos en el template que los necesita.
- Evitar lógica JavaScript duplicada entre vistas.

## Login

`templates/cuentas/login.html` no extiende `base.html` porque usa un layout propio de autenticación.

Incluye:

- Bootstrap.
- Bootstrap Icons.
- `static/css/styles.css`.
- Panel izquierdo con formulario.
- Panel derecho visual con imagen y chips informativos.

No usar el sidebar global en login.

## Footer

`partials/footer.html` existe, pero actualmente está comentado en `base.html`.

Si se reactiva:

- Revisar márgenes con sidebar.
- Validar responsive.
- Confirmar que no afecte páginas con tablas largas o formularios.

## Checklist Para Nuevas Vistas

- Extiende `base.html` salvo que sea una pantalla pública especial.
- Define `title`, `page_title` y `page_subtitle`.
- Usa `page_actions` para acciones principales.
- Usa cards, `app-table`, `app-form`, `app-dl` y `error-card` según corresponda.
- Usa Bootstrap Icons con accesibilidad básica.
- Incluye `partials/pagination.html` dentro de la card de tabla si hay paginación.
- Usa mensajes Django en la vista y deja que `partials/messages.html` los renderice.
- No duplices sidebar, toasts ni scripts globales.
- Ejecuta `python manage.py check` después de cambios relevantes.
