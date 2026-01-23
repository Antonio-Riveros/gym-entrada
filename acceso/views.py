from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Acceso
from alumnos.models import Alumno

class AccesoListView(ListView):
    model = Acceso
    template_name = 'acceso/acceso_list.html'
    context_object_name = 'accesos'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Acceso.objects.all().select_related('alumno').order_by('-fecha_hora')
        
        # Filtros
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por fecha
        fecha = self.request.GET.get('fecha')
        if fecha:
            queryset = queryset.filter(fecha_hora__date=fecha)
        
        # Búsqueda por alumno
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
        
        # Estadísticas del día
        hoy = timezone.now().date()
        accesos_hoy = Acceso.objects.filter(fecha_hora__date=hoy)
        
        total_hoy = accesos_hoy.count()
        rfid_hoy = accesos_hoy.filter(tipo='RFID').count()
        manual_hoy = accesos_hoy.filter(tipo='MANUAL').count()
        denegado_hoy = accesos_hoy.filter(tipo='DENEGADO').count()
        
        # Última hora
        ultima_hora = timezone.now() - timedelta(hours=1)
        accesos_ultima_hora = Acceso.objects.filter(fecha_hora__gte=ultima_hora).count()
        
        context.update({
            'total_hoy': total_hoy,
            'rfid_hoy': rfid_hoy,
            'manual_hoy': manual_hoy,
            'denegado_hoy': denegado_hoy,
            'accesos_ultima_hora': accesos_ultima_hora,
            'hoy': hoy,
        })
        
        return context

class AccesoCreateView(CreateView):
    model = Acceso
    template_name = 'acceso/acceso_form.html'
    fields = ['alumno', 'tipo', 'observacion']
    success_url = reverse_lazy('acceso_list')
    
    def get_initial(self):
        initial = super().get_initial()
        # Si viene de un alumno específico
        alumno_id = self.request.GET.get('alumno')
        if alumno_id:
            try:
                alumno = Alumno.objects.get(id=alumno_id)
                initial['alumno'] = alumno
                initial['tipo'] = 'MANUAL'
            except Alumno.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        # Establecer fecha y hora actual
        form.instance.fecha_hora = timezone.now()
        
        # Verificar si el alumno tiene pago pendiente
        alumno = form.cleaned_data.get('alumno')
        if alumno:
            tiene_pago_pendiente = alumno.pagos.filter(
                pagado=False,
                fecha_vencimiento__lt=timezone.now().date()
            ).exists()
            
            if tiene_pago_pendiente and form.cleaned_data.get('tipo') != 'DENEGADO':
                form.instance.tipo = 'DENEGADO'
                form.instance.observacion = f"Acceso denegado - Pago pendiente. {form.instance.observacion or ''}"
                messages.warning(self.request, 'Acceso denegado: Alumno con pago pendiente.')
            else:
                messages.success(self.request, 'Acceso registrado exitosamente.')
        
        return super().form_valid(form)

def acceso_rfid(request):
    """Vista para simular acceso por RFID"""
    if request.method == 'POST':
        rfid_code = request.POST.get('rfid_code')
        
        try:
            alumno = Alumno.objects.get(rfid=rfid_code, activo=True)
            
            # Verificar si tiene pagos pendientes
            tiene_pago_pendiente = alumno.pagos.filter(
                pagado=False,
                fecha_vencimiento__lt=timezone.now().date()
            ).exists()
            
            if tiene_pago_pendiente:
                # Registrar acceso denegado
                Acceso.objects.create(
                    alumno=alumno,
                    tipo='DENEGADO',
                    observacion='Pago pendiente'
                )
                return render(request, 'acceso/acceso_rfid.html', {
                    'acceso': False,
                    'alumno': alumno,
                    'mensaje': 'ACCESO DENEGADO - Pago pendiente'
                })
            else:
                # Registrar acceso permitido
                Acceso.objects.create(
                    alumno=alumno,
                    tipo='RFID',
                    observacion='Acceso por RFID'
                )
                return render(request, 'acceso/acceso_rfid.html', {
                    'acceso': True,
                    'alumno': alumno,
                    'mensaje': 'ACCESO PERMITIDO'
                })
                
        except Alumno.DoesNotExist:
            # Registrar acceso denegado para RFID no reconocido
            Acceso.objects.create(
                alumno=None,
                tipo='DENEGADO',
                observacion=f'RFID no reconocido: {rfid_code}'
            )
            return render(request, 'acceso/acceso_rfid.html', {
                'acceso': False,
                'alumno': None,
                'mensaje': 'RFID NO RECONOCIDO'
            })
    
    return render(request, 'acceso/acceso_rfid.html')