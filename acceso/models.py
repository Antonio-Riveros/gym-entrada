from django.db import models

class Acceso(models.Model):
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=[
        ('RFID', 'RFID'),
        ('MANUAL', 'Manual'),
        ('DENEGADO', 'Denegado')
    ])
    observacion = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Registro de Acceso'
        verbose_name_plural = 'Registros de Acceso'
    
    def __str__(self):
        alumno_nombre = self.alumno if self.alumno else "Desconocido"
        return f"{self.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {alumno_nombre} - {self.tipo}"