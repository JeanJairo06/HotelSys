from datetime import date

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from config.choices import CargoEmpleado, EstadoGeneral
from cuentas.models import UsuarioEmpleado
from cuentas.services import UsuarioService
from empleados.exceptions import CargoEmpleadoInvalido, DatosEmpleadoInvalidos, EmpleadoDuplicado
from empleados.forms import EmpleadoForm
from empleados.models import Empleado
from empleados.services import EmpleadoService


class EmpleadoModelTests(TestCase):
    def test_normaliza_datos_del_empleado(self):
        empleado = Empleado.objects.create(
            codigo=' emp001 ',
            nombres=' Ana ',
            apellidos=' Torres ',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='ANA.TORRES@EXAMPLE.COM',
            telefono=' 999 888 777 ',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        self.assertEqual(empleado.codigo, 'EMP001')
        self.assertEqual(empleado.nombres, 'Ana')
        self.assertEqual(empleado.apellidos, 'Torres')
        self.assertEqual(empleado.email, 'ana.torres@example.com')
        self.assertEqual(empleado.telefono, '999 888 777')

    def test_genera_codigo_automaticamente(self):
        empleado = Empleado.objects.create(
            nombres='Ana',
            apellidos='Torres',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='ana.codigo@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        self.assertEqual(empleado.codigo, 'EMP-0001')

    def test_incrementa_codigo_automaticamente(self):
        Empleado.objects.create(
            nombres='Ana',
            apellidos='Torres',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='ana.incremento@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )
        empleado = Empleado.objects.create(
            nombres='Luis',
            apellidos='Ramos',
            cargo=CargoEmpleado.HOUSEKEEPING,
            email='luis.incremento@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        self.assertEqual(empleado.codigo, 'EMP-0002')

    def test_formulario_ignora_codigo_manual_al_crear(self):
        form = EmpleadoForm(data={
            'codigo': 'MANUAL',
            'nombres': 'Ana',
            'apellidos': 'Torres',
            'cargo': CargoEmpleado.RECEPCIONISTA,
            'email': 'ana.form@example.com',
            'telefono': '',
            'estado': EstadoGeneral.ACTIVO,
            'fecha_ingreso': date.today().isoformat(),
        })

        self.assertTrue(form.is_valid(), form.errors)
        empleado = form.save()

        self.assertEqual(empleado.codigo, 'EMP-0001')

    def test_formulario_no_expone_estado(self):
        form = EmpleadoForm()

        self.assertNotIn('estado', form.fields)

    def test_formulario_conserva_codigo_al_editar(self):
        empleado = Empleado.objects.create(
            nombres='Ana',
            apellidos='Torres',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='ana.editar@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )
        form = EmpleadoForm(data={
            'codigo': 'MANUAL',
            'nombres': 'Ana Maria',
            'apellidos': 'Torres',
            'cargo': CargoEmpleado.RECEPCIONISTA,
            'email': 'ana.editar@example.com',
            'telefono': '',
            'estado': EstadoGeneral.ACTIVO,
            'fecha_ingreso': date.today().isoformat(),
        }, instance=empleado)

        self.assertTrue(form.is_valid(), form.errors)
        empleado = form.save()

        self.assertEqual(empleado.codigo, 'EMP-0001')
        self.assertEqual(empleado.nombres, 'Ana Maria')

    def test_rechaza_telefono_invalido(self):
        empleado = Empleado(
            codigo='EMP002',
            nombres='Luis',
            apellidos='Ramos',
            cargo=CargoEmpleado.HOUSEKEEPING,
            email='luis.ramos@example.com',
            telefono='abc123',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            empleado.full_clean()

        self.assertIn('telefono', context.exception.message_dict)


class EmpleadoServiceTests(TestCase):
    def setUp(self):
        self.grupo_admin = Group.objects.get(name='admin')
        self.actor = User.objects.create_user(username='admin-servicio', password='test123')
        self.actor.groups.add(self.grupo_admin)

    def _datos_empleado(self, **overrides):
        data = {
            'nombres': 'Ana',
            'apellidos': 'Torres',
            'cargo': CargoEmpleado.RECEPCIONISTA,
            'email': 'ana.service@example.com',
            'telefono': '999888777',
            'estado': EstadoGeneral.ACTIVO,
            'fecha_ingreso': date.today(),
        }
        data.update(overrides)
        return data

    def _crear_usuario_empleado(self, empleado):
        return UsuarioService.crear_usuario(
            username='usuario-empleado',
            password='test12345',
            empleado=empleado,
            groups=[],
            usuario_actor=self.actor,
        )

    def test_crear_empleado_normaliza_y_genera_codigo(self):
        empleado = EmpleadoService.crear_empleado(
            data=self._datos_empleado(
                nombres=' Ana ',
                apellidos=' Torres ',
                email='ANA.SERVICE@EXAMPLE.COM',
                telefono=' 999888777 ',
            )
        )

        self.assertEqual(empleado.codigo, 'EMP-0001')
        self.assertEqual(empleado.nombres, 'Ana')
        self.assertEqual(empleado.apellidos, 'Torres')
        self.assertEqual(empleado.email, 'ana.service@example.com')
        self.assertEqual(empleado.telefono, '999888777')

    def test_actualizar_empleado_conserva_codigo(self):
        empleado = EmpleadoService.crear_empleado(data=self._datos_empleado())

        actualizado = EmpleadoService.actualizar_empleado(
            empleado=empleado,
            data=self._datos_empleado(
                codigo='MANUAL',
                nombres='Ana Maria',
                email='ana.actualizada@example.com',
            ),
        )

        self.assertEqual(actualizado.codigo, 'EMP-0001')
        self.assertEqual(actualizado.nombres, 'Ana Maria')
        self.assertEqual(actualizado.email, 'ana.actualizada@example.com')

    def test_crear_empleado_rechaza_email_duplicado(self):
        EmpleadoService.crear_empleado(data=self._datos_empleado(email='duplicado@example.com'))

        with self.assertRaises(EmpleadoDuplicado):
            EmpleadoService.crear_empleado(
                data=self._datos_empleado(
                    email='DUPLICADO@EXAMPLE.COM',
                    telefono='999111222',
                )
            )

    def test_crear_empleado_rechaza_telefono_duplicado(self):
        EmpleadoService.crear_empleado(data=self._datos_empleado(telefono='999888777'))

        with self.assertRaises(EmpleadoDuplicado):
            EmpleadoService.crear_empleado(
                data=self._datos_empleado(
                    email='otro@example.com',
                    telefono='999888777',
                )
            )

    def test_crear_empleado_rechaza_fecha_futura(self):
        with self.assertRaises(DatosEmpleadoInvalidos):
            EmpleadoService.crear_empleado(
                data=self._datos_empleado(
                    fecha_ingreso=date(date.today().year + 1, 1, 1),
                )
            )

    def test_crear_empleado_rechaza_cargo_invalido(self):
        with self.assertRaises(CargoEmpleadoInvalido):
            EmpleadoService.crear_empleado(data=self._datos_empleado(cargo='CONTABILIDAD'))

    def test_desactivar_empleado_aplica_estado_inactivo_y_soft_delete(self):
        empleado = EmpleadoService.crear_empleado(data=self._datos_empleado())

        EmpleadoService.desactivar_empleado(empleado=empleado)

        empleado.refresh_from_db()
        self.assertEqual(empleado.estado, EstadoGeneral.INACTIVO)
        self.assertFalse(empleado.activo)
        self.assertFalse(Empleado.objects.filter(pk=empleado.pk).exists())
        self.assertTrue(Empleado.todos.filter(pk=empleado.pk).exists())

    def test_desactivar_empleado_desactiva_usuario_asociado(self):
        empleado = EmpleadoService.crear_empleado(data=self._datos_empleado(email='ana.usuario@example.com'))
        user = self._crear_usuario_empleado(empleado)

        EmpleadoService.desactivar_empleado(empleado=empleado, usuario_actor=self.actor)

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(UsuarioEmpleado.objects.filter(usuario=user).exists())
        self.assertTrue(UsuarioEmpleado.todos.filter(usuario=user, empleado=empleado, activo=False).exists())

    def test_activar_empleado_no_reactiva_usuario_asociado(self):
        empleado = EmpleadoService.crear_empleado(data=self._datos_empleado(email='ana.reactivar.usuario@example.com'))
        user = self._crear_usuario_empleado(empleado)
        EmpleadoService.desactivar_empleado(empleado=empleado, usuario_actor=self.actor)

        EmpleadoService.activar_empleado(empleado=empleado, usuario_actor=self.actor)

        user.refresh_from_db()
        perfil = UsuarioEmpleado.todos.get(usuario=user, empleado=empleado)
        self.assertEqual(empleado.estado, EstadoGeneral.ACTIVO)
        self.assertTrue(empleado.activo)
        self.assertFalse(user.is_active)
        self.assertFalse(perfil.activo)

    def test_actualizar_empleado_inactivo_conserva_estado_y_usuario_inactivo(self):
        empleado = EmpleadoService.crear_empleado(data=self._datos_empleado(email='ana.editar.inactiva@example.com'))
        user = self._crear_usuario_empleado(empleado)
        EmpleadoService.desactivar_empleado(empleado=empleado, usuario_actor=self.actor)

        EmpleadoService.actualizar_empleado(
            empleado=empleado,
            data=self._datos_empleado(
                nombres='Ana Editada',
                email='ana.editar.inactiva@example.com',
            ),
            usuario_actor=self.actor,
        )

        empleado.refresh_from_db()
        user.refresh_from_db()
        perfil = UsuarioEmpleado.todos.get(usuario=user, empleado=empleado)
        self.assertEqual(empleado.nombres, 'Ana Editada')
        self.assertEqual(empleado.estado, EstadoGeneral.INACTIVO)
        self.assertFalse(empleado.activo)
        self.assertFalse(user.is_active)
        self.assertFalse(perfil.activo)

    def test_activar_empleado_restaura_estado_activo(self):
        empleado = EmpleadoService.crear_empleado(data=self._datos_empleado())
        EmpleadoService.desactivar_empleado(empleado=empleado)

        EmpleadoService.activar_empleado(empleado=empleado)

        empleado.refresh_from_db()
        self.assertEqual(empleado.estado, EstadoGeneral.ACTIVO)
        self.assertTrue(empleado.activo)


class EmpleadoViewsTests(TestCase):
    def setUp(self):
        self.grupo_admin = Group.objects.get(name='admin')
        self.admin = User.objects.create_user(username='admin-empleados', password='test123')
        self.admin.groups.add(self.grupo_admin)

    def _form_data(self, **overrides):
        data = {
            'codigo': '',
            'nombres': 'Ana',
            'apellidos': 'Torres',
            'cargo': CargoEmpleado.RECEPCIONISTA,
            'email': 'ana.views@example.com',
            'telefono': '999888777',
            'estado': EstadoGeneral.ACTIVO,
            'fecha_ingreso': date.today().isoformat(),
        }
        data.update(overrides)
        return data

    def test_crear_empleado_desde_view_usa_servicio(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('empleados:create'), data=self._form_data())

        self.assertRedirects(response, reverse('empleados:list'))
        empleado = Empleado.objects.get(email='ana.views@example.com')
        self.assertEqual(empleado.codigo, 'EMP-0001')
        self.assertEqual(empleado.creado_por, self.admin)

    def test_actualizar_empleado_desde_view_conserva_codigo(self):
        self.client.force_login(self.admin)
        empleado = EmpleadoService.crear_empleado(data=self._form_data())

        response = self.client.post(
            reverse('empleados:update', args=[empleado.pk]),
            data=self._form_data(
                codigo='MANUAL',
                nombres='Ana Maria',
                email='ana.views.actualizada@example.com',
            ),
        )

        self.assertRedirects(response, reverse('empleados:list'))
        empleado.refresh_from_db()
        self.assertEqual(empleado.codigo, 'EMP-0001')
        self.assertEqual(empleado.nombres, 'Ana Maria')
        self.assertEqual(empleado.email, 'ana.views.actualizada@example.com')

    def test_actualizar_empleado_desde_view_no_cambia_estado(self):
        self.client.force_login(self.admin)
        empleado = EmpleadoService.crear_empleado(data=self._form_data(email='ana.estado.view@example.com'))
        EmpleadoService.desactivar_empleado(empleado=empleado, usuario_actor=self.admin)

        response = self.client.post(
            reverse('empleados:update', args=[empleado.pk]),
            data=self._form_data(
                nombres='Ana Editada',
                email='ana.estado.view@example.com',
                estado=EstadoGeneral.ACTIVO,
            ),
        )

        self.assertRedirects(response, reverse('empleados:list'))
        empleado.refresh_from_db()
        self.assertEqual(empleado.nombres, 'Ana Editada')
        self.assertEqual(empleado.estado, EstadoGeneral.INACTIVO)
        self.assertFalse(empleado.activo)

    def test_listado_empleados_usa_busqueda(self):
        self.client.force_login(self.admin)
        EmpleadoService.crear_empleado(data=self._form_data(nombres='Ana', email='ana.search@example.com'))
        EmpleadoService.crear_empleado(data=self._form_data(nombres='Luis', email='luis.search@example.com', telefono='999111222'))

        response = self.client.get(reverse('empleados:list'), {'q': 'Luis'})

        self.assertContains(response, 'Luis')
        self.assertNotContains(response, 'Ana')

    def test_listado_muestra_accion_segun_estado(self):
        self.client.force_login(self.admin)
        activo = EmpleadoService.crear_empleado(data=self._form_data(email='activo.list@example.com'))
        inactivo = EmpleadoService.crear_empleado(data=self._form_data(
            nombres='Luis',
            email='inactivo.list@example.com',
            telefono='999111222',
        ))
        EmpleadoService.desactivar_empleado(empleado=inactivo)

        response = self.client.get(reverse('empleados:list'))

        self.assertContains(response, reverse('empleados:deactivate', args=[activo.pk]))
        self.assertContains(response, reverse('empleados:activate', args=[inactivo.pk]))

    def test_desactivar_empleado_desde_view_usa_servicio(self):
        self.client.force_login(self.admin)
        empleado = EmpleadoService.crear_empleado(data=self._form_data())

        response = self.client.post(reverse('empleados:deactivate', args=[empleado.pk]))

        self.assertRedirects(response, reverse('empleados:list'))
        empleado.refresh_from_db()
        self.assertEqual(empleado.estado, EstadoGeneral.INACTIVO)
        self.assertFalse(empleado.activo)

    def test_activar_empleado_desde_view_usa_servicio(self):
        self.client.force_login(self.admin)
        empleado = EmpleadoService.crear_empleado(data=self._form_data())
        EmpleadoService.desactivar_empleado(empleado=empleado)

        response = self.client.post(reverse('empleados:activate', args=[empleado.pk]))

        self.assertRedirects(response, reverse('empleados:list'))
        empleado.refresh_from_db()
        self.assertEqual(empleado.estado, EstadoGeneral.ACTIVO)
        self.assertTrue(empleado.activo)

    def test_rechaza_telefono_con_longitud_invalida(self):
        empleado = Empleado(
            codigo='EMP003',
            nombres='Mario',
            apellidos='Lopez',
            cargo=CargoEmpleado.HOUSEKEEPING,
            email='mario.lopez@example.com',
            telefono='123456',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            empleado.full_clean()

        self.assertIn('telefono', context.exception.message_dict)

    def test_rechaza_fecha_ingreso_futura(self):
        empleado = Empleado(
            codigo='EMP004',
            nombres='Rosa',
            apellidos='Vega',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='rosa.vega@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date(date.today().year + 1, 1, 1),
        )

        with self.assertRaises(ValidationError) as context:
            empleado.full_clean()

        self.assertIn('fecha_ingreso', context.exception.message_dict)

    def test_rechaza_email_duplicado(self):
        Empleado.objects.create(
            codigo='EMP005',
            nombres='Elena',
            apellidos='Diaz',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='elena.diaz@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )
        empleado = Empleado(
            codigo='EMP006',
            nombres='Elena',
            apellidos='Rojas',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='ELENA.DIAZ@EXAMPLE.COM',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            empleado.full_clean()

        self.assertIn('email', context.exception.message_dict)

    def test_rechaza_telefono_duplicado(self):
        Empleado.objects.create(
            codigo='EMP007',
            nombres='Pedro',
            apellidos='Soto',
            cargo=CargoEmpleado.HOUSEKEEPING,
            email='pedro.soto@example.com',
            telefono='999888777',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )
        empleado = Empleado(
            codigo='EMP008',
            nombres='Pedro',
            apellidos='Mora',
            cargo=CargoEmpleado.HOUSEKEEPING,
            email='pedro.mora@example.com',
            telefono='999888777',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date.today(),
        )

        with self.assertRaises(ValidationError) as context:
            empleado.full_clean()

        self.assertIn('telefono', context.exception.message_dict)
