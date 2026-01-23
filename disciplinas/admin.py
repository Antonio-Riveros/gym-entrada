from django.contrib import admin
from .models import Disciplina, Horario, Combo

class HorarioInline(admin.TabularInline):
    model = Horario
    extra = 1
    fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'capacidad_maxima')

@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_display', 'precio_mensual', 'precio_clase_suelta')
    list_editable = ('precio_mensual', 'precio_clase_suelta')
    inlines = [HorarioInline]
    search_fields = ('nombre',)
    
    fieldsets = (
        ('Información de la Disciplina', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Precios', {
            'fields': ('precio_mensual', 'precio_clase_suelta')
        }),
    )

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('disciplina', 'get_dia_semana_display', 'hora_inicio', 'hora_fin', 'capacidad_maxima')
    list_filter = ('disciplina', 'dia_semana')
    ordering = ('dia_semana', 'hora_inicio')
    search_fields = ('disciplina__nombre',)



@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_combo', 'calcular_descuento_porcentaje', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    filter_horizontal = ('disciplinas',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'descuento_aplicado')
    
    fieldsets = (
        ('Información del Combo', {
            'fields': ('nombre', 'descripcion', 'disciplinas')
        }),
        ('Precios y Estado', {
            'fields': ('precio_combo', 'descuento_aplicado', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def calcular_descuento_porcentaje(self, obj):
        return f"{obj.calcular_descuento_porcentaje():.1f}%"
    calcular_descuento_porcentaje.short_description = 'Descuento'
    
    def save_model(self, request, obj, form, change):
        # Calcular descuento automáticamente al guardar
        precio_total = sum(d.precio_mensual for d in obj.disciplinas.all())
        if precio_total > 0:
            obj.descuento_aplicado = ((precio_total - obj.precio_combo) / precio_total * 100)
        super().save_model(request, obj, form, change)