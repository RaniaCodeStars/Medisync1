from django.urls import path
from .views import delete_account, login_view,signup_view , logout_view, dashboard_medecin, dashboard_patient, dashboard_admin, dashboard_pharmacien
from . import views
from django.contrib.auth.views import LogoutView
app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('delete/', delete_account, name='delete_account'),
   # path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('dashboard-medecin/', dashboard_medecin, name='dashboard_medecin'),
    path('dashboard-patient/', dashboard_patient, name='dashboard_patient'),
    path('dashboard-admin/', dashboard_admin, name='dashboard_admin'),
    path('dashboard-pharmacien/', dashboard_pharmacien, name='dashboard_pharmacien'),
]