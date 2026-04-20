from django.db import models

class Disciplina(models.Model):
    DISCIPLINAS = [
        ('MMA', 'MMA'),
        ('LUTA_LIVRE', 'Luta Livre'),
        ('JIU_JITSU', 'Jiu Jitsu'),
        ('MUAY_THAI', 'Muay Thai'),
        ('KICKBOXING', 'Kickboxing'),
        ('PARKOUR', 'Parkour'),
        ('WRESTLING', 'Wrestling'),
        ('BOXEO', 'Boxeo'),
        ('FUNCIONAL', 'Funcional'),
        ('INFANTILES', 'Infantiles'),
    ]
    
    DIAS_SEMANA = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
        ('DOM', 'Domingo'),
    ]
    
    nombre = models.CharField(max_length=20, choices=DISCIPLINAS, unique=True)
    descripcion = models.TextField(blank=True)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    precio_clase_suelta = models.DecimalField(max_digits=10, decimal_places=2)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.get_nombre_display()
    
    class Meta:
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'

        
class Horario(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=3, choices=Disciplina.DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    capacidad_maxima = models.PositiveIntegerField(default=20)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['disciplina', 'dia_semana', 'hora_inicio']
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
    
    def __str__(self):
        return f"{self.disciplina.get_nombre_display()} - {self.get_dia_semana_display()} {self.hora_inicio.strftime('%H:%M')}"
    
    def esta_lleno(self):
        from pagos.models import Inscripcion
        inscritos_count = Inscripcion.objects.filter(horario=self, activa=True).count()
        return inscritos_count >= self.capacidad_maxima
    
    def espacios_disponibles(self):
        from pagos.models import Inscripcion
        inscritos_count = Inscripcion.objects.filter(horario=self, activa=True).count()
        return max(0, self.capacidad_maxima - inscritos_count)


class Combo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    disciplinas = models.ManyToManyField('Disciplina', related_name='combos')
    precio_combo = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    def calcular_precio_normal(self):
        total = sum(disciplina.precio_mensual for disciplina in self.disciplinas.all())
        return total
    
    def calcular_descuento_porcentaje(self):
        precio_normal = self.calcular_precio_normal()
        if precio_normal > 0:
            return ((precio_normal - self.precio_combo) / precio_normal * 100)
        return 0
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_combo}"
    
    class Meta:
        verbose_name = 'Combo'
        verbose_name_plural = 'Combos'
        ordering = ['nombre']