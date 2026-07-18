from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from config.choices import CargoEmpleado, EstadoGeneral
from cuentas.exceptions import EmpleadoNoDisponible, RolUsuarioInvalido, UsuarioDuplicado, UsuarioNoDesactivable
from cuentas.models import AuditoriaSesion, MotivoExpiracionSesion, UsuarioEmpleado
from cuentas.session_audit import registrar_expiracion_sesion
from cuentas.session_policy import get_session_policy
from cuentas.session_state import SESSION_LAST_ACTIVITY_AT, SESSION_STARTED_AT
from cuentas.services import UsuarioService
from empleados.models import Empleado


SESSION_ROLE_POLICIES = {
    'admin': {'idle_timeout': 900, 'absolute_timeout': 28800},
    'recepcionista': {'idle_timeout': 1200, 'absolute_timeout': 43200},
    'housekeeping': {'idle_timeout': 900, 'absolute_timeout': 28800},
    'default': {'idle_timeout': 900, 'absolute_timeout': 28800},
}


@override_settings(SESSION_ROLE_POLICIES=SESSION_ROLE_POLICIES)
class SessionPolicyTests(TestCase):
    def setUp(self):
        self.admin_group = Group.objects.get(name='admin')
        self.recepcion_group = Group.objects.get(name='recepcionista')
        self.housekeeping_group = Group.objects.get(name='housekeeping')

    def test_aplica_politica_de_recepcionista(self):
        user = User.objects.create_user(username='recepcion', password='testpass123')
        user.groups.add(self.recepcion_group)

        policy = get_session_policy(user)

        self.assertEqual(policy.idle_timeout, 1200)
        self.assertEqual(policy.absolute_timeout, 43200)
        self.assertEqual(policy.roles, ('recepcionista',))

    def test_aplica_politica_de_housekeeping(self):
        user = User.objects.create_user(username='limpieza', password='testpass123')
        user.groups.add(self.housekeeping_group)

        policy = get_session_policy(user)

        self.assertEqual(policy.idle_timeout, 900)
        self.assertEqual(policy.absolute_timeout, 28800)
        self.assertEqual(policy.roles, ('housekeeping',))

    def test_recalcula_la_politica_cuando_cambia_el_rol(self):
        user = User.objects.create_user(username='multirole', password='testpass123')
        user.groups.add(self.recepcion_group)

        self.assertEqual(get_session_policy(user).idle_timeout, 1200)

        user.groups.add(self.admin_group)
        policy = get_session_policy(user)

        self.assertEqual(policy.idle_timeout, 900)
        self.assertEqual(policy.absolute_timeout, 28800)
        self.assertEqual(policy.roles, ('admin', 'recepcionista'))

    def test_superusuario_usa_politica_de_admin(self):
        user = User.objects.create_superuser(username='root', email='root@example.com', password='testpass123')

        policy = get_session_policy(user)

        self.assertEqual(policy.idle_timeout, 900)
        self.assertEqual(policy.absolute_timeout, 28800)
        self.assertEqual(policy.roles, ('admin',))

    def test_usuario_sin_rol_usa_politica_predeterminada(self):
        user = User.objects.create_user(username='sin-rol', password='testpass123')

        policy = get_session_policy(user)

        self.assertEqual(policy.idle_timeout, 900)
        self.assertEqual(policy.absolute_timeout, 28800)
        self.assertEqual(policy.roles, ())

    def test_registra_auditoria_sin_parametros_de_la_ruta(self):
        user = User.objects.create_user(username='admin', password='testpass123')
        user.groups.add(self.admin_group)

        audit = registrar_expiracion_sesion(
            user=user,
            policy=get_session_policy(user),
            motivo=MotivoExpiracionSesion.INACTIVIDAD,
            ruta='/reservas/?huesped_id=42&session_key=secret',
        )

        self.assertEqual(AuditoriaSesion.objects.count(), 1)
        self.assertEqual(audit.usuario, user)
        self.assertEqual(audit.roles_efectivos, 'admin')
        self.assertEqual(audit.motivo, MotivoExpiracionSesion.INACTIVIDAD)
        self.assertEqual(audit.ruta, '/reservas/')


@override_settings(
    SESSION_ROLE_POLICIES={
        'admin': {'idle_timeout': 60, 'absolute_timeout': 600},
        'recepcionista': {'idle_timeout': 120, 'absolute_timeout': 1200},
        'housekeeping': {'idle_timeout': 60, 'absolute_timeout': 600},
        'default': {'idle_timeout': 60, 'absolute_timeout': 600},
    },
)
class SessionExpirationTests(TestCase):
    def setUp(self):
        self.admin_group = Group.objects.get(name='admin')
        self.recepcion_group = Group.objects.get(name='recepcionista')
        self.user = User.objects.create_user(username='admin-sesion', password='testpass123')
        self.user.groups.add(self.admin_group)

    def authenticate(self, user=None):
        self.client.force_login(user or self.user)

    def set_session_timestamps(self, *, started_at, last_activity_at):
        session = self.client.session
        session[SESSION_STARTED_AT] = int(started_at.timestamp())
        session[SESSION_LAST_ACTIVITY_AT] = int(last_activity_at.timestamp())
        session.save()

    def test_login_inicializa_las_marcas_de_sesion(self):
        self.authenticate()

        self.assertIsInstance(self.client.session[SESSION_STARTED_AT], int)
        self.assertIsInstance(self.client.session[SESSION_LAST_ACTIVITY_AT], int)

    def test_expira_por_inactividad_y_registra_auditoria(self):
        self.authenticate()
        now = timezone.now()
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=30),
            last_activity_at=now - timedelta(seconds=61),
        )

        response = self.client.get(reverse('usuarios:list'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
        audit = AuditoriaSesion.objects.get()
        self.assertEqual(audit.motivo, MotivoExpiracionSesion.INACTIVIDAD)
        self.assertEqual(audit.ruta, reverse('usuarios:list'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_expira_por_limite_absoluto_aunque_haya_actividad_reciente(self):
        self.authenticate()
        now = timezone.now()
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=601),
            last_activity_at=now,
        )

        response = self.client.get(reverse('usuarios:list'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            AuditoriaSesion.objects.get().motivo,
            MotivoExpiracionSesion.LIMITE_ABSOLUTO,
        )

    def test_cambio_de_rol_aplica_la_politica_mas_restrictiva_en_la_siguiente_solicitud(self):
        user = User.objects.create_user(username='recepcion-sesion', password='testpass123')
        user.groups.add(self.recepcion_group)
        self.authenticate(user)
        now = timezone.now()
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=30),
            last_activity_at=now - timedelta(seconds=61),
        )
        user.groups.add(self.admin_group)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(
            AuditoriaSesion.objects.get().motivo,
            MotivoExpiracionSesion.INACTIVIDAD,
        )

    def test_navegacion_html_renueva_la_actividad(self):
        self.authenticate()
        now = timezone.now()
        previous_activity = now - timedelta(seconds=30)
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=60),
            last_activity_at=previous_activity,
        )

        response = self.client.get(reverse('usuarios:list'))

        self.assertEqual(response.status_code, 200)
        self.assertGreater(self.client.session[SESSION_LAST_ACTIVITY_AT], int(previous_activity.timestamp()))

    def test_renderiza_el_aviso_de_expiracion_para_sesiones_activas(self):
        self.authenticate()

        response = self.client.get(reverse('usuarios:list'))

        self.assertContains(response, 'id="session-timeout-modal"')
        self.assertContains(response, 'data-session-expires-at=')
        self.assertContains(response, 'data-session-continue')
        self.assertContains(response, 'src="/static/js/session.')

    def test_endpoint_de_actividad_renueva_solo_el_tiempo_inactivo(self):
        self.authenticate()
        now = timezone.now()
        started_at = now - timedelta(seconds=30)
        previous_activity = now - timedelta(seconds=30)
        self.set_session_timestamps(
            started_at=started_at,
            last_activity_at=previous_activity,
        )

        response = self.client.post(reverse('session_activity'), HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertGreater(self.client.session[SESSION_LAST_ACTIVITY_AT], int(previous_activity.timestamp()))
        self.assertEqual(self.client.session[SESSION_STARTED_AT], int(started_at.timestamp()))
        self.assertIn('expires_at', response.json())

    def test_solicitud_json_expirada_recibe_401_estandar(self):
        self.authenticate()
        now = timezone.now()
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=30),
            last_activity_at=now - timedelta(seconds=61),
        )

        response = self.client.post(reverse('session_activity'), HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], 'session_expired')

    def test_rutas_api_no_renuevan_la_actividad(self):
        self.authenticate()
        now = timezone.now()
        previous_activity = now - timedelta(seconds=30)
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=60),
            last_activity_at=previous_activity,
        )

        self.client.get('/api/v1/reservas/huespedes-autocomplete/', HTTP_ACCEPT='application/json')

        self.assertEqual(
            self.client.session[SESSION_LAST_ACTIVITY_AT],
            int(previous_activity.timestamp()),
        )

    def test_sesion_sin_marcas_se_invalida_como_heredada(self):
        self.client.force_login(self.user)
        session = self.client.session
        session.pop(SESSION_STARTED_AT, None)
        session.pop(SESSION_LAST_ACTIVITY_AT, None)
        session.save()

        response = self.client.get(reverse('usuarios:list'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            AuditoriaSesion.objects.get().motivo,
            MotivoExpiracionSesion.SESION_LEGADA,
        )

    def test_ruta_de_retorno_permanece_interna(self):
        self.authenticate()
        now = timezone.now()
        self.set_session_timestamps(
            started_at=now - timedelta(seconds=30),
            last_activity_at=now - timedelta(seconds=61),
        )

        response = self.client.get(f'{reverse("usuarios:list")}?next=https://evil.example')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
        self.assertFalse(response.url.startswith('https://evil.example'))

    def test_endpoint_de_actividad_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(reverse('session_activity'), HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 403)


class UsuarioServiceTests(TestCase):
    def setUp(self):
        self.grupo_admin = Group.objects.get(name='admin')
        self.actor = User.objects.create_user(username='lider', password='test123')
        self.empleado = self._crear_empleado(
            codigo='EMP-9001',
            nombres='Jean',
            apellidos='Senador',
            email='jean@example.com',
        )

    def _crear_empleado(self, *, codigo, nombres, apellidos, email, estado=EstadoGeneral.ACTIVO):
        return Empleado.objects.create(
            codigo=codigo,
            nombres=nombres,
            apellidos=apellidos,
            cargo=CargoEmpleado.ADMINISTRADOR,
            email=email,
            estado=estado,
            fecha_ingreso=date.today(),
        )

    def test_crear_usuario_crea_perfil_con_auditoria(self):
        user = UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[self.grupo_admin],
            usuario_actor=self.actor,
        )

        perfil = UsuarioEmpleado.objects.get(usuario=user)
        self.assertEqual(perfil.empleado, self.empleado)
        self.assertEqual(perfil.creado_por, self.actor)
        self.assertTrue(user.is_staff)

    def test_crear_usuario_rechaza_empleado_ya_vinculado(self):
        UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[],
        )

        with self.assertRaises(EmpleadoNoDisponible):
            UsuarioService.crear_usuario(
                username='otro',
                password='test12345',
                empleado=self.empleado,
                groups=[],
            )

    def test_crear_usuario_rechaza_username_duplicado(self):
        User.objects.create_user(username='jean', password='test12345')

        with self.assertRaises(UsuarioDuplicado):
            UsuarioService.crear_usuario(
                username='jean',
                password='test12345',
                empleado=self.empleado,
                groups=[],
            )

    def test_crear_usuario_rechaza_empleado_inactivo(self):
        empleado_inactivo = self._crear_empleado(
            codigo='EMP-9004',
            nombres='Empleado',
            apellidos='Inactivo',
            email='empleado-inactivo@example.com',
            estado=EstadoGeneral.INACTIVO,
        )

        with self.assertRaises(EmpleadoNoDisponible):
            UsuarioService.crear_usuario(
                username='inactivo',
                password='test12345',
                empleado=empleado_inactivo,
                groups=[],
            )

    def test_crear_usuario_rechaza_rol_no_permitido(self):
        grupo_invalido = Group.objects.create(name='contabilidad')

        with self.assertRaises(RolUsuarioInvalido):
            UsuarioService.crear_usuario(
                username='jean',
                password='test12345',
                empleado=self.empleado,
                groups=[grupo_invalido],
            )

    def test_empleados_disponibles_excluye_empleado_con_cuenta_historica(self):
        user = UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[],
        )
        UsuarioService.desactivar_usuario(user=user, usuario_actor=self.actor)

        queryset = UsuarioService.empleados_disponibles_queryset()

        self.assertNotIn(self.empleado, queryset)

    def test_empleados_disponibles_incluye_empleado_actual_en_edicion(self):
        UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[],
        )

        queryset = UsuarioService.empleados_disponibles_queryset(
            empleado_actual=self.empleado,
        )

        self.assertIn(self.empleado, queryset)

    def test_desactivar_usuario_aplica_soft_delete_al_perfil(self):
        user = UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[],
        )

        UsuarioService.desactivar_usuario(user=user, usuario_actor=self.actor)

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(UsuarioEmpleado.objects.filter(usuario=user).exists())
        self.assertTrue(UsuarioEmpleado.todos.filter(usuario=user, activo=False).exists())

    def test_desactivar_usuario_rechaza_usuario_actual(self):
        with self.assertRaises(UsuarioNoDesactivable):
            UsuarioService.desactivar_usuario(user=self.actor, usuario_actor=self.actor)

    def test_reactivar_usuario_activa_usuario_y_perfil_historico(self):
        user = UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[],
        )
        UsuarioService.desactivar_usuario(user=user, usuario_actor=self.actor)

        UsuarioService.reactivar_usuario(user=user, usuario_actor=self.actor)

        user.refresh_from_db()
        perfil = UsuarioEmpleado.todos.get(usuario=user)
        self.assertTrue(user.is_active)
        self.assertTrue(perfil.activo)

    def test_reactivar_usuario_rechaza_empleado_inactivo(self):
        user = UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[],
        )
        UsuarioService.desactivar_usuario(user=user, usuario_actor=self.actor)
        self.empleado.estado = EstadoGeneral.INACTIVO
        self.empleado.save(update_fields=['estado'])

        with self.assertRaises(EmpleadoNoDisponible):
            UsuarioService.reactivar_usuario(user=user, usuario_actor=self.actor)

    def test_actualizar_usuario_rechaza_auto_desactivacion(self):
        self.actor.groups.add(self.grupo_admin)
        empleado_actor = self._crear_empleado(
            codigo='EMP-9002',
            nombres='Lider',
            apellidos='Admin',
            email='lider@example.com',
        )
        UsuarioEmpleado.objects.create(usuario=self.actor, empleado=empleado_actor)

        with self.assertRaises(UsuarioNoDesactivable):
            UsuarioService.actualizar_usuario(
                user=self.actor,
                username=self.actor.username,
                empleado=empleado_actor,
                groups=[self.grupo_admin],
                is_active=False,
                usuario_actor=self.actor,
            )

    def test_actualizar_usuario_rechaza_quitarse_rol_admin(self):
        self.actor.groups.add(self.grupo_admin)
        empleado_actor = self._crear_empleado(
            codigo='EMP-9003',
            nombres='Lider',
            apellidos='Admin',
            email='lider-admin@example.com',
        )
        UsuarioEmpleado.objects.create(usuario=self.actor, empleado=empleado_actor)

        with self.assertRaises(UsuarioNoDesactivable):
            UsuarioService.actualizar_usuario(
                user=self.actor,
                username=self.actor.username,
                empleado=empleado_actor,
                groups=[],
                is_active=True,
                usuario_actor=self.actor,
            )

    def test_actualizar_usuario_rechaza_dejar_sistema_sin_admins(self):
        admin_user = UsuarioService.crear_usuario(
            username='jean',
            password='test12345',
            empleado=self.empleado,
            groups=[self.grupo_admin],
        )

        with self.assertRaises(UsuarioNoDesactivable):
            UsuarioService.actualizar_usuario(
                user=admin_user,
                username=admin_user.username,
                empleado=self.empleado,
                groups=[],
                is_active=True,
            )


@override_settings(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'cuentas-login-tests',
        },
    },
    LOGIN_RATE_LIMIT_ATTEMPTS=3,
    LOGIN_RATE_LIMIT_WINDOW=60,
)
class CuentaLoginViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='recepcion', password='testpass123')

    def post_login(self, username, password, ip_address='198.51.100.10'):
        return self.client.post(
            reverse('login'),
            {'username': username, 'password': password},
            REMOTE_ADDR=ip_address,
        )

    def test_login_muestra_control_accesible_para_ver_contrasena(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, 'src="/static/js/auth.js"')
        self.assertContains(response, 'data-password-toggle')
        self.assertContains(response, 'aria-controls="id_password"')
        self.assertContains(response, 'aria-pressed="false"')
        self.assertContains(response, 'aria-label="Mostrar contraseña"')
        self.assertNotContains(response, 'novalidate')

    def test_login_invalido_anuncia_y_asocia_el_error_con_los_campos(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.user.username, 'password': 'contrasena-incorrecta'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="login-errors"')
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'aria-invalid="true"', count=2)
        self.assertContains(response, 'aria-describedby="login-errors"', count=2)
        self.assertContains(response, 'is-invalid', count=2)

    def test_login_asocia_los_errores_requeridos_con_sus_campos(self):
        response = self.client.post(reverse('login'), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="username-errors"')
        self.assertContains(response, 'id="password-errors"')
        self.assertContains(response, 'aria-describedby="username-errors"')
        self.assertContains(response, 'aria-describedby="password-errors"')
        self.assertContains(response, 'aria-invalid="true"', count=2)

    def test_login_valido_crea_la_sesion(self):
        response = self.post_login(self.user.username, 'testpass123')

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.assertIn('_auth_user_id', self.client.session)

    def test_bloquea_intentos_excesivos_con_la_misma_respuesta_generica(self):
        for _ in range(3):
            response = self.post_login(self.user.username, 'contrasena-incorrecta')
            self.assertEqual(response.status_code, 200)

        response = self.post_login(self.user.username, 'testpass123')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña inválidos.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_limite_por_usuario_aplica_desde_otra_ip(self):
        for _ in range(3):
            self.post_login(self.user.username, 'contrasena-incorrecta', '198.51.100.10')

        response = self.post_login(self.user.username, 'testpass123', '203.0.113.10')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_limite_por_ip_aplica_con_usuarios_distintos(self):
        for username in ('usuario-1', 'usuario-2', 'usuario-3'):
            self.post_login(username, 'contrasena-incorrecta')

        response = self.post_login(self.user.username, 'testpass123')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inicio_exitoso_reinicia_los_contadores(self):
        self.post_login(self.user.username, 'contrasena-incorrecta')
        response = self.post_login(self.user.username, 'testpass123')

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.client.logout()

        self.post_login(self.user.username, 'contrasena-incorrecta')
        self.post_login(self.user.username, 'contrasena-incorrecta')
        response = self.post_login(self.user.username, 'testpass123')

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)


class UsuarioViewsTests(TestCase):
    def setUp(self):
        self.grupo_admin = Group.objects.get(name='admin')
        self.admin = User.objects.create_user(username='admin-test', password='test123')
        self.admin.groups.add(self.grupo_admin)
        self.empleado_admin = Empleado.objects.create(
            codigo='EMP-9100',
            nombres='Admin',
            apellidos='Sistema',
            cargo=CargoEmpleado.ADMINISTRADOR,
            email='admin-test@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )
        UsuarioEmpleado.objects.create(usuario=self.admin, empleado=self.empleado_admin)

        empleado_inactivo = Empleado.objects.create(
            codigo='EMP-9101',
            nombres='Usuario',
            apellidos='Inactivo',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='usuario-inactivo@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )
        self.usuario_inactivo = UsuarioService.crear_usuario(
            username='usuario-inactivo',
            password='test12345',
            empleado=empleado_inactivo,
            groups=[],
        )
        UsuarioService.desactivar_usuario(user=self.usuario_inactivo, usuario_actor=self.admin)

    def test_listado_muestra_activar_para_usuario_inactivo(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('usuarios:list'))

        self.assertContains(response, reverse('usuarios:activate', args=[self.usuario_inactivo.pk]))
        self.assertNotContains(response, reverse('usuarios:deactivate', args=[self.usuario_inactivo.pk]))

    def test_detalle_muestra_auditoria_del_perfil(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('usuarios:detail', args=[self.usuario_inactivo.pk]))

        self.assertContains(response, 'Auditoría del perfil')
        self.assertContains(response, 'Perfil activo')
        self.assertContains(response, 'Creado por')
        self.assertContains(response, 'Creado en')
        self.assertContains(response, 'Actualizado en')
