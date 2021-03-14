from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from general.permissions import CustomModelPermissions, IsObjectUser, ListOrCreatePermission
from .models import Department, Designation
from .serializers import DepartmentSerializer, DepartmentListSerializer, DesignationSerializer, \
	DesignationListSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
	"""create, update, delete, retirve departments of an organization or
	branch
	"""
	serializer_class = DepartmentSerializer
	queryset = Department.objects.all()
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated, CustomModelPermissions, IsObjectUser, ListOrCreatePermission]
	lookup_field = 'slug'

	def list(self, request):
		data = {'detail': 'Not found'}
		return Response(data, status=status.HTTP_404_NOT_FOUND)

	@action(methods=['post'], detail=False, url_path='all-departments')
	def all_departments(self, request):
		serializer = DepartmentListSerializer(data=request.data)
		if serializer.is_valid():

			organization_slug = serializer.data.get('organization')

			departments = Department.objects.filter(organization__slug=organization_slug)

			serializer = self.get_serializer(departments, many=True)

			return Response(serializer.data)
		else:
			return Response(serializer.errors)

	@action(methods=['post'], detail=False, url_path='organization-departments')
	def organization_departments(self, request):

		serializer = DepartmentListSerializer(data=request.data)

		if serializer.is_valid():

			organization_slug = serializer.data.get('organization')
			branch_slug = serializer.data.get('branch')

			if branch_slug:
				departments = Department.objects.filter(
					organization__slug=organization_slug,
					branch__slug=branch_slug
				)
			else:
				departments = Department.objects.filter(
					organization__slug=organization_slug,
					branch__isnull=True
				)

			serializer = self.get_serializer(departments, many=True)

			return Response(serializer.data)
		else:
			return Response(serializer.errors)


class DesignationViewSet(viewsets.ModelViewSet):
	"""create, update, delete, retirve designation of an organization
	"""
	serializer_class = DesignationSerializer
	queryset = Designation.objects.all()
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated, CustomModelPermissions, 
	IsObjectUser, ListOrCreatePermission]
	lookup_field = 'slug'

	def list(self, request):
		data = {'detail': 'Not found'}
		return Response(data, status=status.HTTP_404_NOT_FOUND)

	@action(methods=['post'], detail=False, url_path='organization-designations')
	def organization_designations(self, request):

		serializer = DesignationListSerializer(data=request.data)

		if serializer.is_valid():
			
			organization_slug = serializer.data.get('organization')

			designations = Designation.objects.filter(
				organization__slug=organization_slug
			).order_by('weight')

			sort_list = self.request.data.get('sort')

			if sort_list:
				for index, slug in enumerate(sort_list):
					Designation.objects.filter(slug=slug).update(weight=index)

			serializer = self.get_serializer(designations, many=True)

			return Response(serializer.data)
		else:
			return Response(serializer.errors)


class DepartmentSearchViewSet(viewsets.ModelViewSet):
	"""create, update, delete, retirve departments of an organization or
	branch
	"""
	serializer_class = DepartmentSerializer
	queryset = Department.objects.all()
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated, CustomModelPermissions, IsObjectUser, ListOrCreatePermission]
	lookup_field = 'slug'

	def list(self, request):
		data = {'detail': 'Not found'}
		return Response(data, status=status.HTTP_404_NOT_FOUND)

	@action(methods=['post'], detail=False, url_path='organization-departments')
	def organization_departments(self, request):

		serializer = DepartmentListSerializer(data=request.data)
		if serializer.is_valid():

			organization_slug = serializer.data.get('organization')

			search = self.request.GET.get('q', None)
			branch_only = self.request.GET.get('branch_only', None)
			branch_slug = serializer.data.get('branch', None)

			departments = Department.objects.filter(organization__slug=organization_slug)

			if branch_only == 'branches_only':
				departments = departments.filter(branch__isnull=False)

			if branch_slug:
				departments = departments.filter(
					branch__slug=branch_slug
				)

			if search:
				departments = departments.filter(department_name__icontains=search)

			serializer = self.get_serializer(departments, many=True)

			return Response(serializer.data)
		else:
			return Response(serializer.errors)


