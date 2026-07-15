from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase

from config.choices import CargoEmpleado, EstadoGeneral
from cuentas.exceptions import EmpleadoNoDisponible, UsuarioNoDesactivable
from cuentas.models import UsuarioEmpleado
from cuentas.services import UsuarioService
from empleados.models import Empleado


class UsuarioServiceTests(TestCase):
    def setUp(self):
        self.grupo_admin = Group.objects.get(name='admin')
        self.actor = User.objects.create_user(username='lider', password='test123')
        self.empleado = Empleado.objects.create(
            codigo='EMP-9001',
            nombres='Jean',
            apellidos='Senador',
            cargo=CargoEmpleado.ADMINISTRADOR,
            email='jean@example.com',
            estado=EstadoGeneral.ACTIVO,
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
