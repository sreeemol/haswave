from django.urls import path

from rest_framework.routers import DefaultRouter

from employees import views


app_name = 'employees'

urlpatterns = [
    path('employee-api-login/', views.EmployeeAPILogin.as_view()),
    path('create-employee-screenshot/', views.EmployeeScreenshotCreateAPIView.as_view()),
    path('employee-email-verification/<uidb64>/<token>/', views.EmployeeEmailVerificationView.as_view())
]

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee'),
router.register(r'search-employees', views.EmployeesSearchViewSet, basename='search_employees')


urlpatterns += router.urls
