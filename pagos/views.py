from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import date, timedelta
from .models import Pago, Inscripcion
from alumnos.models import Alumno


class PagoListView(ListView):
    model = Pago
    template_name = 'pagos/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 30

    def get_queryset(self):
        queryset = Pago.objects.all().select_related('alumno').order_by('-fecha_pago')

        estado = self.request.GET.get('estado')
        if estado == 'pagado':
            queryset = queryset.filter(pagado=True)
        elif estado == 'pendiente':
            queryset = queryset.filter(pagado=False)

        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha_pago__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_pago__lte=fecha_hasta)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(alumno__nombre__icontains=search) |
                Q(alumno__apellido__icontains=search) |
                Q(alumno__telefono__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoy = date.today()
        mes_actual = hoy.replace(day=1)

        total_pagos = Pago.objects.count()
        pagos_pagados = Pago.objects.filter(pagado=True).count()
        pagos_pendientes = Pago.objects.filter(pagado=False).count()
        ingresos_mes = Pago.objects.filter(
            fecha_pago__gte=mes_actual,
            pagado=True
        ).aggregate(Sum('monto'))['monto__sum'] or 0

        pagos_vencidos = Pago.objects.filter(
            pagado=False,
            fecha_vencimiento__lt=hoy
        ).count()

        context.update({
            'total_pagos': total_pagos,
            'pagos_pagados': pagos_pagados,
            'pagos_pendientes': pagos_pendientes,
            'ingresos_mes': ingresos_mes,
            'pagos_vencidos': pagos_vencidos,
        })

        return context


class PagoCreateView(CreateView):
    model = Pago
    template_name = 'pagos/pago_form.html'
    fields = ['alumno', 'monto', 'descuento_aplicado', 'fecha_vencimiento', 'metodo_pago', 'observaciones']
    success_url = reverse_lazy('pago_list')

    def get_initial(self):
        initial = super().get_initial()
        alumno_id = self.request.GET.get('alumno')
        if alumno_id:
            try:
                alumno = Alumno.objects.get(id=alumno_id)
                initial['alumno'] = alumno

                inscripciones_activas = Inscripcion.objects.filter(alumno=alumno, activa=True)
                monto_sugerido = sum(i.disciplina.precio_mensual for i in inscripciones_activas)
                initial['monto'] = monto_sugerido

            except Alumno.DoesNotExist:
                pass

        initial['fecha_vencimiento'] = timezone.now().date() + timedelta(days=30)
        return initial

    def form_valid(self, form):
        form.instance.pagado = True
        form.instance.fecha_pago = timezone.now().date()
        messages.success(self.request, 'Pago registrado exitosamente.')
        return super().form_valid(form)


class ReportePagosView(ListView):
    template_name = 'pagos/reporte_pagos.html'
    context_object_name = 'pagos'

    def get_queryset(self):
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        return Pago.objects.filter(
            fecha_pago__gte=inicio_mes
        ).select_related('alumno').order_by('-fecha_pago')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        pagos_mes = Pago.objects.filter(fecha_pago__gte=inicio_mes)

        total_mes = pagos_mes.filter(pagado=True).aggregate(Sum('monto'))['monto__sum'] or 0
        pagados_mes = pagos_mes.filter(pagado=True).count()
        pendientes_mes = pagos_mes.filter(pagado=False).count()

        por_metodo = pagos_mes.filter(pagado=True).values('metodo_pago').annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        )

        context.update({
            'total_mes': total_mes,
            'pagados_mes': pagados_mes,
            'pendientes_mes': pendientes_mes,
            'por_metodo': por_metodo,
            'inicio_mes': inicio_mes,
            'hoy': hoy,
        })

        return context


# ✅ NUEVO: Desactivar una inscripción desde el perfil del alumno
@login_required
def inscripcion_desactivar(request, pk):
    inscripcion = get_object_or_404(Inscripcion, pk=pk)
    alumno_id = inscripcion.alumno.id
    if request.method == 'POST':
        inscripcion.activa = False
        inscripcion.save()
        messages.success(request, f'Inscripción en {inscripcion.disciplina.get_nombre_display()} desactivada.')
    return redirect('alumno_detail', pk=alumno_id)


# ✅ NUEVO: Marcar un pago como pagado desde el perfil del alumno
@login_required
def pago_marcar_pagado(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    alumno_id = pago.alumno.id
    if request.method == 'POST':
        pago.pagado = True
        pago.fecha_pago = date.today()
        pago.save()
        messages.success(request, f'Pago de ${pago.monto} marcado como pagado.')
    return redirect('alumno_detail', pk=alumno_id)