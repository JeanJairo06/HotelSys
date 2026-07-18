from django.test import TestCase

from hoteles.forms import HotelForm
from hoteles.models import Hotel
from hoteles.services import guardar_hotel_desde_formulario


class HotelServiceTests(TestCase):
    def test_guardar_hotel_desde_formulario(self):
        form = HotelForm(data={
            'nombre': 'Hotel Central',
            'ruc': '12345678901',
            'direccion': 'Av. Principal 123',
            'estrellas': 4,
            'telefono': '999999999',
        })

        self.assertTrue(form.is_valid())
        hotel = guardar_hotel_desde_formulario(form)

        self.assertEqual(Hotel.objects.count(), 1)
        self.assertEqual(hotel.nombre, 'Hotel Central')
