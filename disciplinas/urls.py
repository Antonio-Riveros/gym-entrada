from django.urls import path
from . import views

urlpatterns = [
    # Disciplinas
    path('', views.DisciplinaListView.as_view(), name='disciplina_list'),
    path('nueva/', views.DisciplinaCreateView.as_view(), name='disciplina_create'),
    path('<int:pk>/editar/', views.DisciplinaUpdateView.as_view(), name='disciplina_update'),
    path('horario/<int:pk>/', views.HorarioDetailView.as_view(), name='horario_detail'),
    
    # Precios rápidos
    path('precios-rapidos/', views.PreciosRapidosView.as_view(), name='precios_rapidos'),
    
    # Combos
    path('combos/', views.ComboListView.as_view(), name='combo_list'),
    path('combos/nuevo/', views.ComboCreateView.as_view(), name='combo_create'),
    path('combos/<int:pk>/', views.ComboDetailView.as_view(), name='combo_detail'),
    path('combos/<int:pk>/editar/', views.ComboUpdateView.as_view(), name='combo_update'),
    path('api/calcular-combo/', views.calcular_combo_precio, name='calcular_combo_precio'),
    
    path('api/<int:pk>/activar/', views.ActivarDesactivarDisciplinaView.as_view(), name='disciplina_activar'),
    path('api/activar-lote/', views.ActivarDesactivarLoteView.as_view(), name='disciplina_activar_lote'),
    path('api/cambiar-precio-lote/', views.CambiarPrecioLoteView.as_view(), name='disciplina_cambiar_precio_lote'),
    
    # Horarios
    path('<int:disciplina_id>/horarios/nuevo/', views.HorarioCreateView.as_view(), name='horario_create'),
    path('horarios/<int:pk>/editar/', views.HorarioUpdateView.as_view(), name='horario_update'),
    
    # API para horarios
    path('api/horarios-disciplina/', views.obtener_horarios_disciplina, name='obtener_horarios_disciplina'),
]