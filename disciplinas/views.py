from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import date
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Disciplina, Horario, Combo
from alumnos.models import Alumno
from pagos.models import Inscripcion, Pago
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import date, datetime
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Disciplina, Horario, Combo
from alumnos.models import Alumno
from pagos.models import Inscripcion, Pago
from .forms import DisciplinaForm, HorarioFormSet, ComboForm
from datetime import date, timedelta




class DisciplinaListView(LoginRequiredMixin, ListView):
    model = Disciplina
    template_name = 'disciplinas/disciplina_list.html'
    context_object_name = 'disciplinas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        total_disciplinas = Disciplina.objects.count()
        total_inscripciones = Inscripcion.objects.filter(activa=True).count()
        ingresos_mensuales = 0
        
        # Calcular ingresos potenciales mensuales
        for disciplina in Disciplina.objects.all():
            inscripciones_count = Inscripcion.objects.filter(
                disciplina=disciplina,
                activa=True
            ).count()
            ingresos_mensuales += inscripciones_count * disciplina.precio_mensual
        
        context.update({
            'total_disciplinas': total_disciplinas,
            'total_inscripciones': total_inscripciones,
            'ingresos_mensuales': ingresos_mensuales,
        })
        
        return context

class HorarioDetailView(LoginRequiredMixin, DetailView):
    model = Horario
    template_name = 'disciplinas/horario_detail.html'
    context_object_name = 'horario'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        horario = self.object
        
        # Alumnos inscritos en este horario
        inscripciones = Inscripcion.objects.filter(
            horario=horario,
            activa=True
        ).select_related('alumno')
        
        # Verificar estado de pago
        alumnos_con_estado = []
        for inscripcion in inscripciones:
            alumno = inscripcion.alumno
            tiene_pago_pendiente = Pago.objects.filter(
                alumno=alumno,
                pagado=False,
                fecha_vencimiento__lt=timezone.now().date()
            ).exists()
            
            alumnos_con_estado.append({
                'alumno': alumno,
                'inscripcion': inscripcion,
                'tiene_pago_pendiente': tiene_pago_pendiente,
            })
        
        # Estadísticas
        espacios_disponibles = horario.capacidad_maxima - inscripciones.count()
        porcentaje_ocupacion = (inscripciones.count() / horario.capacidad_maxima * 100) if horario.capacidad_maxima > 0 else 0
        
        context.update({
            'alumnos_inscritos': alumnos_con_estado,
            'total_inscritos': inscripciones.count(),
            'espacios_disponibles': espacios_disponibles,
            'porcentaje_ocupacion': round(porcentaje_ocupacion, 1),
        })
        
        return context

class PreciosRapidosView(LoginRequiredMixin, View):
    """Vista para editar precios rápidamente"""
    template_name = 'disciplinas/precios_rapidos.html'
    
    def get(self, request):
        disciplinas = Disciplina.objects.all().order_by('nombre')
        combos = Combo.objects.filter(activo=True).order_by('nombre')
        
        return render(request, self.template_name, {
            'disciplinas': disciplinas,
            'combos': combos,
        })
    
    def post(self, request):
        # Actualizar precios de disciplinas
        for key, value in request.POST.items():
            if key.startswith('precio_disciplina_'):
                disciplina_id = key.replace('precio_disciplina_', '')
                try:
                    disciplina = Disciplina.objects.get(id=disciplina_id)
                    nuevo_precio = value.replace('$', '').replace('.', '').replace(',', '.')
                    disciplina.precio_mensual = float(nuevo_precio)
                    disciplina.precio_clase_suelta = float(nuevo_precio) / 10  # 10% del mensual
                    disciplina.save()
                except (Disciplina.DoesNotExist, ValueError):
                    continue
        
        # Actualizar precios de combos
        for key, value in request.POST.items():
            if key.startswith('precio_combo_'):
                combo_id = key.replace('precio_combo_', '')
                try:
                    combo = Combo.objects.get(id=combo_id)
                    nuevo_precio = value.replace('$', '').replace('.', '').replace(',', '.')
                    combo.precio_combo = float(nuevo_precio)
                    combo.save()
                except (Combo.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, 'Precios actualizados exitosamente.')
        return redirect('precios_rapidos')

class ComboListView(LoginRequiredMixin, ListView):
    model = Combo
    template_name = 'disciplinas/combo_list.html'
    context_object_name = 'combos'
    
    def get_queryset(self):
        return Combo.objects.all().order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        total_combos = Combo.objects.count()
        combos_activos = Combo.objects.filter(activo=True).count()
        
        # Alumnos con combos
        alumnos_con_combos = Alumno.objects.filter(
            inscripciones__disciplina__combos__isnull=False
        ).distinct().count()
        
        context.update({
            'total_combos': total_combos,
            'combos_activos': combos_activos,
            'alumnos_con_combos': alumnos_con_combos,
        })
        
        return context

class ComboCreateView(LoginRequiredMixin, CreateView):
    model = Combo
    template_name = 'disciplinas/combo_form.html'
    fields = ['nombre', 'descripcion', 'disciplinas', 'precio_combo', 'activo']
    success_url = reverse_lazy('combo_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nuevo Combo'
        context['disciplinas'] = Disciplina.objects.all()
        return context
    
    def form_valid(self, form):
        # Calcular descuento aplicado
        combo = form.save(commit=False)
        precio_total_disciplinas = sum(
            d.precio_mensual for d in form.cleaned_data['disciplinas']
        )
        
        if precio_total_disciplinas > 0:
            descuento = ((precio_total_disciplinas - combo.precio_combo) / 
                        precio_total_disciplinas * 100)
            combo.descuento_aplicado = round(descuento, 2)
        
        combo.save()
        form.save_m2m()  # Guardar relaciones many-to-many
        
        messages.success(self.request, 'Combo creado exitosamente.')
        return super().form_valid(form)

class ComboUpdateView(LoginRequiredMixin, UpdateView):
    model = Combo
    template_name = 'disciplinas/combo_form.html'
    fields = ['nombre', 'descripcion', 'disciplinas', 'precio_combo', 'activo']
    success_url = reverse_lazy('combo_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Combo'
        context['disciplinas'] = Disciplina.objects.all()
        return context
    
    def form_valid(self, form):
        # Calcular descuento aplicado
        combo = form.save(commit=False)
        precio_total_disciplinas = sum(
            d.precio_mensual for d in form.cleaned_data['disciplinas']
        )
        
        if precio_total_disciplinas > 0:
            descuento = ((precio_total_disciplinas - combo.precio_combo) / 
                        precio_total_disciplinas * 100)
            combo.descuento_aplicado = round(descuento, 2)
        
        messages.success(self.request, 'Combo actualizado exitosamente.')
        return super().form_valid(form)

class ComboDetailView(LoginRequiredMixin, DetailView):
    model = Combo
    template_name = 'disciplinas/combo_detail.html'
    context_object_name = 'combo'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        combo = self.object
        
        # Calcular ahorro
        precio_normal = combo.calcular_precio_normal()
        ahorro = precio_normal - combo.precio_combo
        
        # Alumnos que tienen este combo
        disciplinas_ids = combo.disciplinas.values_list('id', flat=True)
        alumnos_con_combo = Alumno.objects.filter(
            inscripciones__disciplina__id__in=disciplinas_ids
        ).distinct()
        
        context.update({
            'precio_normal': precio_normal,
            'ahorro': ahorro,
            'porcentaje_descuento': combo.calcular_descuento_porcentaje(),
            'alumnos_con_combo': alumnos_con_combo.count(),
        })
        
        return context

def calcular_combo_precio(request):
    """API para calcular precio de combo en tiempo real"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            disciplinas_ids = data.get('disciplinas', [])
            
            # Calcular precio total
            disciplinas = Disciplina.objects.filter(id__in=disciplinas_ids)
            precio_total = sum(d.precio_mensual for d in disciplinas)
            
            return JsonResponse({
                'precio_total': float(precio_total),
                'cantidad_disciplinas': len(disciplinas_ids)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


class DisciplinaCreateView(LoginRequiredMixin, CreateView):
    model = Disciplina
    template_name = 'disciplinas/disciplina_form.html'
    fields = ['nombre', 'descripcion', 'precio_mensual', 'precio_clase_suelta']
    success_url = reverse_lazy('disciplina_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nueva Disciplina'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Disciplina creada exitosamente.')
        return super().form_valid(form)

class DisciplinaUpdateView(LoginRequiredMixin, UpdateView):
    model = Disciplina
    template_name = 'disciplinas/disciplina_form.html'
    fields = ['nombre', 'descripcion', 'precio_mensual', 'precio_clase_suelta']
    success_url = reverse_lazy('disciplina_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Disciplina'
        
        # Calcular ingresos mensuales de esta disciplina
        from pagos.models import Inscripcion
        inscripciones_count = Inscripcion.objects.filter(
            disciplina=self.object,
            activa=True
        ).count()
        context['ingresos_mensuales'] = inscripciones_count * self.object.precio_mensual
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Disciplina actualizada exitosamente.')
        return super().form_valid(form)


@method_decorator(csrf_exempt, name='dispatch')
class ActivarDesactivarDisciplinaView(View):
    def post(self, request, pk):
        try:
            disciplina = Disciplina.objects.get(id=pk)
            accion = request.POST.get('accion', 'activar')
            
            if accion == 'activar':
                disciplina.activa = True
                mensaje = 'Disciplina activada'
            else:
                disciplina.activa = False
                mensaje = 'Disciplina desactivada'
            
            disciplina.save()
            return JsonResponse({'success': True, 'message': mensaje})
        except Disciplina.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Disciplina no encontrada'})

@method_decorator(csrf_exempt, name='dispatch')
class ActivarDesactivarLoteView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            accion = data.get('accion', 'activar')
            
            disciplinas = Disciplina.objects.filter(id__in=ids)
            
            if accion == 'activar':
                disciplinas.update(activa=True)
                mensaje = f'{len(disciplinas)} disciplinas activadas'
            else:
                disciplinas.update(activa=False)
                mensaje = f'{len(disciplinas)} disciplinas desactivadas'
            
            return JsonResponse({'success': True, 'message': mensaje})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@method_decorator(csrf_exempt, name='dispatch')
class CambiarPrecioLoteView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            precio_mensual = data.get('precio_mensual')
            precio_clase_suelta = data.get('precio_clase_suelta')
            
            if not precio_mensual:
                return JsonResponse({'success': False, 'error': 'Precio mensual requerido'})
            
            disciplinas = Disciplina.objects.filter(id__in=ids)
            
            # Actualizar precios
            for disciplina in disciplinas:
                disciplina.precio_mensual = precio_mensual
                if precio_clase_suelta:
                    disciplina.precio_clase_suelta = precio_clase_suelta
                else:
                    # Calcular automáticamente (10% del mensual)
                    disciplina.precio_clase_suelta = float(precio_mensual) * 0.1
                disciplina.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Precios actualizados en {len(disciplinas)} disciplinas'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
class DisciplinaCreateView(LoginRequiredMixin, CreateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'disciplinas/disciplina_form.html'
    success_url = reverse_lazy('disciplina_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['horario_formset'] = HorarioFormSet(self.request.POST, instance=self.object)
        else:
            context['horario_formset'] = HorarioFormSet(instance=self.object)
        context['form_title'] = 'Nueva Disciplina'
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        horario_formset = context['horario_formset']
        
        if horario_formset.is_valid():
            self.object = form.save()
            horario_formset.instance = self.object
            horario_formset.save()
            messages.success(self.request, 'Disciplina creada exitosamente.')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class DisciplinaUpdateView(LoginRequiredMixin, UpdateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'disciplinas/disciplina_form.html'
    success_url = reverse_lazy('disciplina_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['horario_formset'] = HorarioFormSet(self.request.POST, instance=self.object)
        else:
            context['horario_formset'] = HorarioFormSet(instance=self.object)
        context['form_title'] = 'Editar Disciplina'
        
        # Calcular ingresos mensuales de esta disciplina
        inscripciones_count = Inscripcion.objects.filter(
            disciplina=self.object,
            activa=True
        ).count()
        context['ingresos_mensuales'] = inscripciones_count * self.object.precio_mensual
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        horario_formset = context['horario_formset']
        
        if horario_formset.is_valid():
            self.object = form.save()
            horario_formset.instance = self.object
            horario_formset.save()
            messages.success(self.request, 'Disciplina actualizada exitosamente.')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

# Agregar esta función para verificar conflictos de horarios
def verificar_conflicto_horario(alumno, nuevo_horario):
    """
    Verifica si un alumno ya tiene inscripciones en horarios que se superponen
    con el nuevo horario que se quiere asignar
    """
    if not nuevo_horario:
        return False, []
    
    # Obtener todas las inscripciones activas del alumno
    inscripciones = Inscripcion.objects.filter(
        alumno=alumno,
        activa=True
    ).exclude(horario__isnull=True)
    
    conflictos = []
    for inscripcion in inscripciones:
        horario_existente = inscripcion.horario
        
        # Verificar si son el mismo día
        if horario_existente.dia_semana != nuevo_horario.dia_semana:
            continue
        
        # Convertir a datetime para comparar
        hoy = date.today()
        existente_inicio = datetime.combine(hoy, horario_existente.hora_inicio)
        existente_fin = datetime.combine(hoy, horario_existente.hora_fin)
        nuevo_inicio = datetime.combine(hoy, nuevo_horario.hora_inicio)
        nuevo_fin = datetime.combine(hoy, nuevo_horario.hora_fin)
        
        # Verificar superposición
        if (nuevo_inicio < existente_fin and nuevo_fin > existente_inicio):
            conflictos.append({
                'disciplina': inscripcion.disciplina.get_nombre_display(),
                'horario': f"{horario_existente.get_dia_semana_display()} {horario_existente.hora_inicio.strftime('%H:%M')}-{horario_existente.hora_fin.strftime('%H:%M')}",
                'horario_nuevo': f"{nuevo_horario.get_dia_semana_display()} {nuevo_horario.hora_inicio.strftime('%H:%M')}-{nuevo_horario.hora_fin.strftime('%H:%M')}"
            })
    
    return len(conflictos) > 0, conflictos

# Actualizar la vista InscripcionRapidaView para incluir validación de horarios
class InscripcionRapidaView(LoginRequiredMixin, View):
    """Vista principal para inscripción rápida"""
    template_name = 'alumnos/inscripcion_rapida.html'
    
    def get(self, request):
        # Obtener datos para el formulario
        alumnos = Alumno.objects.filter(activo=True).order_by('apellido', 'nombre')
        disciplinas = Disciplina.objects.all().order_by('nombre')
        
        context = {
            'alumnos': alumnos,
            'disciplinas': disciplinas,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        try:
            alumno_id = request.POST.get('alumno')
            disciplina_id = request.POST.get('disciplina')
            horario_id = request.POST.get('horario', None)
            
            # Validar que se hayan enviado los datos necesarios
            if not alumno_id or not disciplina_id:
                messages.error(request, 'Por favor, selecciona un alumno y una disciplina.')
                return redirect('inscripcion_rapida')
            
            # Obtener objetos
            alumno = get_object_or_404(Alumno, id=alumno_id)
            disciplina = get_object_or_404(Disciplina, id=disciplina_id)
            
            # Verificar si ya está inscrito
            if Inscripcion.objects.filter(alumno=alumno, disciplina=disciplina, activa=True).exists():
                messages.warning(request, f'{alumno} ya está inscrito en {disciplina.get_nombre_display()}.')
                return redirect('inscripcion_rapida')
            
            # Obtener horario si se seleccionó
            horario = None
            if horario_id:
                horario = get_object_or_404(Horario, id=horario_id)
                
                # Verificar conflictos de horario
                tiene_conflicto, conflictos = verificar_conflicto_horario(alumno, horario)
                if tiene_conflicto:
                    mensaje_conflicto = '❌ No se puede inscribir: Horarios en conflicto:<br>'
                    for conflicto in conflictos:
                        mensaje_conflicto += f"- Ya inscrito en {conflicto['disciplina']} ({conflicto['horario']})<br>"
                    mensaje_conflicto += f"No se puede asignar {disciplina.get_nombre_display()} ({conflicto['horario_nuevo']})"
                    messages.error(request, mensaje_conflicto)
                    return redirect('inscripcion_rapida')
                
                # Verificar si ya está inscrito en ese horario exacto
                if Inscripcion.objects.filter(alumno=alumno, horario=horario, activa=True).exists():
                    messages.warning(request, f'{alumno} ya tiene una inscripción en este horario.')
                    return redirect('inscripcion_rapida')
                
                # Verificar capacidad del horario
                inscritos_en_horario = Inscripcion.objects.filter(horario=horario, activa=True).count()
                if inscritos_en_horario >= horario.capacidad_maxima:
                    messages.error(request, f'El horario seleccionado está lleno ({horario.capacidad_maxima}/{horario.capacidad_maxima}).')
                    return redirect('inscripcion_rapida')
            
            # Crear la inscripción
            inscripcion = Inscripcion.objects.create(
                alumno=alumno,
                disciplina=disciplina,
                horario=horario
            )
            
            # Registrar pago automático si se seleccionó
            if request.POST.get('registrar_pago') == 'on':
                self._registrar_pago_automatico(alumno, disciplina, inscripcion)
                messages.success(request, f'✅ {alumno} inscrito y pago registrado en {disciplina.get_nombre_display()}.')
            else:
                messages.success(request, f'✅ {alumno} inscrito exitosamente en {disciplina.get_nombre_display()}.')
            
            return redirect('inscripcion_rapida')
            
        except Exception as e:
            messages.error(request, f'Error al procesar la inscripción: {str(e)}')
            return redirect('inscripcion_rapida')
    
    def _registrar_pago_automatico(self, alumno, disciplina, inscripcion):
        """Registra un pago automático para la inscripción"""
        Pago.objects.create(
            alumno=alumno,
            monto=disciplina.precio_mensual,
            fecha_vencimiento=date.today() + timedelta(days=30),
            metodo_pago='EFECTIVO',
            pagado=True,
            observaciones=f"Inscripción a {disciplina.get_nombre_display()}",
            relacion_inscripcion=inscripcion
        )

def obtener_horarios_disciplina(request):
    """Obtiene los horarios disponibles para una disciplina específica"""
    if request.method == 'GET' and 'disciplina_id' in request.GET:
        disciplina_id = request.GET.get('disciplina_id')
        alumno_id = request.GET.get('alumno_id')  # Nuevo: para verificar conflictos
        
        try:
            disciplina = Disciplina.objects.get(id=disciplina_id)
            horarios = Horario.objects.filter(disciplina=disciplina).order_by('dia_semana', 'hora_inicio')
            
            horarios_data = []
            for horario in horarios:
                # Contar inscritos en este horario
                inscritos_count = Inscripcion.objects.filter(horario=horario, activa=True).count()
                disponible = horario.capacidad_maxima - inscritos_count
                
                # Verificar si el alumno tiene conflictos con este horario
                conflicto = False
                mensaje_conflicto = ""
                if alumno_id:
                    try:
                        alumno = Alumno.objects.get(id=alumno_id)
                        tiene_conflicto, conflictos = verificar_conflicto_horario(alumno, horario)
                        if tiene_conflicto:
                            conflicto = True
                            mensaje_conflicto = " (CONFLICTO DE HORARIO)"
                    except Alumno.DoesNotExist:
                        pass
                
                horarios_data.append({
                    'id': horario.id,
                    'dia': horario.get_dia_semana_display(),
                    'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
                    'hora_fin': horario.hora_fin.strftime('%H:%M'),
                    'capacidad': horario.capacidad_maxima,
                    'inscritos': inscritos_count,
                    'disponible': disponible,
                    'lleno': disponible <= 0,
                    'conflicto': conflicto,
                    'mensaje_conflicto': mensaje_conflicto
                })
            
            return JsonResponse({
                'success': True,
                'disciplina': disciplina.get_nombre_display(),
                'precio': str(disciplina.precio_mensual),
                'horarios': horarios_data
            })
            
        except Disciplina.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Disciplina no encontrada'})
    
    return JsonResponse({'success': False, 'error': 'Parámetros inválidos'})

def verificar_conflicto_horario(alumno, nuevo_horario):
    """
    Verifica si un alumno ya tiene inscripciones en horarios que se superponen
    con el nuevo horario que se quiere asignar
    """
    if not nuevo_horario:
        return False, []
    
    # Obtener todas las inscripciones activas del alumno
    inscripciones = Inscripcion.objects.filter(
        alumno=alumno,
        activa=True
    ).exclude(horario__isnull=True)
    
    conflictos = []
    for inscripcion in inscripciones:
        horario_existente = inscripcion.horario
        
        # Verificar si son el mismo día
        if horario_existente.dia_semana != nuevo_horario.dia_semana:
            continue
        
        # Convertir a datetime para comparar
        hoy = date.today()
        existente_inicio = datetime.combine(hoy, horario_existente.hora_inicio)
        existente_fin = datetime.combine(hoy, horario_existente.hora_fin)
        nuevo_inicio = datetime.combine(hoy, nuevo_horario.hora_inicio)
        nuevo_fin = datetime.combine(hoy, nuevo_horario.hora_fin)
        
        # Verificar superposición
        if (nuevo_inicio < existente_fin and nuevo_fin > existente_inicio):
            conflictos.append({
                'disciplina': inscripcion.disciplina.get_nombre_display(),
                'horario': f"{horario_existente.get_dia_semana_display()} {horario_existente.hora_inicio.strftime('%H:%M')}-{horario_existente.hora_fin.strftime('%H:%M')}",
                'horario_nuevo': f"{nuevo_horario.get_dia_semana_display()} {nuevo_horario.hora_inicio.strftime('%H:%M')}-{nuevo_horario.hora_fin.strftime('%H:%M')}"
            })
    
    return len(conflictos) > 0, conflictos