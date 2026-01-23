from django.urls import path
from . import views

urlpatterns = [
    path('', views.AccesoListView.as_view(), name='acceso_list'),
    path('nuevo/', views.AccesoCreateView.as_view(), name='acceso_create'),
    path('rfid/', views.acceso_rfid, name='acceso_rfid'),
]