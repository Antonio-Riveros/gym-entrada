from django.shortcuts import render
from django.db.models import Sum, Count, Q
from datetime import date, timedelta
from alumnos.models import Alumno
from pagos.models import Pago, Inscripcion
from acceso.models import Acceso
from disciplinas.models import Disciplina

def dashboard(request):
    hoy = date.today()
    mes_actual = hoy.month
    proxima_semana = hoy + timedelta(days=7)
    
    # Cumpleaños del mes
    cumpleaneros = Alumno.objects.filter(
        fecha_nacimiento__month=mes_actual,
        activo=True
    ).order_by('fecha_nacimiento__day').select_related()
    
    # Próximos vencimientos (7 días)
    vencimientos_proximos = Pago.objects.filter(
        fecha_vencimiento__range=[hoy, proxima_semana],
        pagado=False
    ).select_related('alumno').order_by('fecha_vencimiento')
    
    # Estadísticas
    total_alumnos = Alumno.objects.filter(activo=True).count()
    
    total_morosos = Pago.objects.filter(
        pagado=False, 
        fecha_vencimiento__lt=hoy
    ).values('alumno').distinct().count()
    
    # Ingresos del mes
    inicio_mes = hoy.replace(day=1)
    ingresos_mes = Pago.objects.filter(
        fecha_pago__gte=inicio_mes,
        pagado=True
    ).aggregate(Sum('monto'))['monto__sum'] or 0
    
    # Alumnos por disciplina
    alumnos_por_disciplina = []
    disciplinas = Disciplina.objects.all()
    
    for disciplina in disciplinas:
        count = Inscripcion.objects.filter(
            disciplina=disciplina,
            activa=True
        ).count()
        if count > 0:
            total_inscritos = Inscripcion.objects.filter(activa=True).count()
            porcentaje = (count / total_inscritos * 100) if total_inscritos > 0 else 0
            
            alumnos_por_disciplina.append({
                'nombre': disciplina.get_nombre_display(),
                'cantidad': count,
                'precio': disciplina.precio_mensual,
                'total': count * disciplina.precio_mensual,
                'porcentaje': porcentaje
            })
    
    # Últimos accesos
    ultimos_accesos = Acceso.objects.select_related('alumno').order_by('-fecha_hora')[:10]
    
    # Pagos recientes
    pagos_recientes = Pago.objects.select_related('alumno').order_by('-fecha_pago')[:10]
    
    # New students this month
    nuevos_mes = Alumno.objects.filter(fecha_inscripcion__gte=inicio_mes).count()
    
    # Total active subscriptions
    total_inscripciones = Inscripcion.objects.filter(activa=True).count()
    
    # Disciplinas count
    disciplinas_count = Disciplina.objects.count()
    
    context = {
        'cumpleaneros': cumpleaneros,
        'vencimientos_proximos': vencimientos_proximos,
        'ultimos_accesos': ultimos_accesos,
        'pagos_recientes': pagos_recientes,
        'total_alumnos': total_alumnos,
        'total_morosos': total_morosos,
        'ingresos_mes': ingresos_mes,
        'alumnos_por_disciplina': alumnos_por_disciplina,
        'nuevos_mes': nuevos_mes,
        'total_inscripciones': total_inscripciones,
        'disciplinas_count': disciplinas_count,
        'hoy': hoy,
        'proxima_semana': proxima_semana,
    }
    
    return render(request, 'dashboard/dashboard.html', context)