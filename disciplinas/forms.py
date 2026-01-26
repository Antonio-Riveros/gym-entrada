from django import forms
from django.forms import inlineformset_factory
from .models import Disciplina, Horario, Combo
from django import forms
from django.forms import inlineformset_factory
from .models import Disciplina, Horario, Combo
# En forms.py, actualiza HorarioForm
class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo']
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        help_texts = {
            'capacidad_maxima': 'Número máximo de alumnos en este horario',
            'activo': 'Desactivar para ocultar este horario temporalmente'
        }

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise forms.ValidationError('La hora de inicio debe ser anterior a la hora de fin')
        
        return cleaned_data

class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nombre', 'descripcion', 'precio_mensual', 'precio_clase_suelta']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['precio_clase_suelta'].help_text = 'Recomendado: 10% del precio mensual'

class ComboForm(forms.ModelForm):
    class Meta:
        model = Combo
        fields = ['nombre', 'descripcion', 'disciplinas', 'precio_combo', 'activo']
        widgets = {
            'disciplinas': forms.CheckboxSelectMultiple,
        }

# Añade esto al final del archivo
HorarioFormSet = inlineformset_factory(
    Disciplina,
    Horario,
    form=HorarioForm,
    extra=1,  # Una línea vacía por defecto
    can_delete=True,  # Permitir eliminar horarios
    fields=['dia_semana', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo']
)

class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nombre', 'descripcion', 'precio_mensual', 'precio_clase_suelta']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['precio_clase_suelta'].help_text = 'Recomendado: 10% del precio mensual'

class ComboForm(forms.ModelForm):
    class Meta:
        model = Combo
        fields = ['nombre', 'descripcion', 'disciplinas', 'precio_combo', 'activo']
        widgets = {
            'disciplinas': forms.CheckboxSelectMultiple,
        }