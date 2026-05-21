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
        subtotal_cargos = self.estancia.cargos.aggregate(
            total=models.Sum('monto')
        )['total'] or 0

        self.subtotal = (self.estancia.precio_final + subtotal_cargos).quantize(Decimal('0.01'))
        self.igv = (self.subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        self.total = (self.subtotal + self.igv).quantize(Decimal('0.01'))
        self.save(update_fields=['subtotal', 'igv', 'total'])
        return self.total
