class HotelService:
    @staticmethod
    def guardar_desde_formulario(form):
        return form.save()


def guardar_hotel_desde_formulario(form):
    return HotelService.guardar_desde_formulario(form)
