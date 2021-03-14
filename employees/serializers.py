import uuid

from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import serializers

from general.models import Country, State, City, PermissionGroup
from departments.models import Department, Designation
from organizations.models import Organization, Branch
from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Employee, EmployeeScreenshot
from general.validators import is_postcode_valid
from general.token_generator import account_activation_token

from departments.serializers import DesignationSerializer, DepartmentSerializer
from organizations.serializers import BranchSerializer



from phonenumber_field.serializerfields import PhoneNumberField


class EmployeeSerializer(serializers.ModelSerializer):
    """serializer to create, update, retrive , delete employee of 
    an organization or branch
    """
    organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
    branch = serializers.SlugRelatedField(queryset=Branch.objects.all(), slug_field='slug', allow_null=True)
    department = serializers.SlugRelatedField(queryset=Department.objects.all(), slug_field='slug', allow_null=True)
    designation = serializers.SlugRelatedField(queryset=Designation.objects.all(), slug_field='slug')
    phone = PhoneNumberField(allow_blank=True, allow_null=True)

    class Meta:
        model = Employee
        fields = ['slug', 'organization', 'branch', 'department', 'designation', 'photo', 
        'first_name', 'last_name', 'phone', 'nationality', 'state', 'city', 'house_name',
        'street_name', 'locality_name', 'pin_code']
        read_only_fields = ['slug']

    def to_representation(self, obj):

        data = super().to_representation(obj)

        if obj.nationality:
            data['nationality'] = {
                'id': obj.nationality.id,
                'name_ascii' : obj.nationality.name_ascii
            }

        if obj.state:
            data['state'] = {
                'id': obj.state.id,
                'name_ascii' : obj.state.name_ascii
            }

        if obj.city:
            data['city'] = {
                'id': obj.city.id,
                'name_ascii': obj.city.name_ascii
            }
        data['email'] = obj.user.email
        data['id'] = obj.id
        data['designation'] = DesignationSerializer(obj.designation).data

        if hasattr(obj.branch, 'branch_name'):
            data['branch'] = BranchSerializer(obj.branch).data
        else:
            data['branch'] = None

        if hasattr(obj.department, 'department_name'):
            data['department'] = DepartmentSerializer(obj.department).data
        else:
            data['department'] = None

        data['status'] = obj.employee_status
        data['invitation_accepted'] = obj.invitation_accepted
        data['is_owner'] = obj.user.is_superuser


        return data

    def validate(self, data):
        """vaidating nationality, state, city 
        """
        nationality = data.get("nationality")
        state = data.get("state")
        city = data.get("city")
        pin_code = data.get("pin_code")

        if state:
            state_exists = State.objects.filter(
                pk=state.pk, 
                country=nationality
            ).exists()
        
            if not state_exists:
                raise serializers.ValidationError({
                        'state' : 'invalid state for Nationality %s' %nationality.pk
                    })

        if city:
            city_exists = City.objects.filter(
                pk=city.pk, 
                region=state
            ).exists()

            if not city_exists:
                raise serializers.ValidationError({
                        'city' : 'invalid city for state %s' %state.pk
                    })
    
        # validating postal code related to country
        if pin_code and nationality:

            if not is_postcode_valid(pin_code, nationality.code2):

                raise serializers.ValidationError("Invalid pincode")

        # vaidating branch, department are from correct organization
        organization = data.get("organization")
        branch = data.get("branch", None)
        department = data.get("department")
        designation = data.get("designation")

        if organization and branch:
            branch_exists = Branch.objects.filter(
                pk=branch.pk, 
                organization=organization
            ).exists()
        
            if not branch_exists:
                raise serializers.ValidationError({
                        'branch' : 'Invalid Branch for Organiation %s' %organization.slug
                    })

        if organization and department:
            department_exists = Department.objects.filter(
                pk=department.pk, 
                organization=organization,
                branch=branch
            ).exists()
        
            if not department_exists:
                raise serializers.ValidationError({
                        'department' : 'Invalid Department for Organiation and Branch'
                    })

        if organization and designation:
            designation_exists = Designation.objects.filter(
                pk=designation.pk, 
                organization=organization
            ).exists()
        
            if not designation_exists:
                raise serializers.ValidationError({
                        'branch' : 'Invalid Designation for Organiation %s' %organization.slug
                    })


        return data

    def create(self, validated_data):

        created_by = self.context['request'].user

        user = validated_data.pop('user')

        employee = Employee(**validated_data)
        employee.user = user
        employee.created_by = created_by
        employee.updated_by = created_by
        employee.slug = slugify(uuid.uuid4())
        employee.save()

        permission_groups = employee.designation.permission_groups.all()
        employee.permission_groups.set(permission_groups)

        return employee

    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        instance = super().update(instance, validated_data)
        instance.updated_by = user
        instance.save()
        
        # Mapping userprofile 
        if instance.user.is_superuser:
            instance.user.user_profile.first_name=instance.first_name
            instance.user.user_profile.last_name=instance.last_name
            instance.user.user_profile.contact_number=instance.phone
            instance.user.user_profile.country_id=instance.nationality_id
            instance.user.user_profile.state_id=instance.state_id
            instance.user.user_profile.city_id=instance.city_id
            instance.user.user_profile.photo=instance.photo
            
            instance.user.user_profile.save()

            # mapping same owner employee in other organizations
            obj_list=Employee.objects.filter(user=user).exclude(id=instance.id)
            if obj_list :
                for obj in obj_list:
                    obj.first_name=instance.first_name
                    obj.last_name=instance.last_name
                    obj.phone=instance.phone
                    obj.photo=instance.photo
                    obj.nationality_id=instance.nationality_id
                    obj.state_id=instance.state_id
                    obj.city_id=instance.city_id
                    obj.house_name=instance.house_name
                    obj.street_name=instance.street_name
                    obj.locality_name=instance.locality_name
                    obj.pin_code=instance.pin_code
                    obj.invitation_accepted=instance.invitation_accepted
                    
                    obj.save()
                    

        return instance


class InviteEmployeeSerializer(serializers.Serializer):
    """serializer to send invitation email to an employee
    """
    invite_url = serializers.URLField()
    site_name = serializers.CharField()

    class Meta:
        fields = ['invite_url', 'site_name']

    def send_invitation_email(self, employee):
        """send a invitation email to employee email address
        """
        token = account_activation_token.make_token(employee.user)

        html_message = render_to_string('employees/employee_invitation_email.html', {
            'employee': employee,
            'invite_url': self.data['invite_url'],
            'uid': urlsafe_base64_encode(force_bytes(employee.user.pk)).decode("utf-8"),
            'token': token,
            'organization': employee.organization,
            'site_name': self.data['invite_url'],
            'expiration_days': settings.PASSWORD_RESET_TIMEOUT_DAYS
        })

        subject = 'Welcome ' + employee.first_name + ' ' + employee.last_name

        send_mail(subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [employee.user.email],
            html_message = html_message,
            fail_silently=False
        )

    def save(self, employee=None):
        self.send_invitation_email(employee)


class EmployeeListSerializer(serializers.ModelSerializer):
    """serializer to list employee of 
    an organization, branch
    """
    organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
    branch = serializers.SlugRelatedField(queryset=Branch.objects.all(), slug_field='slug', allow_null=True)

    class Meta:
        model = Employee
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


class EmployeePermissionSerializer(serializers.ModelSerializer):
    """serializer to update, retrive permission groups of an employee
    """
    permission_groups = serializers.SlugRelatedField(queryset=PermissionGroup.objects.all(), many=True, slug_field='slug', allow_null=True)
    
    class Meta:
        model = Employee
        fields = ['slug', 'permission_groups']
        read_only_fields = ['slug']

    def validate(self, data):
        """vaidate branch of given organization
        """
        if self.instance:
            organization = self.instance.organization
            permission_groups = data.get("permission_groups")

            for permission_group in permission_groups:

                if not (permission_group.organization == organization):
                    raise serializers.ValidationError({
                        'permission_groups' : 'invalid permission groups of organization'
                    })

        return data

    def to_representation(self, obj):
        data = super().to_representation(obj)
        permissions_list=[]
        data['permission_groups'] = obj.permission_groups.all().values(
            'slug', 
            'group_name'
        )

        for i in obj.permission_groups.all():
            for perm in i.permissions.all():
                permissions_list.append(perm.codename)

        data['all_permissions']=permissions_list
        data['designationName']=obj.designation.designation_name

        return data


class EmployeeLoginSerializer(serializers.Serializer):
    """Serializer to login an employee user thorugh API
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'},
        trim_whitespace=False)

    def validate(self, data):
        """Authenticating user email address and password
        """
        email = data['email']
        password = data['password']

        if email and password:
            user = authenticate(username=email, password=password)

            if user:
                if hasattr(user, 'employee_user'):
                    data['user'] = user
                    return data

            raise serializers.ValidationError("Unable to log in with provided credentials.",
                code='authorization')

        return data


class EmployeeScreenshotSerializer(serializers.ModelSerializer):
    """Serializer to upload employee screenshort
    """
    slug = serializers.CharField(source='employee.slug')
    class Meta:
        model = EmployeeScreenshot
        fields = ('id', 'slug', 'datetime', 'screenshot')

    def create(self, validated_data):
        """Overriding default create method to create employee screenshort
        using employee instance of slug value provided through API
        """
        employee = Employee.objects.get(slug=validated_data['employee']['slug'])

        employee_screenshot_obj = EmployeeScreenshot(
            employee = employee,
            datetime = validated_data['datetime'],
            screenshot = validated_data['screenshot']
            )

        employee_screenshot_obj.save()

        return employee_screenshot_obj