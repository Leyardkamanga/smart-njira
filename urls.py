from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from routing.views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),                            # Django admin panel
    path('api/', include('routing.urls')),                      # Your app routes (e.g. RouteViewSet)
    path('api/auth/register/', RegisterView.as_view()),         # Register new user
    path('api/auth/token/login/', obtain_auth_token),           # Login (returns token)
]
