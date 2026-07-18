from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from config.choices import EstadoEstancia, EstadoFolio, TipoCargo
from estancias.models import Estancia, CargoEstancia
from .models import Folio, Pago, Factura
from .exceptions import FolioCerradoError, EstanciaFinalizadaError, PagoInvalidoError, TarifaNoDisponibleError
from datetime import date
from habitaciones.models import Tarifa
from datetime import timedelta

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
    
    @staticmethod
    def validar_sin_deuda(estancia_id: int) -> bool:
        try:
            folio = Folio.objects.get(estancia_id=estancia_id)
            if folio.saldo_pendiente > Decimal('0.00'):
                from .exceptions import CheckoutBloqueadoError
                raise CheckoutBloqueadoError(f"No se puede realizar el check-out. El folio presenta un saldo pendiente de S/ {folio.saldo_pendiente}")
            return True
        except Folio.DoesNotExist:
            return True
    
    @staticmethod
    @transaction.atomic
    def emitir_comprobante_y_cerrar(folio_id: int, ruc_dni: str, razon_social: str, usuario=None) -> Factura:
        folio = Folio.objects.get(pk=folio_id)
        
        if folio.saldo_pendiente > Decimal('0.00'):
            from .exceptions import CheckoutBloqueadoError
            raise CheckoutBloqueadoError("No se puede facturar un folio con saldo pendiente.")

        # Creamos la factura
        factura = Factura.objects.create(
            folio=folio,
            ruc_dni=ruc_dni,
            razon_social=razon_social,
            monto_subtotal=folio.subtotal,
            monto_igv=folio.igv,
            monto_total=folio.total,
            creado_por=usuario
        )

        folio.estado = EstadoFolio.CERRADO
        folio.save()

        return factura


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
            creado_por=usuario,
        )
        
        return pago

class TarifaService:
    @staticmethod
    def calcular_precio_estancia(tipo_habitacion, fecha_entrada: date, fecha_salida: date) -> Decimal:
        if fecha_entrada >= fecha_salida:
            raise PagoInvalidoError("La fecha de entrada debe ser anterior a la de salida.")

        total_estancia = Decimal('0.00')
        fecha_actual = fecha_entrada

        while fecha_actual < fecha_salida:
            tarifa_especial = Tarifa.objects.filter(
                activo=True,
                tipo_habitacion=tipo_habitacion,
                fecha_inicio__lte=fecha_actual,
                fecha_fin__gte=fecha_actual
            ).first()

            if tarifa_especial:
                total_estancia += Decimal(str(tarifa_especial.precio_noche))
            else:
                total_estancia += Decimal(str(tipo_habitacion.precio_base))
            
            fecha_actual += timedelta(days=1)

        return total_estancia.quantize(Decimal('0.01'))