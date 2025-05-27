from django.urls import path
from . import views
from . import admin as myapp_admin  # ✅ Import from your own admin.py
from .views import contact_view
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect
from .models import UserProfile
from django.contrib.auth.views import PasswordChangeDoneView
from myapp.verifier import ecg_authentication_view
class CustomPasswordChangeView(PasswordChangeView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # turn off the flag after successful change
        profile = self.request.user.userprofile
        profile.must_change_password = False
        profile.save()
        return response


urlpatterns = [
    path('', views.index, name='index'),
    path('welcome/', views.welcome, name='welcome'),
    path('contact/', views.contact_view, name='contact_page'),
    path('logout/', views.logout_view, name='logout'),
    path('demo/', ecg_authentication_view, name='demo'),
    path('admin/password_change/', CustomPasswordChangeView.as_view(), name='admin:password_change'),
    path('admin/password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    # ✅ Add your custom admin views here
    path('admin/user-logs/', myapp_admin.user_logs_view, name='admin_user_logs'),
    path('admin/user-logs/<str:log_date>/', myapp_admin.user_logs_by_date_view, name='admin_user_logs_by_date_view'),
    path('logs/<str:day>/', views.logs_by_day, name='logs_by_day'),
]



