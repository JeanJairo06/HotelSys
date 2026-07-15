from django.urls import path

from cuentas.views import (
    UsuarioActivateView,
    UsuarioCreateView,
    UsuarioDeactivateView,
    UsuarioDetailView,
    UsuarioListView,
    UsuarioUpdateView,
)


app_name = 'usuarios'

urlpatterns = [
    path('', UsuarioListView.as_view(), name='list'),
    path('crear/', UsuarioCreateView.as_view(), name='create'),
    path('<int:pk>/', UsuarioDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', UsuarioUpdateView.as_view(), name='update'),
    path('<int:pk>/activar/', UsuarioActivateView.as_view(), name='activate'),
    path('<int:pk>/desactivar/', UsuarioDeactivateView.as_view(), name='deactivate'),
]
