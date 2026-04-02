from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

admin.site.site_header = "Jaychandra Ice Cream Admin"
admin.site.site_title = "Jaychandra Ice Cream Admin Portal"
admin.site.index_title = "Welcome to Jaychandra Ice Cream Researcher Portal"

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
handler403 = 'django.views.defaults.permission_denied'

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
