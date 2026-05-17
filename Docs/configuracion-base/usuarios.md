# Usuarios

Este documento describe el módulo de usuarios de HotelSys: CRUD web, permisos, formularios, relación con empleados y autocompletado de empleados disponibles.

El módulo usa `django.contrib.auth.models.User` como cuenta de acceso y `cuentas.models.UsuarioEmpleado` como vínculo uno a uno con `empleados.models.Empleado`.

## Archivos Principales

| Archivo | Responsabilidad |
|---|---|
| `cuentas/models.py` | Modelo `UsuarioEmpleado` para vincular usuario y empleado |
| `cuentas/views.py` | Vistas CRUD de usuarios |
| `cuentas/forms.py` | Formularios de creación y edición |
| `cuentas/urls.py` | Rutas del módulo bajo `/usuarios/` |
| `cuentas/roles.py` | Constantes y helpers de roles |
| `cuentas/decorators.py` | Decoradores de protección por rol |
| `templates/cuentas/usuarios/` | Templates del CRUD |
| `api/views.py` | Endpoint de empleados disponibles para autocompletado |

## Modelo de Relación Usuario-Empleado

El vínculo está definido en `cuentas/models.py`.

```python
class UsuarioEmpleado(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil_empleado',
    )
    empleado = models.OneToOneField(
        Empleado,
        on_delete=models.PROTECT,
        related_name='cuenta_usuario',
    )
```

Reglas:

| Relación | Regla |
|---|---|
| `User -> UsuarioEmpleado` | Un usuario tiene como máximo un empleado vinculado |
| `Empleado -> UsuarioEmpleado` | Un empleado tiene como máximo una cuenta de usuario |
| Eliminación de usuario | El vínculo se elimina por `CASCADE` |
| Eliminación de empleado | Protegida por `PROTECT` si tiene usuario vinculado |

Accesos comunes:

```python
usuario.perfil_empleado.empleado
empleado.cuenta_usuario.usuario
```

## Roles del Sistema

Los roles se manejan con grupos Django.

Constantes actuales en `cuentas/roles.py`:

```python
ROLE_ADMIN = 'admin'
ROLE_RECEPCIONISTA = 'recepcionista'
ROLE_HOUSEKEEPING = 'housekeeping'
```

Helpers disponibles:

| Helper | Uso |
|---|---|
| `user_has_role(user, role)` | Valida si el usuario tiene un rol |
| `user_has_any_role(user, roles)` | Valida si tiene alguno de los roles indicados |

Regla especial:

- `user.is_superuser` cuenta como `admin` cuando se valida `ROLE_ADMIN`.

## Permisos del CRUD

Todas las vistas del CRUD de usuarios requieren rol `admin`.

Implementación:

```python
@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioListView(ListView):
    ...
```

El decorador `role_required` combina:

- `login_required`
- `user_passes_test`
- `PermissionDenied` si el usuario autenticado no tiene el rol requerido

Resultado esperado:

| Caso | Resultado |
|---|---|
| Usuario anónimo | Redirección a `login` |
| Usuario autenticado sin rol admin | Error 403 |
| Usuario admin | Acceso permitido |

## Rutas

Las rutas viven en `cuentas/urls.py` y se montan desde `config/urls.py` bajo `/usuarios/`.

```python
path('usuarios/', include('cuentas.urls'))
```

| Nombre | Método | URL | Vista |
|---|---|---|---|
| `usuarios:list` | `GET` | `/usuarios/` | `UsuarioListView` |
| `usuarios:create` | `GET`, `POST` | `/usuarios/crear/` | `UsuarioCreateView` |
| `usuarios:detail` | `GET` | `/usuarios/<pk>/` | `UsuarioDetailView` |
| `usuarios:update` | `GET`, `POST` | `/usuarios/<pk>/editar/` | `UsuarioUpdateView` |
| `usuarios:delete` | `GET`, `POST` | `/usuarios/<pk>/eliminar/` | `UsuarioDeleteView` |

Usar siempre `{% url 'usuarios:nombre' %}` o `reverse_lazy('usuarios:nombre')`. No hardcodear rutas.

## Listado de Usuarios

Vista:

```python
class UsuarioListView(ListView):
    model = User
    template_name = 'cuentas/usuarios/list.html'
    context_object_name = 'usuarios'
    paginate_by = 10
```

Queryset:

```python
User.objects.select_related('perfil_empleado__empleado').prefetch_related('groups').order_by('username')
```

El listado muestra:

- Usuario.
- Empleado vinculado.
- Correo.
- Roles/grupos.
- Estado activo/inactivo.
- Acciones de ver, editar y eliminar.

Las acciones del listado usan iconos Bootstrap Icons con `title` y `aria-label` para accesibilidad.

## Detalle de Usuario

Vista:

```python
class UsuarioDetailView(DetailView):
    model = User
    template_name = 'cuentas/usuarios/detail.html'
    context_object_name = 'usuario'
```

Queryset:

```python
User.objects.select_related('perfil_empleado__empleado').prefetch_related('groups')
```

El detalle muestra:

- Información de cuenta: username, último acceso y fecha de registro.
- Empleado vinculado: código, nombres, apellidos, cargo, correo y teléfono.
- Estado de acceso: activo/inactivo, superusuario y roles.

## Creación de Usuario

Vista:

```python
class UsuarioCreateView(CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = 'cuentas/usuarios/form.html'
    success_url = reverse_lazy('usuarios:list')
```

Formulario:

```python
class UsuarioCreateForm(BootstrapFormMixin, UserCreationForm):
    empleado = forms.ModelChoiceField(...)
    groups = forms.ModelMultipleChoiceField(...)
    is_active = forms.BooleanField(...)
```

Campos principales:

| Campo | Uso |
|---|---|
| `empleado` | Empleado activo disponible para vincular |
| `username` | Nombre de usuario Django |
| `password1` | Contraseña |
| `password2` | Confirmación de contraseña |
| `groups` | Roles/grupos del sistema |
| `is_active` | Estado de acceso |

Reglas al guardar:

- `first_name` se toma desde `empleado.nombres`.
- `last_name` se toma desde `empleado.apellidos`.
- `email` se toma desde `empleado.email`.
- `is_staff` se activa si el usuario tiene el grupo `admin`.
- Se crea `UsuarioEmpleado(usuario=user, empleado=empleado)`.

Mensaje de éxito:

```text
Usuario creado correctamente.
```

## Edición de Usuario

Vista:

```python
class UsuarioUpdateView(UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = 'cuentas/usuarios/form.html'
    success_url = reverse_lazy('usuarios:list')
```

Formulario:

```python
class UsuarioUpdateForm(BootstrapFormMixin, forms.ModelForm):
    empleado = forms.ModelChoiceField(...)
    groups = forms.ModelMultipleChoiceField(...)
```

Diferencias frente a creación:

- No edita contraseña.
- Mantiene el empleado actual como opción válida.
- Permite cambiar a otro empleado activo sin cuenta vinculada.
- Actualiza o crea el vínculo con `UsuarioEmpleado.objects.update_or_create()`.

Reglas al guardar:

- Sincroniza nombres, apellidos y correo desde el empleado seleccionado.
- Recalcula `is_staff` según pertenencia al grupo `admin`.
- Guarda roles mediante `save_m2m()`.

Mensaje de éxito:

```text
Usuario actualizado correctamente.
```

## Eliminación de Usuario

Vista:

```python
class UsuarioDeleteView(DeleteView):
    model = User
    template_name = 'cuentas/usuarios/confirm_delete.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('usuarios:list')
```

Regla de seguridad:

- Un usuario no puede eliminarse a sí mismo desde esta pantalla.

Implementación:

```python
def dispatch(self, request, *args, **kwargs):
    self.object = self.get_object()
    if self.object == request.user:
        messages.error(request, 'No puedes eliminar tu propio usuario.')
        return self.get(request, *args, **kwargs)
    return super().dispatch(request, *args, **kwargs)
```

Mensaje de éxito:

```text
Usuario eliminado correctamente.
```

## Autocompletado de Empleados

El campo `empleado` del formulario usa Tom Select y consume un endpoint API interno.

Endpoint:

```http
GET /api/v1/empleados/disponibles-para-usuario/
```

URL usada en template:

```django
{% url 'api:empleados_disponibles_usuario' %}
```

Fetch actual:

```javascript
fetch(tomSelect.getUrl(query), {
    credentials: 'same-origin',
    headers: { 'Accept': 'application/json' },
})
```

Parámetros enviados:

| Parámetro | Uso |
|---|---|
| `search` | Texto escrito por el usuario |
| `page_size` | Actualmente `15` |

Respuesta esperada:

```json
{
  "results": [
    {
      "id": 1,
      "text": "Ana Perez",
      "codigo": "EMP001",
      "email": "ana@example.com",
      "cargo_display": "Recepcionista"
    }
  ],
  "next": null
}
```

El serializer completo está documentado en `Docs/api.md`.

## Templates

| Template | Uso |
|---|---|
| `templates/cuentas/usuarios/list.html` | Tabla paginada de usuarios |
| `templates/cuentas/usuarios/detail.html` | Detalle de cuenta y empleado vinculado |
| `templates/cuentas/usuarios/form.html` | Creación y edición |
| `templates/cuentas/usuarios/confirm_delete.html` | Confirmación de eliminación |

Reglas de UI:

- Usar Bootstrap Icons para acciones y estados.
- En listados, las acciones CRUD deben mostrarse como iconos con `aria-label`.
- Mantener el paginador integrado como footer de tabla usando `partials/pagination.html`.
- Mantener mensajes usando `partials/messages.html`.

## Mensajes del Módulo

| Acción | Tipo | Mensaje |
|---|---|---|
| Crear | `success` | `Usuario creado correctamente.` |
| Editar | `success` | `Usuario actualizado correctamente.` |
| Eliminar | `success` | `Usuario eliminado correctamente.` |
| Autoeliminación bloqueada | `error` | `No puedes eliminar tu propio usuario.` |

## Reglas Para Desarrolladores

- No crear usuarios sin empleado vinculado desde este CRUD.
- No permitir vincular un empleado inactivo.
- No permitir vincular un empleado que ya tenga cuenta, salvo que sea el empleado actual en edición.
- No duplicar lógica de roles fuera de `cuentas/roles.py`.
- No hardcodear nombres de roles en templates.
- Si se agrega un nuevo rol, actualizar `SYSTEM_ROLES`, grupos seed/migraciones si aplican, documentación y permisos asociados.
- Si se cambia el endpoint de autocompletado, actualizar `form.html` y `Docs/api.md`.
- Si se agrega búsqueda al listado, conservar paginación y parámetros de query.
- No eliminar usuarios con historial operativo sin validar impacto funcional.

## Checklist al Modificar Usuarios

- Usuario admin puede listar usuarios.
- Usuario sin rol admin recibe 403.
- Usuario anónimo redirige a login.
- Creación exige empleado activo disponible.
- Creación copia nombres, apellidos y correo desde empleado.
- Edición mantiene el empleado actual como opción válida.
- Edición actualiza roles y `is_staff` correctamente.
- No se puede eliminar el usuario autenticado actual.
- El autocompletado carga empleados con sesión Django.
- El paginador sigue mostrando conteo y navegación.
- `python manage.py check` no reporta errores.
