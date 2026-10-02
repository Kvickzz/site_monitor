from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'monitor'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('websites/', views.website_list, name='website_list'),
    path('websites/add/', views.add_website, name='add_website'),
    path('websites/<uuid:website_id>/', views.website_detail, name='website_detail'),
    path('websites/<uuid:website_id>/edit/', views.edit_website, name='edit_website'),
    path('websites/<uuid:website_id>/delete/', views.delete_website, name='delete_website'),
    path('websites/<uuid:website_id>/toggle/', views.toggle_monitoring, name='toggle_monitoring'),
    path('websites/<uuid:website_id>/check-now/', views.run_check_now, name='run_check_now'),
    path('statistics/', views.statistics, name='statistics'),
    path('login/', LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='monitor:login'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.profile, name='profile'),
]
