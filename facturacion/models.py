from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from config.choices import EstadoFolio
from estancias.models import Estancia


class Folio(models.Model):
    estancia = models.OneToOneField(
        Estancia,
        on_delete=models.PROTECT,
        related_name='folio'
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    igv = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
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

    def calcular_totales(self):
        subtotal_acumulado = self.estancia.precio_final
        suma_cargos = self.estancia.cargos.aggregate(models.Sum('monto'))['monto__sum']
        if suma_cargos:
            subtotal_acumulado += suma_cargos
        self.subtotal = subtotal_acumulado.quantize(Decimal('0.01'))
        self.igv = (self.subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        self.total = (self.subtotal + self.igv).quantize(Decimal('0.01'))
        
        self.save()

        return self.total.quantize(Decimal('0.0000'))


class Factura(models.Model):
    folio = models.ForeignKey(
        Folio,
        on_delete=models.PROTECT,
        related_name='facturas'
    )
    ruc_dni = models.CharField(max_length=11)
    razon_social =models.CharField(max_length=200)
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
        return f'Factura #{self.id} - {self.razon_social} (S/ {self.monto_total})'
