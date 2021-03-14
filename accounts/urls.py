from rest_framework.routers import DefaultRouter
from django.urls import path
from clients import views
# from clients.views import *

app_name = 'clients'

urlpatterns=[
    # path('add-new-client/',ClientCreateView.as_view())
]

router = DefaultRouter()
router.register(r'clients', views.ClientViewSet, basename='clients'),
router.register(r'other-details', views.OtherDetailsViewset, basename='other-details'),
router.register(r'address', views.AddressViewset, basename='address'),
router.register(r'remarks', views.RemarksViewset, basename='remarks'),
router.register(r'contact-persons', views.ContactPersonsViewset, basename='contact-persons'),


router.register(r'client-comments',views.ClientCommentViewSet, basename='client-comments')


urlpatterns += router.urls