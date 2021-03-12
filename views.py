from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.shortcuts import get_object_or_404
from django.db.models import Value as V
from django.db.models.functions import Concat
from django.db.models import Q

from general.token_generator import account_activation_token, password_reset_token


from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action



from general.permissions import CustomModelPermissions, IsObjectUser, ListOrCreatePermission
from .models import Employee, EmployeeScreenshot
from accounts.serializers import UserSerializer
from .serializers import EmployeeSerializer, EmployeeLoginSerializer, EmployeeScreenshotSerializer, \
InviteEmployeeSerializer, EmployeeListSerializer, EmployeePermissionSerializer

from accounts.models import User


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class EmployeeViewSet(viewsets.ModelViewSet):
    """create, update, delete, retirve employees of an organization
    """
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated, CustomModelPermissions, 
    # IsObjectUser, ListOrCreatePermission]
    
    permission_classes = [IsAuthenticated,  
    IsObjectUser, ListOrCreatePermission]
    
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination

    def create(self, request):
        """Create an employee and send invitation email to 
        emplyee email address
        """

        context = { 'request': request }

        user_serializer = UserSerializer(data=request.data)
        is_valid_user = user_serializer.is_valid()

        serializer = self.get_serializer(data=request.data, context=context)
        is_valid_serializer = serializer.is_valid()

        invite_serializer = InviteEmployeeSerializer(data=request.data)
        is_valid_invite = invite_serializer.is_valid()

        if is_valid_user and is_valid_serializer and is_valid_invite:
            
            try:
                with transaction.atomic():

                    # creating a user and update is_active filed to false
                    user = user_serializer.save()
                    user.is_active = False
                    user.save()

                    employee = serializer.save(user=user)
                    invite_serializer.save(employee=employee)
            except:
                errors = {
                    'error': 'Something went wrong, please try again later'
                }
                return Response(errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(serializer.data)

        else:
            data = {}
            data.update(user_serializer.errors)
            data.update(serializer.errors)
            data.update(invite_serializer.errors)

            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False, url_path='organization-employees')
    def organization_employees(self, request):
        serializer = EmployeeListSerializer(data=request.data)

        if serializer.is_valid():

            organization_slug = serializer.data.get('organization')

            branch_slug = serializer.data.get('branch')
            employees = Employee.objects.filter(
                    organization__slug=organization_slug,user__is_active=True, invitation_accepted=True
                )

            page = self.paginate_queryset(employees)
            if page is not None:
                serializer = self.get_serializer(page, many=True)

                data = {}

                page_nated_data = self.get_paginated_response(serializer.data).data
                data.update(page_nated_data)
                data['response'] = data.pop('results')

                return Response(data)

            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    @action(methods=['get'], detail=True, url_path='list-employee-permissions')
    def list_employee_permissions(self, request, slug=None):
        
        employee = self.get_object()

        serializer = EmployeePermissionSerializer(employee)

        return Response(serializer.data)
    
    

    @action(methods=['post'], detail=True, url_path='employee-permissions')
    def employee_permissions(self, request, slug=None):
        employee = self.get_object()

        serializer = EmployeePermissionSerializer(employee, data=request.data)

        if serializer.is_valid():
            serializer.save()
            
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, url_path='employee-status-change')
    def employee_status_change(self, request, slug=None):

        employee = self.get_object()
        if employee.employee_status == 'Active':
            employee.user.is_active = False
            employee.user.save()

        else:
            employee.user.is_active = True
            employee.user.save()

        return Response({'status': 'success'})


class EmployeeAPILogin(APIView):
    """Employee Login API view
    Returns user id, email, and authentication token
    """
    def post(self, request):

        serializer = EmployeeLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'token': token.key,
                'slug': user.employee_user.slug,
                'email': user.email
            })

        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class EmployeeScreenshotCreateAPIView(generics.CreateAPIView):
    """API view to create new screenshort instance in database
    input fields are employee slug, screenshort, datetime
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = EmployeeScreenshotSerializer


class EmployeeEmailVerificationView(APIView):
    """ Confirming registration via link provided in email"""

    def get(self, request, *args, **kwargs):
        """ Ckecking token and conforming account activation"""
        pk = force_text(urlsafe_base64_decode( kwargs.get('uidb64')))
        token = kwargs.get('token')
        
        user = get_object_or_404(User, pk=pk)
        
        if account_activation_token.check_token(user, token):

            request.session.flush()
            
            user.is_active = True
            employee_obj = user.employee_user.first()
            employee_obj.invitation_accepted = True
            employee_obj.save()
            user.save()

            token, created = Token.objects.get_or_create(user=user)

            data = {
                'status': 'success',
                'profile_slug': user.employee_user.first().slug,
                'email': user.email,
                'token': token.key,
                'message': 'email verificaton successfull'
            }

            return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                'status': 'error',
                'message': 'Invalid verification link'
            }

            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class EmployeesSearchViewSet(viewsets.ModelViewSet):
    """search and filtering employees of an organization ,branch,department
    """
    serializer_class = EmployeeListSerializer
    queryset = Employee.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, CustomModelPermissions, IsObjectUser, ListOrCreatePermission]
    lookup_field = 'slug'
    pagination_class = StandardResultsSetPagination

    # def list(self, request):
    #     data = {'detail': 'Not found'}
    #     return Response(data, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['post'], detail=False, url_path='organization-employees')
    def organization_employees(self, request):

        serializer = EmployeeListSerializer(data=request.data)

        if serializer.is_valid():

            queryset = self.get_queryset()

            organization_slug = serializer.data.get('organization')

            queryset = queryset.filter(organization__slug=organization_slug)

            status = self.request.POST.get('status', None)

            if status == 'inactive':
                queryset = queryset.filter(user__is_active=False, invitation_accepted=True)

            elif status == 'invited':
                queryset = queryset.filter(invitation_accepted=False)
            else:
                queryset = queryset.filter(user__is_active=True, invitation_accepted=True)

            listing = self.request.POST.get('listing', None)

            if listing == 'branches':
                queryset = queryset.filter(branch__isnull=False)

            if listing == 'general':
                queryset = queryset.filter(organization__isnull=False, branch__isnull=True)

            branch_slug = self.request.POST.get('branch', None)

            if branch_slug:
                queryset = queryset.filter(branch__slug=branch_slug)

            q = self.request.POST.get('q', None)

            if q:
                queryset = queryset.annotate(
                    search=Concat('first_name', V(' '), 'last_name')
                ).filter(Q(search__icontains=q) | Q(user__email__icontains=q))

            department_slug = self.request.POST.get('department', None)
            if department_slug:
                queryset = queryset.filter(department__slug=department_slug)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = EmployeeSerializer(page, many=True)

                data = {}

                page_nated_data = self.get_paginated_response(serializer.data).data
                data.update(page_nated_data)
                data['response'] = data.pop('results')

                return Response(data)

            serializer = EmployeeSerializer(queryset, many=True)

            return Response(serializer.data)
        else:
            return Response(serializer.errors)
