from django import forms
from .models import Alumno
from datetime import date

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'telefono', 'email', 
                  'fecha_nacimiento', 'rfid', 'foto', 'activo']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'telefono': forms.TextInput(attrs={'placeholder': '341-1234567'}),
            'email': forms.EmailInput(attrs={'placeholder': 'ejemplo@email.com'}),
        }
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            edad = (date.today() - fecha_nacimiento).days // 365
            if edad < 12:
                raise forms.ValidationError('El alumno debe tener al menos 12 años.')
            if edad > 80:
                raise forms.ValidationError('Por favor verifique la fecha de nacimiento.')
        return fecha_nacimiento
    
    def clean_rfid(self):
        rfid = self.cleaned_data.get('rfid')
        if rfid:
            # Verificar que el RFID no esté duplicado
            qs = Alumno.objects.filter(rfid=rfid)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise forms.ValidationError('Este código RFID ya está asignado a otro alumno.')
        return rfid