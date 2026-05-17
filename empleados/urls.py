from django.urls import path

from empleados.views import (
    EmpleadoCreateView,
    EmpleadoDeleteView,
    EmpleadoDetailView,
    EmpleadoListView,
    EmpleadoUpdateView,
)


app_name = 'empleados'

urlpatterns = [
    path('', EmpleadoListView.as_view(), name='list'),
    path('crear/', EmpleadoCreateView.as_view(), name='create'),
    path('<int:pk>/', EmpleadoDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', EmpleadoUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', EmpleadoDeleteView.as_view(), name='delete'),
]
