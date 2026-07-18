# Empleados

Este documento describe el modulo de empleados de HotelSys: modelo, reglas de negocio, Service Layer, flujo web, relacion con usuarios, auditoria y verificacion.

El modulo usa `empleados.models.Empleado` como registro laboral del personal del hotel. Las cuentas de acceso se gestionan aparte con `django.contrib.auth.models.User` y se vinculan mediante `cuentas.models.UsuarioEmpleado`.

## Archivos Principales

| Archivo | Responsabilidad |
|---|---|
| `empleados/models.py` | Modelo `Empleado`, normalizacion y validaciones basicas |
| `empleados/services.py` | Reglas de negocio y operaciones transaccionales del modulo |
| `empleados/exceptions.py` | Excepciones de dominio especificas de empleados |
| `empleados/forms.py` | Formulario web de creacion y edicion |
| `empleados/views.py` | Vistas CRUD web y flujos de activar/desactivar |
| `empleados/urls.py` | Rutas del modulo bajo `/empleados/` |
| `empleados/admin.py` | Configuracion del admin Django |
| `templates/empleados/` | Templates del CRUD web |
| `empleados/tests.py` | Pruebas de modelo, servicio y vistas |

## Modelo

El modelo `Empleado` hereda de `core.models.ModeloBase`.

Campos heredados:

| Campo | Uso |
|---|---|
| `creado_en` | Fecha y hora de creacion |
| `actualizado_en` | Fecha y hora de ultima actualizacion |
| `creado_por` | Usuario que creo el registro, si aplica |
| `activo` | Soft delete logico del registro |

Campos propios:

| Campo | Regla |
|---|---|
| `codigo` | Unico, autogenerado con prefijo `EMP-` si no se envia |
| `nombres` | Obligatorio, se normaliza con `strip()` |
| `apellidos` | Obligatorio, se normaliza con `strip()` |
| `cargo` | Debe pertenecer a `CargoEmpleado` |
| `email` | Unico, se normaliza a minusculas |
| `telefono` | Opcional, unico si existe, entre 7 y 15 digitos normalizados |
| `estado` | `EstadoGeneral.ACTIVO` o `EstadoGeneral.INACTIVO` |
| `fecha_ingreso` | No puede ser futura |

Managers heredados:

| Manager | Uso |
|---|---|
| `Empleado.objects` | Solo registros con `activo=True` |
| `Empleado.todos` | Todos los registros, activos e inactivos |

Regla importante:

- Usar `Empleado.todos` cuando el flujo debe consultar historico o permitir operar empleados inactivos.
- Usar `Empleado.objects` cuando solo se deben considerar empleados activos.

## Reglas de Negocio

| Regla | Implementacion |
|---|---|
| El codigo se genera automaticamente | `Empleado.generar_codigo()` y `EmpleadoService.generar_codigo()` |
| El codigo no se modifica al editar | `EmpleadoForm.clean_codigo()` y `EmpleadoService._preparar_datos()` |
| El formulario no expone `estado` | `EmpleadoForm.Meta.fields` no incluye `estado` |
| Editar empleado no cambia estado | `EmpleadoService.actualizar_empleado()` conserva `empleado.estado` |
| Activar/desactivar es el unico flujo de cambio de estado | `EmpleadoService.activar_empleado()` y `EmpleadoService.desactivar_empleado()` |
| Desactivar empleado aplica soft delete | `estado=INACTIVO` y `activo=False` |
| Activar empleado restaura disponibilidad | `estado=ACTIVO` y `activo=True` |
| Desactivar empleado desactiva usuario asociado activo | `EmpleadoService._desactivar_cuenta_asociada()` delega en `UsuarioService.desactivar_usuario()` |
| Activar empleado no reactiva usuario asociado | Regla explicita del servicio |
| Email y telefono se validan contra historico | Validaciones usan `Empleado.todos` |

## Service Layer

Toda regla de negocio nueva debe entrar por `EmpleadoService` antes de tocar vistas o formularios.

Metodos publicos actuales:

| Metodo | Uso |
|---|---|
| `empleados_queryset(q=None, incluir_inactivos=True)` | Listado web y busqueda |
| `detalle_queryset()` | Detalle, edicion y flujos sobre historico |
| `generar_codigo()` | Generacion de codigo de empleado |
| `crear_empleado(data, usuario_actor=None)` | Alta transaccional con auditoria |
| `actualizar_empleado(empleado, data, usuario_actor=None)` | Edicion sin cambiar estado ni codigo |
| `desactivar_empleado(empleado, usuario_actor=None)` | Soft delete y desactivacion de usuario asociado |
| `activar_empleado(empleado, usuario_actor=None)` | Reactivacion del empleado sin reactivar usuario |

Ejemplo recomendado:

```python
empleado = EmpleadoService.crear_empleado(
    data=form.cleaned_data,
    usuario_actor=request.user,
)
```

No recomendado:

```python
Empleado.objects.create(**form.cleaned_data)
```

## Excepciones de Dominio

Las excepciones del modulo viven en `empleados/exceptions.py` y heredan de `core.exceptions`.

| Excepcion | Uso |
|---|---|
| `EmpleadoDuplicado` | Email, telefono o integridad duplicada |
| `EmpleadoNoEncontrado` | Recurso inexistente |
| `EmpleadoNoDesactivable` | Operacion de desactivacion no permitida |
| `EmpleadoInactivo` | Operacion no permitida por estado inactivo |
| `CargoEmpleadoInvalido` | Cargo fuera de `CargoEmpleado` |
| `DatosEmpleadoInvalidos` | Datos invalidos de dominio |

Las vistas deben capturar `AppError` para mostrar mensajes controlados al usuario.

## Relacion Con Usuarios

La relacion con cuentas de acceso se administra desde `cuentas.models.UsuarioEmpleado`.

Reglas finales:

| Caso | Resultado |
|---|---|
| Crear usuario | Solo se puede vincular un empleado activo y sin cuenta historica |
| Desactivar usuario | `User.is_active=False` y soft delete del perfil `UsuarioEmpleado` |
| Desactivar empleado con usuario activo | Tambien se desactiva el usuario asociado |
| Desactivar empleado sin usuario | Solo se desactiva el empleado |
| Activar empleado con usuario historico inactivo | No se reactiva automaticamente el usuario |
| Reactivar usuario | Debe hacerse desde el modulo usuarios y solo si el empleado esta activo |

Motivo de la regla de no reactivar automaticamente:

- La reactivacion de una cuenta de acceso es una decision de seguridad distinta a la disponibilidad laboral del empleado.

## Rutas

Las rutas viven en `empleados/urls.py` y se montan desde `config/urls.py` bajo `/empleados/`.

```python
path('empleados/', include('empleados.urls'))
```

| Nombre | Metodo | URL | Vista |
|---|---|---|---|
| `empleados:list` | `GET` | `/empleados/` | `EmpleadoListView` |
| `empleados:create` | `GET`, `POST` | `/empleados/crear/` | `EmpleadoCreateView` |
| `empleados:detail` | `GET` | `/empleados/<pk>/` | `EmpleadoDetailView` |
| `empleados:update` | `GET`, `POST` | `/empleados/<pk>/editar/` | `EmpleadoUpdateView` |
| `empleados:activate` | `GET`, `POST` | `/empleados/<pk>/activar/` | `EmpleadoActivateView` |
| `empleados:deactivate` | `GET`, `POST` | `/empleados/<pk>/desactivar/` | `EmpleadoDeactivateView` |

Usar siempre `{% url 'empleados:nombre' %}` o `reverse('empleados:nombre')`. No hardcodear rutas.

## Vistas Web

Todas las vistas del CRUD de empleados requieren rol `admin` mediante `role_required(ROLE_ADMIN)`.

| Vista | Regla |
|---|---|
| `EmpleadoListView` | Lista activos e inactivos usando `EmpleadoService.empleados_queryset()` |
| `EmpleadoDetailView` | Usa historico y muestra auditoria + usuario asociado |
| `EmpleadoCreateView` | Crea solo mediante `EmpleadoService.crear_empleado()` |
| `EmpleadoUpdateView` | Edita solo mediante `EmpleadoService.actualizar_empleado()` y permite inactivos |
| `EmpleadoDeactivateView` | Desactiva mediante `EmpleadoService.desactivar_empleado()` |
| `EmpleadoActivateView` | Activa mediante `EmpleadoService.activar_empleado()` |

## Templates

| Template | Uso |
|---|---|
| `templates/empleados/list.html` | Listado, busqueda y acciones condicionales |
| `templates/empleados/detail.html` | Datos laborales, auditoria y usuario asociado |
| `templates/empleados/form.html` | Crear/editar sin campo `estado` |
| `templates/empleados/confirm_deactivate.html` | Confirmacion de desactivacion |
| `templates/empleados/confirm_activate.html` | Confirmacion de activacion |

Reglas de UI:

- Empleado activo: mostrar accion `Desactivar`.
- Empleado inactivo: mostrar accion `Activar`.
- No mostrar accion de eliminacion fisica.
- No exponer selector manual de `estado` en formularios.

## Auditoria

El detalle de empleado muestra:

| Campo | Fuente |
|---|---|
| Registro activo | `empleado.activo` |
| Creado por | `empleado.creado_por` |
| Creado en | `empleado.creado_en` |
| Actualizado en | `empleado.actualizado_en` |
| Usuario asociado | `UsuarioEmpleado.todos.filter(empleado=empleado).first()` |
| Cuenta activa | `perfil_usuario.usuario.is_active` |
| Perfil activo | `perfil_usuario.activo` |

## Admin Django

El admin de `Empleado` muestra campos operativos y de auditoria.

Configuracion actual:

| Opcion | Valor |
|---|---|
| `list_display` | Incluye codigo, nombres, cargo, email, estado, activo y auditoria |
| `list_filter` | `activo`, `estado`, `cargo`, `creado_en` |
| `search_fields` | `codigo`, `nombres`, `apellidos`, `email`, `cargo` |
| `readonly_fields` | `creado_en`, `actualizado_en` |

Nota operativa:

- Si el admin Django se usa para operacion real, conviene agregar acciones admin que deleguen en `EmpleadoService.activar_empleado()` y `EmpleadoService.desactivar_empleado()`.
- Mientras no existan esas acciones, el flujo recomendado para cambios de estado es la UI web del modulo.

## Pruebas

La suite de `empleados` cubre:

| Area | Cobertura |
|---|---|
| Modelo | Normalizacion, codigo automatico y validaciones |
| Formulario | Codigo readonly y ausencia de `estado` |
| Servicio | Crear, actualizar, duplicados, activar/desactivar e integracion con usuarios |
| Vistas | Crear, editar, listar, detalle, activar y desactivar |
| Integracion con usuarios | Desactivar empleado desactiva usuario; activar empleado no reactiva usuario |

Comandos de verificacion recomendados:

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py makemigrations --check --dry-run
docker compose run --rm web python manage.py test empleados
docker compose run --rm web python manage.py test cuentas empleados
```

Para cierre completo del proyecto antes de merge:

```bash
docker compose run --rm web python manage.py test
```

Warnings conocidos que no bloquean el modulo:

- `DEFAULT_AUTO_FIELD` en apps antiguas.
- Warning local de Docker Compose si `.env` contiene `$` en `SECRET_KEY` sin escapar.

## Criterios de Cierre Del Modulo

El modulo `empleados` puede considerarse cerrado funcionalmente cuando se cumple lo siguiente:

| Criterio | Estado esperado |
|---|---|
| Modelo hereda de `ModeloBase` | Cumplido |
| No hay borrado fisico desde UI | Cumplido |
| Activar/desactivar esta centralizado en service | Cumplido |
| Formulario no cambia estado directamente | Cumplido |
| Desactivar empleado desactiva usuario asociado | Cumplido |
| Activar empleado no reactiva usuario asociado | Cumplido |
| Detalle muestra auditoria y usuario asociado | Cumplido |
| Tests de `empleados` pasan | Cumplido |
| Tests `cuentas empleados` pasan | Cumplido |
| Documentacion del modulo existe | Cumplido |

Pendiente opcional:

- Endurecer el admin Django para que las transiciones tambien deleguen en `EmpleadoService`.
- Ejecutar la suite completa del proyecto antes de integrar a rama principal.
