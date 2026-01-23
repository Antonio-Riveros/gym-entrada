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
]