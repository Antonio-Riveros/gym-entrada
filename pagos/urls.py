from django.urls import path
from . import views

urlpatterns = [
    path('', views.PagoListView.as_view(), name='pago_list'),
    path('nuevo/', views.PagoCreateView.as_view(), name='pago_create'),
    path('reporte/', views.ReportePagosView.as_view(), name='pago_reporte'),
    # ✅ AGREGADO: URLs para acciones desde el perfil del alumno
    path('inscripcion/<int:pk>/desactivar/', views.inscripcion_desactivar, name='inscripcion_desactivar'),
    path('<int:pk>/marcar-pagado/', views.pago_marcar_pagado, name='pago_marcar_pagado'),
]