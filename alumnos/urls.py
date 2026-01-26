from django.urls import path
from . import views

urlpatterns = [
    # Vistas principales
    path('', views.AlumnoListView.as_view(), name='alumno_list'),
    path('nuevo/', views.AlumnoCreateView.as_view(), name='alumno_create'),
    path('<int:pk>/', views.AlumnoDetailView.as_view(), name='alumno_detail'),
    path('<int:pk>/editar/', views.AlumnoUpdateView.as_view(), name='alumno_update'),
    
    # Inscripción rápida
    path('inscripcion-rapida/', views.InscripcionRapidaView.as_view(), name='inscripcion_rapida'),
    path('<int:pk>/info/', views.obtener_info_disciplina, name='disciplina_info'),
    
    # APIs AJAX
    path('buscar-ajax/', views.buscar_alumnos_ajax, name='buscar_alumnos_ajax'),
    path('horarios-disciplina/', views.obtener_horarios_disciplina, name='horarios_disciplina'),
    path('info-alumno/', views.obtener_info_alumno, name='info_alumno'),
    path('registro-rapido-completo/', views.RegistroRapidoCompletoView.as_view(), name='registro_rapido_completo'),
    
    # APIs para acciones rápidas (NUEVAS)
    path('api/<int:pk>/activar/', views.activar_alumno_api, name='alumno_activar_api'),
    path('api/<int:pk>/desactivar/', views.desactivar_alumno_api, name='alumno_desactivar_api'),
    path('api/<int:pk>/eliminar/', views.eliminar_alumno_api, name='alumno_eliminar_api'),
    path('api/activar-lote/', views.activar_alumnos_lote_api, name='alumnos_activar_lote'),
    path('api/desactivar-lote/', views.desactivar_alumnos_lote_api, name='alumnos_desactivar_lote'),
    path('api/eliminar-lote/', views.eliminar_alumnos_lote_api, name='alumnos_eliminar_lote'),
    path('api/asignar-disciplina-lote/', views.asignar_disciplina_lote_api, name='alumnos_asignar_disciplina_lote'),
]