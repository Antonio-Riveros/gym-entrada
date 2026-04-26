from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import date, timedelta, datetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Alumno
from disciplinas.models import Disciplina, Horario, Combo
from pagos.models import Inscripcion, Pago
from acceso.models import Acceso


class InscripcionRapidaView(LoginRequiredMixin, View):
    """Vista principal para inscripción rápida"""
    template_name = 'alumnos/inscripcion_rapida.html'

    def get(self, request):
        alumnos = Alumno.objects.filter(activo=True).order_by('apellido', 'nombre')
        disciplinas = Disciplina.objects.all().order_by('nombre')
        # ✅ CORREGIDO: ahora pasa combos al template
        combos = Combo.objects.filter(activo=True).prefetch_related('disciplinas').order_by('nombre')

        return render(request, self.template_name, {
            'alumnos': alumnos,
            'disciplinas': disciplinas,
            'combos': combos,
        })

    def post(self, request):
        try:
            alumno_id = request.POST.get('alumno')
            disciplina_id = request.POST.get('disciplina')
            combo_id = request.POST.get('combo_id')  # ✅ CORREGIDO: leer combo_id
            horario_id = request.POST.get('horario', None)

            if not alumno_id:
                messages.error(request, 'Por favor, selecciona un alumno.')
                return redirect('inscripcion_rapida')

            alumno = get_object_or_404(Alumno, id=alumno_id)

            # ✅ CORREGIDO: si viene combo_id, procesar como combo
            if combo_id:
                return self._procesar_combo(request, alumno, combo_id)

            # Procesar disciplina individual
            if not disciplina_id:
                messages.error(request, 'Por favor, selecciona una disciplina o combo.')
                return redirect('inscripcion_rapida')

            disciplina = get_object_or_404(Disciplina, id=disciplina_id)

            if Inscripcion.objects.filter(alumno=alumno, disciplina=disciplina, activa=True).exists():
                messages.warning(request, f'{alumno} ya está inscrito en {disciplina.get_nombre_display()}.')
                return redirect('inscripcion_rapida')

            horario = None
            if horario_id:
                horario = get_object_or_404(Horario, id=horario_id)

                from disciplinas.views import verificar_conflicto_horario
                tiene_conflicto, conflictos = verificar_conflicto_horario(alumno, horario)
                if tiene_conflicto:
                    mensaje_conflicto = '❌ Horarios en conflicto:<br>'
                    for conflicto in conflictos:
                        mensaje_conflicto += f"- Ya inscrito en {conflicto['disciplina']} ({conflicto['horario']})<br>"
                    messages.error(request, mensaje_conflicto)
                    return redirect('inscripcion_rapida')

                if Inscripcion.objects.filter(alumno=alumno, horario=horario, activa=True).exists():
                    messages.warning(request, f'{alumno} ya tiene una inscripción en este horario.')
                    return redirect('inscripcion_rapida')

                inscritos_en_horario = Inscripcion.objects.filter(horario=horario, activa=True).count()
                if inscritos_en_horario >= horario.capacidad_maxima:
                    messages.error(request, f'El horario está lleno ({horario.capacidad_maxima}/{horario.capacidad_maxima}).')
                    return redirect('inscripcion_rapida')

            inscripcion = Inscripcion.objects.create(
                alumno=alumno,
                disciplina=disciplina,
                horario=horario
            )

            if request.POST.get('registrar_pago') == 'on':
                self._registrar_pago_automatico(alumno, disciplina, inscripcion)
                messages.success(request, f'✅ {alumno} inscrito y pago registrado en {disciplina.get_nombre_display()}.')
            else:
                messages.success(request, f'✅ {alumno} inscrito en {disciplina.get_nombre_display()}.')

            return redirect('inscripcion_rapida')

        except Exception as e:
            messages.error(request, f'Error al procesar la inscripción: {str(e)}')
            return redirect('inscripcion_rapida')

    def _procesar_combo(self, request, alumno, combo_id):
        """✅ NUEVO: Inscribe al alumno en todas las disciplinas del combo"""
        try:
            combo = get_object_or_404(Combo, id=combo_id, activo=True)
            disciplinas_combo = combo.disciplinas.all()

            if not disciplinas_combo.exists():
                messages.error(request, f'El combo "{combo.nombre}" no tiene disciplinas asignadas.')
                return redirect('inscripcion_rapida')

            inscriptos = []
            ya_inscriptos = []

            for disciplina in disciplinas_combo:
                if Inscripcion.objects.filter(alumno=alumno, disciplina=disciplina, activa=True).exists():
                    ya_inscriptos.append(disciplina.get_nombre_display())
                else:
                    Inscripcion.objects.create(
                        alumno=alumno,
                        disciplina=disciplina,
                        horario=None
                    )
                    inscriptos.append(disciplina.get_nombre_display())

            if ya_inscriptos:
                messages.warning(request, f'Ya estaba inscrito en: {", ".join(ya_inscriptos)}.')

            if inscriptos:
                if request.POST.get('registrar_pago') == 'on':
                    Pago.objects.create(
                        alumno=alumno,
                        monto=combo.precio_combo,
                        fecha_vencimiento=date.today() + timedelta(days=30),
                        metodo_pago='EFECTIVO',
                        pagado=True,
                        observaciones=f"Inscripción combo: {combo.nombre} ({', '.join(inscriptos)})"
                    )
                    messages.success(request, f'✅ {alumno} inscrito en combo "{combo.nombre}" y pago registrado. Disciplinas: {", ".join(inscriptos)}.')
                else:
                    messages.success(request, f'✅ {alumno} inscrito en combo "{combo.nombre}". Disciplinas: {", ".join(inscriptos)}.')
            else:
                messages.warning(request, f'{alumno} ya estaba inscrito en todas las disciplinas del combo.')

            return redirect('inscripcion_rapida')

        except Exception as e:
            messages.error(request, f'Error al procesar el combo: {str(e)}')
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


def buscar_alumnos_ajax(request):
    """Búsqueda AJAX de alumnos para el autocomplete"""
    if request.method == 'GET' and 'term' in request.GET:
        term = request.GET.get('term', '').lower()

        if len(term) >= 2:
            alumnos = Alumno.objects.filter(
                Q(nombre__icontains=term) |
                Q(apellido__icontains=term) |
                Q(telefono__icontains=term) |
                Q(email__icontains=term)
            ).filter(activo=True)[:10]

            results = []
            for alumno in alumnos:
                results.append({
                    'id': alumno.id,
                    'value': f"{alumno.nombre} {alumno.apellido}",
                    'label': f"{alumno.nombre} {alumno.apellido} - Tel: {alumno.telefono}",
                    'telefono': alumno.telefono,
                    'email': alumno.email or 'Sin email',
                })

            return JsonResponse(results, safe=False)

    return JsonResponse([], safe=False)


def obtener_horarios_disciplina(request):
    """Obtiene los horarios disponibles para una disciplina específica"""
    if request.method == 'GET' and 'disciplina_id' in request.GET:
        disciplina_id = request.GET.get('disciplina_id')

        try:
            disciplina = Disciplina.objects.get(id=disciplina_id)
            horarios = Horario.objects.filter(disciplina=disciplina).order_by('dia_semana', 'hora_inicio')

            horarios_data = []
            for horario in horarios:
                inscritos_count = Inscripcion.objects.filter(horario=horario, activa=True).count()
                disponible = horario.capacidad_maxima - inscritos_count

                horarios_data.append({
                    'id': horario.id,
                    'dia': horario.get_dia_semana_display(),
                    'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
                    'hora_fin': horario.hora_fin.strftime('%H:%M'),
                    'capacidad': horario.capacidad_maxima,
                    'inscritos': inscritos_count,
                    'disponible': disponible,
                    'lleno': disponible <= 0
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


def obtener_info_alumno(request):
    """Obtiene información detallada de un alumno"""
    if request.method == 'GET' and 'alumno_id' in request.GET:
        alumno_id = request.GET.get('alumno_id')

        try:
            alumno = Alumno.objects.get(id=alumno_id)

            inscripciones_activas = Inscripcion.objects.filter(alumno=alumno, activa=True)
            disciplinas_inscritas = [insc.disciplina.get_nombre_display() for insc in inscripciones_activas]

            tiene_pago_pendiente = Pago.objects.filter(
                alumno=alumno,
                pagado=False,
                fecha_vencimiento__lt=date.today()
            ).exists()

            return JsonResponse({
                'success': True,
                'alumno': {
                    'id': alumno.id,
                    'nombre_completo': f"{alumno.nombre} {alumno.apellido}",
                    'telefono': alumno.telefono,
                    'email': alumno.email or 'Sin email',
                    'fecha_inscripcion': alumno.fecha_inscripcion.strftime('%d/%m/%Y'),
                    'activo': alumno.activo,
                    'tiene_rfid': bool(alumno.rfid),
                },
                'inscripciones': {
                    'total': inscripciones_activas.count(),
                    'disciplinas': disciplinas_inscritas,
                },
                'estado_pago': {
                    'tiene_pendiente': tiene_pago_pendiente,
                    'mensaje': 'Tiene pagos pendientes' if tiene_pago_pendiente else 'Al día'
                }
            })

        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'})

    return JsonResponse({'success': False, 'error': 'Parámetros inválidos'})


class AlumnoListView(LoginRequiredMixin, ListView):
    model = Alumno
    template_name = 'alumnos/alumno_list.html'
    context_object_name = 'alumnos'
    paginate_by = 100

    def get_queryset(self):
        queryset = Alumno.objects.all().order_by('apellido', 'nombre').annotate(
            inscripciones_activas=Count(
                'inscripciones',
                filter=Q(inscripciones__activa=True)
            )
        )

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(apellido__icontains=search_query) |
                Q(telefono__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(rfid__icontains=search_query)
            )

        status = self.request.GET.get('status', '')
        if status == 'activo':
            queryset = queryset.filter(activo=True)
        elif status == 'inactivo':
            queryset = queryset.filter(activo=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_alumnos = Alumno.objects.count()
        alumnos_activos = Alumno.objects.filter(activo=True).count()
        porcentaje_activos = (alumnos_activos / total_alumnos * 100) if total_alumnos > 0 else 0

        first_day = timezone.now().replace(day=1)
        nuevos_mes = Alumno.objects.filter(fecha_inscripcion__gte=first_day).count()

        con_deuda = Pago.objects.filter(
            pagado=False,
            fecha_vencimiento__lt=timezone.now().date()
        ).values('alumno').distinct().count()

        total_inscripciones = Inscripcion.objects.filter(activa=True).count()
        disciplinas = Disciplina.objects.all().order_by('nombre')

        context.update({
            'total_alumnos': total_alumnos,
            'alumnos_activos': alumnos_activos,
            'porcentaje_activos': round(porcentaje_activos, 1),
            'nuevos_mes': nuevos_mes,
            'con_deuda': con_deuda,
            'total_inscripciones': total_inscripciones,
            'disciplinas': disciplinas,
            'today': date.today(),
        })

        return context


class AlumnoCreateView(LoginRequiredMixin, CreateView):
    model = Alumno
    template_name = 'alumnos/alumno_form.html'
    fields = ['nombre', 'apellido', 'telefono', 'email', 'fecha_nacimiento', 'rfid', 'foto', 'activo']
    success_url = reverse_lazy('alumno_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nuevo Alumno'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Alumno {self.object} creado exitosamente.')
        return response


class AlumnoUpdateView(LoginRequiredMixin, UpdateView):
    model = Alumno
    template_name = 'alumnos/alumno_form.html'
    fields = ['nombre', 'apellido', 'telefono', 'email', 'fecha_nacimiento', 'rfid', 'foto', 'activo']
    success_url = reverse_lazy('alumno_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Alumno'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Alumno {self.object} actualizado exitosamente.')
        return response


class AlumnoDetailView(LoginRequiredMixin, DetailView):
    model = Alumno
    template_name = 'alumnos/alumno_detail.html'
    context_object_name = 'alumno'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alumno = self.object

        inscripciones = Inscripcion.objects.filter(alumno=alumno, activa=True).select_related('disciplina', 'horario')
        pagos = Pago.objects.filter(alumno=alumno).order_by('-fecha_pago')
        pagos_pagados = pagos.filter(pagado=True).count()
        pagos_pendientes = pagos.filter(pagado=False).count()
        total_invertido = pagos.filter(pagado=True).aggregate(Sum('monto'))['monto__sum'] or 0
        accesos = Acceso.objects.filter(alumno=alumno).order_by('-fecha_hora')[:50]
        dias_alumno = (timezone.now().date() - alumno.fecha_inscripcion).days
        proximo_vencimiento = pagos.filter(pagado=False).order_by('fecha_vencimiento').first()

        context.update({
            'inscripciones': inscripciones,
            'pagos': pagos[:20],
            'pagos_pagados': pagos_pagados,
            'pagos_pendientes': pagos_pendientes,
            'total_invertido': total_invertido,
            'accesos': accesos,
            'dias_alumno': dias_alumno,
            'proximo_vencimiento': proximo_vencimiento,
        })

        return context


class RegistroRapidoCompletoView(LoginRequiredMixin, View):
    """Vista para crear alumno, inscribir y registrar pago en un solo paso"""
    template_name = 'alumnos/registro_rapido_completo.html'

    def get(self, request):
        try:
            disciplinas = Disciplina.objects.all().order_by('nombre')
            combos = Combo.objects.filter(activo=True).order_by('nombre')

            return render(request, self.template_name, {
                'disciplinas': disciplinas,
                'combos': combos,
            })
        except Exception as e:
            messages.error(request, f'Error al cargar el formulario: {str(e)}')
            return redirect('inscripcion_rapida')

    def post(self, request):
        try:
            alumno = Alumno.objects.create(
                nombre=request.POST.get('nombre'),
                apellido=request.POST.get('apellido'),
                telefono=request.POST.get('telefono'),
                email=request.POST.get('email') or None,
                fecha_nacimiento=request.POST.get('fecha_nacimiento') or date.today(),
                rfid=request.POST.get('rfid') or None,
                activo=True
            )

            seleccion = request.POST.get('disciplina', '')
            monto_pago = 0

            if seleccion.startswith('disciplina-'):
                disciplina_id = seleccion.replace('disciplina-', '')
                disciplina = Disciplina.objects.get(id=disciplina_id)
                monto_pago = disciplina.precio_mensual
                Inscripcion.objects.create(alumno=alumno, disciplina=disciplina, horario=None, activa=True)
                mensaje_disciplina = f"inscrito en {disciplina.get_nombre_display()}"

            elif seleccion.startswith('combo-'):
                combo_id = seleccion.replace('combo-', '')
                combo = Combo.objects.get(id=combo_id)
                monto_pago = combo.precio_combo
                for disciplina in combo.disciplinas.all():
                    Inscripcion.objects.create(alumno=alumno, disciplina=disciplina, horario=None, activa=True)
                mensaje_disciplina = f"inscrito en combo: {combo.nombre}"
            else:
                raise ValueError("No se seleccionó ninguna disciplina/combo")

            if request.POST.get('registrar_pago') == 'on':
                Pago.objects.create(
                    alumno=alumno,
                    monto=monto_pago,
                    fecha_vencimiento=date.today() + timedelta(days=30),
                    metodo_pago=request.POST.get('metodo_pago', 'EFECTIVO'),
                    pagado=True,
                    observaciones=f"Primer pago - {mensaje_disciplina}"
                )
                mensaje_pago = "y pago registrado"
            else:
                mensaje_pago = "sin registrar pago (se puede hacer después)"

            Acceso.objects.create(alumno=alumno, tipo='MANUAL', observacion='Alta de alumno - Registro rápido')

            messages.success(request, f'✅ {alumno} creado exitosamente, {mensaje_disciplina} {mensaje_pago}.')
            return redirect('alumno_detail', pk=alumno.id)

        except Exception as e:
            messages.error(request, f'❌ Error en el registro: {str(e)}')
            return redirect('registro_rapido_completo')


def obtener_info_disciplina(request, pk):
    """Obtiene información detallada de una disciplina"""
    try:
        disciplina = Disciplina.objects.get(id=pk)
        horarios_count = Horario.objects.filter(disciplina=disciplina).count()

        return JsonResponse({
            'success': True,
            'nombre': disciplina.get_nombre_display(),
            'descripcion': disciplina.descripcion,
            'precio': str(disciplina.precio_mensual),
            'precio_clase_suelta': str(disciplina.precio_clase_suelta),
            'horarios_count': horarios_count
        })
    except Disciplina.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Disciplina no encontrada'})


@csrf_exempt
def activar_alumno_api(request, pk):
    if request.method == 'POST':
        try:
            alumno = Alumno.objects.get(id=pk)
            alumno.activo = True
            alumno.save()
            return JsonResponse({'success': True, 'message': f'Alumno {alumno} activado exitosamente.'})
        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def desactivar_alumno_api(request, pk):
    if request.method == 'POST':
        try:
            alumno = Alumno.objects.get(id=pk)
            alumno.activo = False
            alumno.save()
            return JsonResponse({'success': True, 'message': f'Alumno {alumno} desactivado exitosamente.'})
        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def eliminar_alumno_api(request, pk):
    if request.method == 'POST':
        try:
            alumno = Alumno.objects.get(id=pk)
            if Inscripcion.objects.filter(alumno=alumno, activa=True).exists():
                alumno.activo = False
                alumno.save()
                mensaje = f'Alumno {alumno} desactivado (tenía inscripciones activas)'
            else:
                alumno_nombre = str(alumno)
                alumno.delete()
                mensaje = f'Alumno {alumno_nombre} eliminado exitosamente.'
            return JsonResponse({'success': True, 'message': mensaje})
        except Alumno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Alumno no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def activar_alumnos_lote_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            alumnos = Alumno.objects.filter(id__in=ids)
            count = alumnos.count()
            alumnos.update(activo=True)
            return JsonResponse({'success': True, 'message': f'{count} alumnos reactivados exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def desactivar_alumnos_lote_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            alumnos = Alumno.objects.filter(id__in=ids)
            count = alumnos.count()
            alumnos.update(activo=False)
            return JsonResponse({'success': True, 'message': f'{count} alumnos desactivados exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def eliminar_alumnos_lote_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            alumnos = Alumno.objects.filter(id__in=ids)
            eliminados = 0
            desactivados = 0
            for alumno in alumnos:
                if Inscripcion.objects.filter(alumno=alumno, activa=True).exists():
                    alumno.activo = False
                    alumno.save()
                    desactivados += 1
                else:
                    alumno.delete()
                    eliminados += 1
            mensaje = f'{eliminados} alumnos eliminados y {desactivados} desactivados (tenían inscripciones activas).'
            return JsonResponse({'success': True, 'message': mensaje})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def asignar_disciplina_lote_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            disciplina_id = data.get('disciplina_id')
            horario_id = data.get('horario_id')
            registrar_pago = data.get('registrar_pago', False)

            if not disciplina_id:
                return JsonResponse({'success': False, 'error': 'Se requiere una disciplina'})

            disciplina = Disciplina.objects.get(id=disciplina_id)
            horario = Horario.objects.get(id=horario_id) if horario_id else None

            asignados = 0
            for alumno_id in ids:
                try:
                    alumno = Alumno.objects.get(id=alumno_id)
                    if not Inscripcion.objects.filter(alumno=alumno, disciplina=disciplina, activa=True).exists():
                        inscripcion = Inscripcion.objects.create(
                            alumno=alumno,
                            disciplina=disciplina,
                            horario=horario
                        )
                        if registrar_pago:
                            Pago.objects.create(
                                alumno=alumno,
                                monto=disciplina.precio_mensual,
                                fecha_vencimiento=date.today() + timedelta(days=30),
                                metodo_pago='EFECTIVO',
                                pagado=True,
                                observaciones=f"Inscripción a {disciplina.get_nombre_display()}",
                                relacion_inscripcion=inscripcion
                            )
                        asignados += 1
                except Alumno.DoesNotExist:
                    continue

            return JsonResponse({'success': True, 'message': f'Disciplina asignada a {asignados} alumnos exitosamente.'})

        except Disciplina.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Disciplina no encontrada'})
        except Horario.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Horario no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})