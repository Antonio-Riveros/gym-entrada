from django.db import models
from django.utils import timezone
from datetime import timedelta

class Inscripcion(models.Model):
    """Inscripción de un alumno a una disciplina"""
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='inscripciones')
    disciplina = models.ForeignKey('disciplinas.Disciplina', on_delete=models.CASCADE)
    horario = models.ForeignKey('disciplinas.Horario', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        # Un alumno no puede estar inscrito dos veces en la misma disciplina
        unique_together = ['alumno', 'disciplina']
        # Un alumno no puede tener dos inscripciones en el mismo horario
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'horario'],
                condition=models.Q(horario__isnull=False),
                name='unique_alumno_horario'
            )
        ]
    
    def __str__(self):
        return f"{self.alumno} - {self.disciplina}"
    
    def get_estado_display(self):
        """Muestra el estado de la inscripción"""
        if not self.activa:
            return "Inactiva"
        
        # Verificar si tiene pagos pendientes
        tiene_pago_pendiente = self.alumno.pagos.filter(
            pagado=False,
            fecha_vencimiento__lt=timezone.now().date()
        ).exists()
        
        if tiene_pago_pendiente:
            return "Con deuda"
        return "Activa"

class Pago(models.Model):
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('MERCADO_PAGO', 'Mercado Pago'),
        ('OTRO', 'Otro'),
    ]
    
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_pago = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')
    pagado = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    relacion_inscripcion = models.ForeignKey('Inscripcion', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.fecha_vencimiento:
            self.fecha_vencimiento = timezone.now().date() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pago #{self.id} - {self.alumno} - ${self.monto}"
    
    class Meta:
        ordering = ['-fecha_pago']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'