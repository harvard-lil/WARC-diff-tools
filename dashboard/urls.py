from django.conf.urls import url
from dashboard import views
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create/', views.create, name='record'),
    url(r'compare/(?P<compare_id>\d+)', views.compare, name='compare'),
    url(r'view/(?P<compare_id>\d+)', views.view_pair, name='view_pair')
]
