"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inmuebles/', include('apps.inmuebles.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('solicitudes/', include('apps.seguimiento.urls')),
    path('agenda/', include('apps.agenda.urls')),
    path('administracion/horarios/', include('apps.agenda.urls_horario')),
    path('', include('apps.cuentas.urls')),
]

# En desarrollo con disco local, Django sirve las fotos (siguen exigiendo sesión). Con S3 no aplica.
if settings.DEBUG and not settings.AWS_STORAGE_BUCKET_NAME:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
