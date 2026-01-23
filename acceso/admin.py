from django.contrib import admin
from .models import Acceso

@admin.register(Acceso)
class AccesoAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'fecha_hora', 'tipo', 'observacion')
    list_filter = ('tipo', 'fecha_hora')
    search_fields = ('alumno__nombre', 'alumno__apellido', 'observacion')
    readonly_fields = ('fecha_hora',)
    date_hierarchy = 'fecha_hora'
    
    fieldsets = (
        ('Información del Acceso', {
            'fields': ('alumno', 'tipo')
        }),
        ('Detalles', {
            'fields': ('fecha_hora', 'observacion')
        }),
    )