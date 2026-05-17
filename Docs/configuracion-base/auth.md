# Auth - Login y Logout

Este documento describe la configuración base de autenticación web en HotelSys para login y logout usando Django Authentication, sesiones y mensajes del framework.

La autenticación de pantallas administrativas funciona con vistas Django tradicionales. La autenticación JWT para API está documentada en `Docs/api.md`.

## Archivos Principales

| Archivo | Responsabilidad |
|---|---|
| `config/urls.py` | Registra las rutas globales `/login/` y `/logout/` |
| `config/settings.py` | Define redirects base de autenticación |
| `cuentas/views.py` | Implementa `CuentaLoginView` y `CuentaLogoutView` |
| `templates/cuentas/login.html` | Template de inicio de sesión |
| `templates/partials/navbar.html` | Formulario POST de cierre de sesión |

## Settings Base

Configuración actual en `config/settings.py`:

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'
```

Significado:

| Setting | Uso |
|---|---|
| `LOGIN_URL` | Ruta a la que Django redirige cuando una vista requiere autenticación |
| `LOGIN_REDIRECT_URL` | Ruta por defecto después de iniciar sesión |
| `LOGOUT_REDIRECT_URL` | Ruta por defecto después de cerrar sesión |

## Rutas

Las rutas de login/logout están registradas directamente en `config/urls.py`.

```python
path('login/', CuentaLoginView.as_view(), name='login')
path('logout/', CuentaLogoutView.as_view(), name='logout')
```

| Nombre | Método | URL | Vista |
|---|---|---|---|
| `login` | `GET`, `POST` | `/login/` | `CuentaLoginView` |
| `logout` | `POST`, `OPTIONS` | `/logout/` | `CuentaLogoutView` |

No mover estas rutas a `cuentas/urls.py` sin actualizar `LOGIN_URL`, `LOGOUT_REDIRECT_URL`, templates y referencias existentes.

## Login

La vista está en `cuentas/views.py`.

```python
class CuentaLoginView(LoginView):
    template_name = 'cuentas/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('home')
```

Comportamiento:

| Caso | Resultado |
|---|---|
| Usuario anónimo abre `/login/` | Muestra `templates/cuentas/login.html` |
| Credenciales válidas | Inicia sesión y redirige a `next` o `home` |
| Credenciales inválidas | Permanece en login y muestra mensaje de error |
| Usuario autenticado abre `/login/` | Redirige automáticamente por `redirect_authenticated_user = True` |

### Parámetro `next`

Si una vista protegida redirige al login, Django agrega `next`.

Ejemplo:

```text
/login/?next=/usuarios/
```

El template conserva ese valor:

```django
{% if next %}
    <input type="hidden" name="next" value="{{ next }}">
{% endif %}
```

Después de autenticar correctamente, `get_success_url()` prioriza `next` mediante `get_redirect_url()`.

### Mensajes de Login

La vista usa `django.contrib.messages`.

```python
def form_valid(self, form):
    messages.success(self.request, 'Inicio de sesión correcto.')
    return super().form_valid(form)

def form_invalid(self, form):
    messages.error(self.request, 'Usuario o contraseña inválidos.')
    return super().form_invalid(form)
```

Mensajes actuales:

| Evento | Tipo | Mensaje |
|---|---|---|
| Login correcto | `success` | `Inicio de sesión correcto.` |
| Login inválido | `error` | `Usuario o contraseña inválidos.` |

## Template de Login

Template:

```text
templates/cuentas/login.html
```

Requisitos del formulario:

- Debe usar `method="post"`.
- Debe incluir `{% csrf_token %}`.
- Debe enviar campos `username` y `password` con los nombres del form Django.
- Debe preservar `next` cuando exista.

Estructura relevante:

```django
<form method="post" novalidate>
    {% csrf_token %}
    {% if next %}
        <input type="hidden" name="next" value="{{ next }}">
    {% endif %}

    <input type="text" name="{{ form.username.html_name }}">
    <input type="password" name="{{ form.password.html_name }}">

    <button type="submit">Ingresar</button>
</form>
```

El login usa Bootstrap y Bootstrap Icons por CDN, además de estilos del sistema en `static/css/styles.css`.

## Logout

La vista está en `cuentas/views.py`.

```python
class CuentaLogoutView(LogoutView):
    http_method_names = ['post', 'options']
    next_page = reverse_lazy('login')
```

Comportamiento:

| Caso | Resultado |
|---|---|
| `POST /logout/` válido | Cierra sesión y redirige a login |
| `GET /logout/` | No está permitido |
| Después de cerrar sesión | Muestra mensaje informativo |

El logout debe hacerse por POST para evitar cierres de sesión accidentales por enlaces, crawlers o precargas del navegador.

### Formulario de Logout

El logout se ejecuta desde el navbar con un formulario POST.

```django
<form action="{% url 'logout' %}" method="post" class="mt-3">
    {% csrf_token %}
    <button class="btn btn-sm btn-outline-light w-100" type="submit">
        Salir
    </button>
</form>
```

Reglas:

- No usar `<a href="{% url 'logout' %}">` para cerrar sesión.
- Siempre incluir `{% csrf_token %}`.
- Mantener `method="post"`.

### Mensaje de Logout

La vista agrega un mensaje informativo después de cerrar sesión.

```python
def post(self, request, *args, **kwargs):
    response = super().post(request, *args, **kwargs)
    messages.info(request, 'Sesión cerrada correctamente.')
    return response
```

Mensaje actual:

| Evento | Tipo | Mensaje |
|---|---|---|
| Logout correcto | `info` | `Sesión cerrada correctamente.` |

## Protección de Vistas

Para vistas basadas en clases que requieren autenticación o rol, usar los decoradores/helpers existentes del proyecto.

Ejemplo de vista protegida por rol:

```python
from django.utils.decorators import method_decorator

from cuentas.decorators import role_required
from cuentas.roles import ROLE_ADMIN


@method_decorator(role_required(ROLE_ADMIN), name='dispatch')
class UsuarioListView(ListView):
    ...
```

Cuando una vista protegida detecta usuario no autenticado, debe redirigir al login usando `LOGIN_URL`.

## Flujo Completo

Login correcto:

```text
GET /login/
POST /login/
Credenciales validas
Sesion Django creada
Mensaje success
Redirect a next o home
```

Login inválido:

```text
GET /login/
POST /login/
Credenciales invalidas
Mensaje error
Render de templates/cuentas/login.html
```

Logout:

```text
POST /logout/
Sesion Django cerrada
Mensaje info
Redirect a /login/
```

## Reglas Para Desarrolladores

- Mantener login/logout web separados de la autenticación JWT de API.
- No exponer logout por GET.
- No duplicar rutas de login/logout dentro de apps sin una razón concreta.
- Usar `reverse_lazy('login')`, `reverse_lazy('home')` o `{% url 'login' %}` en vez de URLs hardcodeadas.
- Preservar soporte de `next` en el formulario de login.
- Mantener mensajes de autenticación mediante `django.contrib.messages`.
- Si se cambia el template de login, conservar nombres de campos enviados por `LoginView`.
- Si se cambia `LOGIN_URL`, revisar decoradores, redirects y templates.

## Checklist al Modificar Auth

- `GET /login/` renderiza correctamente.
- `POST /login/` con credenciales válidas redirige a `home` o `next`.
- `POST /login/` con credenciales inválidas muestra error.
- Usuario autenticado no puede quedarse en `/login/`.
- `POST /logout/` cierra sesión.
- `GET /logout/` no se usa en templates ni navegación.
- Los formularios incluyen CSRF.
- `python manage.py check` no reporta errores.
