from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('progress/', views.get_progress, name='get_progress'),
    path('disconnect', views.disconnect_view, name='disconnect'),
]
