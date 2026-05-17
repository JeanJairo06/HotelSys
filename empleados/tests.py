from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from config.choices import CargoEmpleado, EstadoGeneral
from empleados.models import Empleado


class EmpleadoModelTests(TestCase):
    def test_normaliza_codigo_en_mayusculas(self):
        empleado = Empleado.objects.create(
            codigo='emp001',
            nombres='Ana',
            apellidos='Torres',
            cargo=CargoEmpleado.RECEPCIONISTA,
            email='ana.torres@example.com',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date(2026, 5, 1),
        )

        self.assertEqual(empleado.codigo, 'EMP001')

    def test_rechaza_telefono_invalido(self):
        empleado = Empleado(
            codigo='EMP002',
            nombres='Luis',
            apellidos='Ramos',
            cargo=CargoEmpleado.HOUSEKEEPING,
            email='luis.ramos@example.com',
            telefono='abc123',
            estado=EstadoGeneral.ACTIVO,
            fecha_ingreso=date(2026, 5, 1),
        )

        with self.assertRaises(ValidationError):
            empleado.full_clean()
