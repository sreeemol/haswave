import uuid
from django.utils.text import slugify

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from departments.models import Department, Designation
from organizations.models import Organization, Branch
from general.models import PermissionGroup


class DepartmentSerializer(serializers.ModelSerializer):
	"""serializer to create, update, retrive , delete department of 
	an organization or branch
	"""
	organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
	branch = serializers.SlugRelatedField(queryset=Branch.objects.all(), slug_field='slug', allow_null=True)

	class Meta:
		model = Department
		fields = ['slug', 'organization', 'branch', 'department_name', 'description']
		read_only_fields = ['slug']

	def validate(self, data):
		"""vaidate branch of given organization,
		checking department exist in given organizationn if branch is null
		"""
		organization = data.get("organization")
		branch = data.get("branch")
		department_name = data.get("department_name")

		if branch:
			branch_exists = Branch.objects.filter(
				pk=branch.pk, 
				organization=organization
			).exists()

			if not branch_exists:
				raise serializers.ValidationError({
					'branch' : 'invalid branch for organization %s' %organization.slug
				})

		if self.instance:
			department_exist = Department.objects.filter(
				organization=organization, 
				branch=branch,
				department_name=department_name
			).exclude(pk=self.instance.pk).exists()

		else:
			department_exist = Department.objects.filter(
				organization=organization, 
				branch=branch,
				department_name=department_name
			).exists()

		if department_exist:
			raise serializers.ValidationError('The fields department_name, organization, branch must make a unique set.')

		return data

	def create(self, validated_data):

		user = self.context['request'].user

		department = Department(**validated_data)
		department.created_by = user
		department.updated_by = user
		department.slug = slugify(uuid.uuid4())
		department.save()

		return department

	def update(self, instance, validated_data):

		user = self.context['request'].user
		
		instance = super().update(instance, validated_data)
		instance.updated_by = user
		instance.save()

		return instance


class DepartmentListSerializer(serializers.ModelSerializer):
	"""serializer to list department of an organization or branch
	"""
	organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
	branch = serializers.SlugRelatedField(queryset=Branch.objects.all(), slug_field='slug', allow_null=True)

	class Meta:
		model = Department
		fields = ['organization', 'branch']

	def validate(self, data):
		"""vaidate branch of given organization
		"""
		organization = data.get("organization")
		branch = data.get("branch")

		if branch:
			branch_exists = Branch.objects.filter(
				pk=branch.pk, 
				organization=organization
			).exists()

			if not branch_exists:
				raise serializers.ValidationError({
					'branch' : 'invalid branch for organization %s' %organization.slug
				})

		return data


class DesignationSerializer(serializers.ModelSerializer):
	"""create, update, retrive, delete designations of an organization
	"""
	organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
	permission_groups = serializers.SlugRelatedField(queryset=PermissionGroup.objects.all(), many=True, required=False, slug_field='slug')

	class Meta:
		model = Designation
		fields = ['slug', 'organization', 'designation_name', 'permission_groups']
		read_only_fields = ['slug']

	def to_representation(self, obj):
		data = super().to_representation(obj)

		permission_groups = obj.permission_groups.all().values('slug' , 'group_name')

		data['permission_groups'] = permission_groups

		return data

	def create(self, validated_data):

		user = self.context['request'].user

		permission_groups = validated_data.pop('permission_groups')

		designation = Designation(**validated_data)
		designation.created_by = user
		designation.updated_by = user
		designation.slug = slugify(uuid.uuid4())
		designation.save()

		designation.permission_groups.set(permission_groups)

		return designation

	def update(self, instance, validated_data):

		user = self.context['request'].user

		permission_groups = validated_data.pop('permission_groups')

		instance = super().update(instance, validated_data)
		instance.updated_by = user
		instance.save()

		instance.permission_groups.set(permission_groups)

		return instance


class DesignationListSerializer(serializers.ModelSerializer):
	"""serializer to list designation of an organization
	"""
	organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')

	class Meta:
		model = Designation
		fields = ['organization']
