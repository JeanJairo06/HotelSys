from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from config.choices import EstadoEstancia, EstadoFolio, TipoCargo
from estancias.models import Estancia, CargoEstancia
from .models import Folio, Pago, Factura
from .exceptions import FolioCerradoError, EstanciaFinalizadaError, PagoInvalidoError

class FolioService:
    @staticmethod
    @transaction.atomic
    def recalcular_totales(folio: Folio) -> Folio:
        subtotal_acumulado = Decimal(str(folio.estancia.precio_final))
        suma_cargos = folio.estancia.cargos.aggregate(Sum('monto'))['monto__sum']
        if suma_cargos:
            subtotal_acumulado += Decimal(str(suma_cargos))
        folio.subtotal = subtotal_acumulado.quantize(Decimal('0.01'))
        folio.igv = (folio.subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        folio.total = (folio.subtotal + folio.igv).quantize(Decimal('0.01'))
        
        folio.save()
        return folio

    @staticmethod
    @transaction.atomic
    def registrar_cargo_extra(folio_id: int, concepto: str, monto: Decimal, tipo: str, usuario=None) -> CargoEstancia:
        folio = Folio.objects.select_related('estancia').get(pk=folio_id)

        if folio.estado != EstadoFolio.ABIERTO:
            raise FolioCerradoError()
            
        if folio.estancia.estado == EstadoEstancia.FINALIZADA:
            raise EstanciaFinalizadaError("No se pueden agregar cargos a una estancia que ya ha sido finalizada.")
            
        if monto <= Decimal('0.00'):
            raise PagoInvalidoError("El monto del cargo debe ser estrictamente mayor a cero.")

        cargo = CargoEstancia.objects.create(
            estancia=folio.estancia,
            concepto=concepto,
            monto=monto.quantize(Decimal('0.01')),
            tipo=tipo
        )
        
        FolioService.recalcular_totales(folio)
        return cargo


class PagoService:
    @staticmethod
    @transaction.atomic
    def registrar_pago_parcial(folio_id: int, monto: Decimal, metodo_pago: str, usuario=None) -> Pago:
        
        folio = Folio.objects.get(pk=folio_id)
        
        if folio.estado != EstadoFolio.ABIERTO:
            raise FolioCerradoError("El folio ya se encuentra cerrado o liquidado.")

        if monto <= Decimal('0.00'):
            raise PagoInvalidoError("El monto del pago debe ser mayor a cero.")

        saldo_actual = folio.saldo_pendiente
        if monto > saldo_actual:
            raise PagoInvalidoError(f"El monto ingresado (S/ {monto}) supera el saldo pendiente actual (S/ {saldo_actual}).")

        pago = Pago.objects.create(
            folio=folio,
            monto=monto.quantize(Decimal('0.01')),
            metodo_pago=metodo_pago,
            creado_by=usuario 
        )
        
        if folio.saldo_pendiente == Decimal('0.00'):
            folio.estado = EstadoFolio.CERRADO
            folio.save()
            
        return pago