from django.conf.urls import url
from dashboard import views

old_guid_pattern = r'(?P<old_guid>[a-zA-Z0-9\-]{8,11})'
new_guid_pattern = r'(?P<new_guid>[a-zA-Z0-9\-]{8,11})'
print("urls being included")
urlpatterns = [
    url(r'^$', views.index, name='index'),
]
