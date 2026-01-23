from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('alumnos/', include('alumnos.urls')),
    path('disciplinas/', include('disciplinas.urls')),
    path('pagos/', include('pagos.urls')),
    path('acceso/', include('acceso.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)