from django.urls import path
from . import views

urlpatterns = [
    path('', views.PagoListView.as_view(), name='pago_list'),
    path('nuevo/', views.PagoCreateView.as_view(), name='pago_create'),
    path('reporte/', views.ReportePagosView.as_view(), name='pago_reporte'),
]