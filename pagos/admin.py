from django.contrib import admin
from .models import Inscripcion, Pago

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'disciplina', 'horario', 'activa', 'fecha_inscripcion')
    list_filter = ('activa', 'disciplina', 'fecha_inscripcion')
    search_fields = ('alumno__nombre', 'alumno__apellido', 'disciplina__nombre')
    raw_id_fields = ('alumno', 'disciplina', 'horario')
    list_editable = ('activa',)
    
    fieldsets = (
        ('Información de Inscripción', {
            'fields': ('alumno', 'disciplina', 'horario')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
    )

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'monto', 'fecha_pago', 'fecha_vencimiento', 'pagado', 'metodo_pago')
    list_filter = ('pagado', 'fecha_pago', 'metodo_pago')
    search_fields = ('alumno__nombre', 'alumno__apellido', 'observaciones')
    readonly_fields = ('fecha_pago',)
    date_hierarchy = 'fecha_pago'
    list_editable = ('pagado',)
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('alumno', 'monto', 'descuento_aplicado')
        }),
        ('Fechas y Estado', {
            'fields': ('fecha_pago', 'fecha_vencimiento', 'pagado')
        }),
        ('Método y Observaciones', {
            'fields': ('metodo_pago', 'observaciones')
        }),
    )