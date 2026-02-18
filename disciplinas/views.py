from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, datetime, timedelta
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Disciplina, Horario, Combo
from alumnos.models import Alumno
from pagos.models import Inscripcion, Pago
from .forms import DisciplinaForm, HorarioFormSet, ComboForm


class DisciplinaListView(LoginRequiredMixin, ListView):
    model = Disciplina
    template_name = 'disciplinas/disciplina_list.html'
    context_object_name = 'disciplinas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_disciplinas = Disciplina.objects.count()
        total_inscripciones = Inscripcion.objects.filter(activa=True).count()
        ingresos_mensuales = 0
        for disciplina in Disciplina.objects.all():
            inscripciones_count = Inscripcion.objects.filter(
                disciplina=disciplina, activa=True
            ).count()
            ingresos_mensuales += inscripciones_count * disciplina.precio_mensual
        context.update({
            'total_disciplinas': total_disciplinas,
            'total_inscripciones': total_inscripciones,
            'ingresos_mensuales': ingresos_mensuales,
        })
        return context


class DisciplinaCreateView(LoginRequiredMixin, CreateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'disciplinas/disciplina_form.html'
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
        inscripciones_count = Inscripcion.objects.filter(
            disciplina=self.object, activa=True
        ).count()
        context['ingresos_mensuales'] = inscripciones_count * self.object.precio_mensual
        context['horarios_activos'] = self.object.horarios.filter(activo=True).count()
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


class HorarioDetailView(LoginRequiredMixin, DetailView):
    model = Horario
    template_name = 'disciplinas/horario_detail.html'
    context_object_name = 'horario'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        horario = self.object
        inscripciones = Inscripcion.objects.filter(
            horario=horario, activa=True
        ).select_related('alumno')
        alumnos_con_estado = []
        for inscripcion in inscripciones:
            alumno = inscripcion.alumno
            tiene_pago_pendiente = Pago.objects.filter(
                alumno=alumno, pagado=False,
                fecha_vencimiento__lt=timezone.now().date()
            ).exists()
            alumnos_con_estado.append({
                'alumno': alumno,
                'inscripcion': inscripcion,
                'tiene_pago_pendiente': tiene_pago_pendiente,
            })
        espacios_disponibles = horario.capacidad_maxima - inscripciones.count()
        porcentaje_ocupacion = (
            inscripciones.count() / horario.capacidad_maxima * 100
        ) if horario.capacidad_maxima > 0 else 0
        context.update({
            'alumnos_inscritos': alumnos_con_estado,
            'total_inscritos': inscripciones.count(),
            'espacios_disponibles': espacios_disponibles,
            'porcentaje_ocupacion': round(porcentaje_ocupacion, 1),
        })
        return context


class PreciosRapidosView(LoginRequiredMixin, View):
    template_name = 'disciplinas/precios_rapidos.html'

    def get(self, request):
        disciplinas = Disciplina.objects.all().order_by('nombre')
        combos = Combo.objects.filter(activo=True).order_by('nombre')
        return render(request, self.template_name, {
            'disciplinas': disciplinas,
            'combos': combos,
        })

    def post(self, request):
        for key, value in request.POST.items():
            if key.startswith('precio_disciplina_'):
                disciplina_id = key.replace('precio_disciplina_', '')
                try:
                    disciplina = Disciplina.objects.get(id=disciplina_id)
                    nuevo_precio = value.replace('$', '').replace('.', '').replace(',', '.')
                    disciplina.precio_mensual = float(nuevo_precio)
                    disciplina.precio_clase_suelta = float(nuevo_precio) / 10
                    disciplina.save()
                except (Disciplina.DoesNotExist, ValueError):
                    continue
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
        total_combos = Combo.objects.count()
        combos_activos = Combo.objects.filter(activo=True).count()
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
        combo = form.save(commit=False)
        precio_total_disciplinas = sum(
            d.precio_mensual for d in form.cleaned_data['disciplinas']
        )
        if precio_total_disciplinas > 0:
            descuento = (
                (precio_total_disciplinas - combo.precio_combo) /
                precio_total_disciplinas * 100
            )
            combo.descuento_aplicado = round(descuento, 2)
        combo.save()
        form.save_m2m()
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
        combo = form.save(commit=False)
        precio_total_disciplinas = sum(
            d.precio_mensual for d in form.cleaned_data['disciplinas']
        )
        if precio_total_disciplinas > 0:
            descuento = (
                (precio_total_disciplinas - combo.precio_combo) /
                precio_total_disciplinas * 100
            )
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
        precio_normal = combo.calcular_precio_normal()
        ahorro = precio_normal - combo.precio_combo
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            disciplinas_ids = data.get('disciplinas', [])
            disciplinas = Disciplina.objects.filter(id__in=disciplinas_ids)
            precio_total = sum(d.precio_mensual for d in disciplinas)
            return JsonResponse({
                'precio_total': float(precio_total),
                'cantidad_disciplinas': len(disciplinas_ids)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


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
            for disciplina in disciplinas:
                disciplina.precio_mensual = precio_mensual
                if precio_clase_suelta:
                    disciplina.precio_clase_suelta = precio_clase_suelta
                else:
                    disciplina.precio_clase_suelta = float(precio_mensual) * 0.1
                disciplina.save()
            return JsonResponse({
                'success': True,
                'message': f'Precios actualizados en {len(disciplinas)} disciplinas'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


def verificar_conflicto_horario(alumno, nuevo_horario):
    if not nuevo_horario:
        return False, []
    inscripciones = Inscripcion.objects.filter(
        alumno=alumno, activa=True
    ).exclude(horario__isnull=True)
    conflictos = []
    for inscripcion in inscripciones:
        horario_existente = inscripcion.horario
        if horario_existente.dia_semana != nuevo_horario.dia_semana:
            continue
        hoy = date.today()
        existente_inicio = datetime.combine(hoy, horario_existente.hora_inicio)
        existente_fin = datetime.combine(hoy, horario_existente.hora_fin)
        nuevo_inicio = datetime.combine(hoy, nuevo_horario.hora_inicio)
        nuevo_fin = datetime.combine(hoy, nuevo_horario.hora_fin)
        if nuevo_inicio < existente_fin and nuevo_fin > existente_inicio:
            conflictos.append({
                'disciplina': inscripcion.disciplina.get_nombre_display(),
                'horario': f"{horario_existente.get_dia_semana_display()} {horario_existente.hora_inicio.strftime('%H:%M')}-{horario_existente.hora_fin.strftime('%H:%M')}",
                'horario_nuevo': f"{nuevo_horario.get_dia_semana_display()} {nuevo_horario.hora_inicio.strftime('%H:%M')}-{nuevo_horario.hora_fin.strftime('%H:%M')}"
            })
    return len(conflictos) > 0, conflictos


class InscripcionRapidaView(LoginRequiredMixin, View):
    template_name = 'alumnos/inscripcion_rapida.html'

    def get(self, request):
        alumnos = Alumno.objects.filter(activo=True).order_by('apellido', 'nombre')
        disciplinas = Disciplina.objects.all().order_by('nombre')
        return render(request, self.template_name, {
            'alumnos': alumnos,
            'disciplinas': disciplinas,
        })

    def post(self, request):
        try:
            alumno_id = request.POST.get('alumno')
            disciplina_id = request.POST.get('disciplina')
            horario_id = request.POST.get('horario', None)
            if not alumno_id or not disciplina_id:
                messages.error(request, 'Por favor, selecciona un alumno y una disciplina.')
                return redirect('inscripcion_rapida')
            alumno = get_object_or_404(Alumno, id=alumno_id)
            disciplina = get_object_or_404(Disciplina, id=disciplina_id)
            if Inscripcion.objects.filter(alumno=alumno, disciplina=disciplina, activa=True).exists():
                messages.warning(request, f'{alumno} ya está inscrito en {disciplina.get_nombre_display()}.')
                return redirect('inscripcion_rapida')
            horario = None
            if horario_id:
                horario = get_object_or_404(Horario, id=horario_id)
                tiene_conflicto, conflictos = verificar_conflicto_horario(alumno, horario)
                if tiene_conflicto:
                    mensaje_conflicto = '❌ No se puede inscribir: Horarios en conflicto:<br>'
                    for conflicto in conflictos:
                        mensaje_conflicto += f"- Ya inscrito en {conflicto['disciplina']} ({conflicto['horario']})<br>"
                    mensaje_conflicto += f"No se puede asignar {disciplina.get_nombre_display()} ({conflicto['horario_nuevo']})"
                    messages.error(request, mensaje_conflicto)
                    return redirect('inscripcion_rapida')
                if Inscripcion.objects.filter(alumno=alumno, horario=horario, activa=True).exists():
                    messages.warning(request, f'{alumno} ya tiene una inscripción en este horario.')
                    return redirect('inscripcion_rapida')
                inscritos_en_horario = Inscripcion.objects.filter(horario=horario, activa=True).count()
                if inscritos_en_horario >= horario.capacidad_maxima:
                    messages.error(request, f'El horario seleccionado está lleno ({horario.capacidad_maxima}/{horario.capacidad_maxima}).')
                    return redirect('inscripcion_rapida')
            inscripcion = Inscripcion.objects.create(
                alumno=alumno, disciplina=disciplina, horario=horario
            )
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
    if request.method == 'GET' and 'disciplina_id' in request.GET:
        disciplina_id = request.GET.get('disciplina_id')
        alumno_id = request.GET.get('alumno_id')
        try:
            disciplina = Disciplina.objects.get(id=disciplina_id)
            horarios = Horario.objects.filter(
                disciplina=disciplina, activo=True
            ).order_by('dia_semana', 'hora_inicio')
            horarios_data = []
            for horario in horarios:
                inscritos_count = Inscripcion.objects.filter(horario=horario, activa=True).count()
                disponible = horario.capacidad_maxima - inscritos_count
                lleno = disponible <= 0
                conflicto = False
                if alumno_id:
                    try:
                        alumno = Alumno.objects.get(id=alumno_id)
                        tiene_conflicto, _ = verificar_conflicto_horario(alumno, horario)
                        conflicto = tiene_conflicto
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
                    'lleno': lleno,
                    'conflicto': conflicto,
                    'mensaje_conflicto': ' (CONFLICTO DE HORARIO)' if conflicto else ''
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


class HorarioCreateView(LoginRequiredMixin, CreateView):
    model = Horario
    template_name = 'disciplinas/horario_form.html'
    fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        disciplina_id = self.kwargs.get('disciplina_id')
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)
        context['disciplina'] = disciplina
        return context

    def form_valid(self, form):
        disciplina_id = self.kwargs.get('disciplina_id')
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)
        form.instance.disciplina = disciplina
        messages.success(self.request, 'Horario creado exitosamente.')
        return super().form_valid(form)

    def get_success_url(self):
        disciplina_id = self.kwargs.get('disciplina_id')
        return reverse('disciplina_update', kwargs={'pk': disciplina_id})


class HorarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Horario
    template_name = 'disciplinas/horario_form.html'
    fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'capacidad_maxima', 'activo']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplina'] = self.object.disciplina
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Horario actualizado exitosamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('disciplina_update', kwargs={'pk': self.object.disciplina.id})