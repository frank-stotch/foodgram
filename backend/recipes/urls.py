from django.urls import path

from . import views


app_name = 'recipes'

urlpatterns = [
    path('<int:pk>/', views.short_link_view, name='short_link'),
]
