from django.conf.urls import url
from dashboard import views
from django.views.generic import TemplateView

# old_archive_dir = r'(?P<old_archive_dir>\w+)'
# new_archive_dir = r'(?P<new_archive_dir>\w+)'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create/', views.create, name='record'),
    # url(r'compare/(?P<compare_obj_id>\d+)', views.compare, name='compare'),
    url(r'compare/(?P<compare_id>\d+)', TemplateView.as_view(template_name='compare.html'), name='compare'),
    url(r'view/123', views.single_link, name='single_link')
]
