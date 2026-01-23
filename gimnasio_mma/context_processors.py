from datetime import date, timedelta
from alumnos.models import Alumno
from pagos.models import Pago

def datos_gimnasio(request):
    hoy = date.today()
    
    # Estadísticas para mostrar en el sidebar o header
    total_alumnos_activos = Alumno.objects.filter(activo=True).count()
    
    # Alumnos con pago pendiente
    alumnos_con_pago_pendiente = Pago.objects.filter(
        pagado=False,
        fecha_vencimiento__lt=hoy
    ).values('alumno').distinct().count()
    
    # Próximos vencimientos (3 días)
    proximos_vencimientos = Pago.objects.filter(
        pagado=False,
        fecha_vencimiento__range=[hoy, hoy + timedelta(days=3)]
    ).count()
    
    return {
        'total_alumnos_activos': total_alumnos_activos,
        'alumnos_con_pago_pendiente': alumnos_con_pago_pendiente,
        'proximos_vencimientos': proximos_vencimientos,
        'hoy': hoy,
    }