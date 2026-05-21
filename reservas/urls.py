from django.urls import path

from reservas.views import ReservaCancelView, ReservaCreateView, ReservaListView, ReservaUpdateView


app_name = 'reservas'

urlpatterns = [
    path('', ReservaListView.as_view(), name='list'),
    path('crear/', ReservaCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', ReservaUpdateView.as_view(), name='update'),
    path('<int:pk>/cancelar/', ReservaCancelView.as_view(), name='cancel'),
]
