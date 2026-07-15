from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from config.choices import CargoEmpleado, EstadoGeneral
from cuentas.exceptions import EmpleadoNoDisponible, RolUsuarioInvalido, UsuarioNoDesactivable
from cuentas.models import UsuarioEmpleado
from cuentas.services import UsuarioService
from empleados.models import Empleado


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
