from django.urls import path

from huespedes.views import (
    HuespedCreateView,
    HuespedDeleteView,
    HuespedDetailView,
    HuespedListView,
    HuespedUpdateView,
)


app_name = 'huespedes'

urlpatterns = [
    path('', HuespedListView.as_view(), name='list'),
    path('crear/', HuespedCreateView.as_view(), name='create'),
    path('<int:pk>/', HuespedDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', HuespedUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', HuespedDeleteView.as_view(), name='delete'),
]
