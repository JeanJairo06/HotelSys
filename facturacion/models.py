from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import ModeloBase
from config.choices import EstadoFolio, MetodoPago
from estancias.models import Estancia

class Folio(ModeloBase):
    estancia = models.OneToOneField(
        Estancia,
        on_delete=models.PROTECT,
        related_name='folio'
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    igv = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00')
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoFolio.choices,
        default=EstadoFolio.ABIERTO
    )

    class Meta:
        db_table = 'folios'
        verbose_name = 'Folio'
        verbose_name_plural = 'Folios'
        ordering = ['-id']

    def __str__(self):
        return f'Folio #{self.id} - {self.estancia.reserva.huesped}'

    @property
    def total_pagado(self):
        """Calcula de forma dinámica la suma de todos los pagos reales ejecutados."""
        suma_pagos = self.pagos.filter(activo=True).aggregate(models.Sum('monto'))['monto__sum']
        return suma_pagos.quantize(Decimal('0.01')) if suma_pagos else Decimal('0.00')

    @property
    def saldo_pendiente(self):
        """Calcula el saldo real: total acumulado menos lo efectivamente pagado."""
        saldo = self.total - self.total_pagado
        return max(saldo.quantize(Decimal('0.01')), Decimal('0.00'))


class Pago(ModeloBase):
    folio = models.ForeignKey(
        Folio, 
        on_delete=models.PROTECT, 
        related_name='pagos'
    )
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))] # Regla: Estrictamente mayor a 0
    )
    metodo_pago = models.CharField(
        max_length=30,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO
    )
    fecha_pago = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos_folios'
        verbose_name = 'Pago de Folio'
        verbose_name_plural = 'Pagos de Folios'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f'Pago #{self.id} - Folio #{self.folio.id} - S/ {self.monto}'


class Factura(ModeloBase):
    folio = models.ForeignKey(
        Folio,
        on_delete=models.PROTECT,
        related_name='facturas'
    )
    ruc_dni = models.CharField(max_length=11)
    razon_social = models.CharField(max_length=200)
    monto_subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    monto_igv = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    monto_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'facturas'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f'Factura #{self.id} - Ref Folio #{self.folio.id}'