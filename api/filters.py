from django_filters import rest_framework as filters


class EstadoFilterMixin(filters.FilterSet):
    estado = filters.CharFilter(field_name='estado', lookup_expr='iexact')


class FechaRangoFilterMixin(filters.FilterSet):
    desde = filters.DateFilter(field_name='fecha_registro__date', lookup_expr='gte')
    hasta = filters.DateFilter(field_name='fecha_registro__date', lookup_expr='lte')
