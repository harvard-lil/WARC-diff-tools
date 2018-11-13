from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url

from dashboard import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create/', views.create, name='record'),
    url(r'compare/(?P<compare_id>\d+)', views.compare, name='compare'),
    url(r'view/(?P<compare_id>\d+)', views.view_pair, name='view_pair'),
    # url(r'background/(?P<compare_id>\d+)', views.background_compare, name='background_compare'),
    # manual trigger to compare html of pair
    # url(r'compare_html/(?P<compare_id>\d+)', views.compare_html, name='compare_html'),
    # manual trigger to compare other things
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

