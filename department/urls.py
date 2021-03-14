from django.urls import path

from rest_framework.routers import DefaultRouter

from departments import views


router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'designations', views.DesignationViewSet, basename='designation')
router.register(r'search-departments', views.DepartmentSearchViewSet, basename='search_department')

urlpatterns = router.urls
