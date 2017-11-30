from django.conf.urls import url
from dashboard import views
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^record', views.record, name='record'),
]
