from django.shortcuts import render
from django.db.models import Sum
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from alumnos.models import Alumno
from pagos.models import Pago, Inscripcion
from disciplinas.models import Disciplina, Combo


def dashboard(request):
    hoy = date.today()
    proxima_semana = hoy + timedelta(days=7)
    inicio_mes = hoy.replace(day=1)

    # Próximos vencimientos (7 días)
    vencimientos_proximos = Pago.objects.filter(
        fecha_vencimiento__range=[hoy, proxima_semana],
        pagado=False
    ).select_related('alumno').order_by('fecha_vencimiento')

    # Estadísticas generales
    total_alumnos = Alumno.objects.filter(activo=True).count()

    total_morosos = Pago.objects.filter(
        pagado=False,
        fecha_vencimiento__lt=hoy
    ).values('alumno').distinct().count()

    ingresos_mes = Pago.objects.filter(
        fecha_pago__gte=inicio_mes,
        pagado=True
    ).aggregate(Sum('monto'))['monto__sum'] or 0

    nuevos_mes = Alumno.objects.filter(fecha_inscripcion__gte=inicio_mes).count()
    total_inscripciones = Inscripcion.objects.filter(activa=True).count()
    disciplinas_count = Disciplina.objects.count()
    combos_count = Combo.objects.filter(activo=True).count()

    # Pagos recientes
    pagos_recientes = Pago.objects.select_related('alumno').order_by('-fecha_pago')[:10]

    # Alumnos por disciplina — con manejo de valores corruptos en BD
    alumnos_por_disciplina = []
    total_inscritos = max(total_inscripciones, 1)

    try:
        for disciplina in Disciplina.objects.all():
            try:
                count = Inscripcion.objects.filter(
                    disciplina=disciplina,
                    activa=True
                ).count()

                if count == 0:
                    continue

                try:
                    precio = Decimal(str(disciplina.precio_mensual))
                except (InvalidOperation, TypeError):
                    precio = Decimal('0')

                total = count * precio
                porcentaje = round(count / total_inscritos * 100, 1)

                alumnos_por_disciplina.append({
                    'nombre': disciplina.get_nombre_display(),
                    'cantidad': count,
                    'total': total,
                    'porcentaje': porcentaje,
                })
            except Exception:
                continue
    except Exception:
        pass

    context = {
        'vencimientos_proximos': vencimientos_proximos,
        'pagos_recientes': pagos_recientes,
        'total_alumnos': total_alumnos,
        'total_morosos': total_morosos,
        'ingresos_mes': ingresos_mes,
        'alumnos_por_disciplina': alumnos_por_disciplina,
        'nuevos_mes': nuevos_mes,
        'total_inscripciones': total_inscripciones,
        'disciplinas_count': disciplinas_count,
        'combos_count': combos_count,
        'hoy': hoy,
    }

    return render(request, 'dashboard/dashboard.html', context)