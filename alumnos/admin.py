from django.contrib import admin
from .models import Alumno

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'telefono', 'activo', 'fecha_inscripcion')
    list_filter = ('activo', 'fecha_inscripcion')
    search_fields = ('nombre', 'apellido', 'telefono', 'rfid', 'email')
    readonly_fields = ('fecha_inscripcion',)
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'fecha_nacimiento', 'foto')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email')
        }),
        ('Sistema', {
            'fields': ('rfid', 'activo', 'fecha_inscripcion')
        }),
    )