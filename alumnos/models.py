from django.db import models

class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    fecha_nacimiento = models.DateField()
    fecha_inscripcion = models.DateField(auto_now_add=True)
    rfid = models.CharField(max_length=50, unique=True, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    def foto_path(instance, filename):
        import os
        name, ext = os.path.splitext(filename)
        return f'alumnos/{instance.nombre}_{instance.apellido}{ext}'
    
    # 👇 CAMBIO CLAVE
    foto = models.FileField(upload_to=foto_path, blank=True, null=True)
    
    def __str__(self):
        return f"{self.apellido}, {self.nombre}"
    
    class Meta:
        ordering = ['apellido', 'nombre']
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'