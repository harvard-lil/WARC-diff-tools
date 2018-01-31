from django.conf.urls import url, include
from django.contrib import admin
from django.http import HttpResponse

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('dashboard.urls')),
]

def handler404(request):
    return HttpResponse('Page Not Found', status=404)


def handler400(request):
    return HttpResponse('Bad request and Page Not Found')


def handler500(request):
    return HttpResponse('External Server Error >:-(')


