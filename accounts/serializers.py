from django.utils import timezone
import uuid


from django.utils.text import slugify
from collections import OrderedDict

from rest_framework import serializers
from .models import *
from departments.models import *
from general.validators import is_postcode_valid
from general.models import Base, Country, State, City
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from projects.serializers import ProjectSerializer ,ResourceSerializer, ContractAttachmentsSerializer, TermAttachmentSerializer
from employees.serializers import EmployeeSerializer


from phonenumber_field.serializerfields import PhoneNumberField


class ClientSerializer(serializers.ModelSerializer):
  
    organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
    branch = serializers.SlugRelatedField(queryset=Branch.objects.all(), slug_field='slug', allow_null=True)
    department = serializers.SlugRelatedField(queryset=Department.objects.all(), slug_field='slug', allow_null=True)
    mobile = PhoneNumberField(allow_blank=True, allow_null=True)
    work_phone = PhoneNumberField(allow_blank=True, allow_null=True)
    
    class Meta:
         model = Client
         fields = ['slug','organization', 'branch', 'department','salutation','first_name','last_name','company_name',
         'email','mobile','work_phone','website','client_type','client_display_name','photo']
         read_only_fields = ['slug']
    
    def create(self, validated_data):

        user = validated_data.pop('user')
        created_by = self.context['request'].user
        client=Client(**validated_data)
        client.created_by=created_by
        client.updated_by=created_by
        client.slug=slugify(uuid.uuid4())
        client.user=user
        client.save()

        return client
    
    def to_representation(self, obj):
        
        data = super().to_representation(obj)
        fulldata = OrderedDict()
        fulldata['client']=data
        if hasattr(obj,'otherdetails'):
            fulldata['otherdetails']=OtherDetailsSerializer(obj.otherdetails).data
        if hasattr(obj,'address'):
            fulldata['billing_address']=AddressSerializer(obj.address).data
            if hasattr(obj.address,'country'):
                fulldata['billing_address']['country']={
                'id': obj.address.country.id,
                'name_ascii' : obj.address.country.name_ascii
                }
            if hasattr(obj.address,'state'):
                fulldata['billing_address']['state']={
                'id': obj.address.state.id,
                'name_ascii' : obj.address.state.name_ascii
                }
            if hasattr(obj.address,'city'):
                fulldata['billing_address']['city']={
                'id': obj.address.city.id,
                'name_ascii': obj.address.city.name_ascii
                }
            
        if hasattr(obj,'shippingaddress'):
            fulldata['shipping_address']=ShippingAddressSerializer(obj.shippingaddress).data
        if hasattr(obj,'remark'):
            fulldata['remark']=RemarkSerializer(obj.remark).data
        if hasattr(obj,'contactperson_set'):
            fulldata['contact_persons']=ContactPersonSerializer(obj.contactperson_set.all(),many=True).data
            
        if hasattr(obj,'project_set'):
                       
            projects=[]
            
            for i in obj.project_set.all():
                resources=[]
                for res_obj in i.financialinfo.resource_set.all().filter(resource_billing_type='billable'):

                    resources_assigned=EmployeeSerializer(res_obj.resource_assigned).data
                    res=ResourceSerializer(res_obj).data
                    res['resource_assigned']=resources_assigned
                    
                    contracts=[]
                    for cont in res_obj.resource_assigned.get_contract.all():                        
                        contracts.append(ContractAttachmentsSerializer(cont).data)   
                    res['contracts']=contracts
                    terms=[]
                    for term in i.financialinfo.termattachment_set.filter(resource=res_obj.resource_assigned):
                        terms.append(TermAttachmentSerializer(term).data)
                    res['terms']=terms
                    resources.append(res)

                projects.append({'project_name':i.project_name,'slug':i.slug,'resources':resources})
            fulldata['projects'] = projects
    
        return fulldata
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        instance = super().update(instance, validated_data)
        instance.updated_by = user
        instance.save()
        return instance

class OtherDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherDetails
        fields = [
            'currency','payment_terms','enable_portal','portal_language','facebook','skype_name'
        ]
    
    def create(self,validated_data):
        client = validated_data.pop('client')
        otherdetails=OtherDetails(**validated_data)
        otherdetails.client=client
        otherdetails.save()
        
        if validated_data['enable_portal']:
            portal_password=self.context['request'].GET.get('portal_password')
            if not portal_password:
                print('yesss')
                portal_password=User.objects.make_random_password()

            client.user.set_password(portal_password)
            client.user.save()
                

            html_message = render_to_string('clients/client_register_email.html', {
                'client': client,
                'password': portal_password
                
            })

            subject = client.organization.organization_name + ' has Invited to you join the portal'

            send_mail(subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [client.email],
                html_message = html_message,
                fail_silently=False
            )

        else:
            print ('noooo')
        return otherdetails

    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        instance = super().update(instance, validated_data)
        instance.updated_by = user
        instance.save()

        if validated_data['enable_portal'] and instance.client.user.password:
            instance.client.user.is_active=True
            instance.client.user.save()
        
        elif validated_data['enable_portal'] and not instance.client.user.password:
            # portal_password=self.context['request'].GET.get('portal_password')
            # if not portal_password:
            #     print('yesss')
            portal_password=User.objects.make_random_password()

            instance.client.user.set_password(portal_password)
            instance.client.user.is_active=True
            instance.client.user.save()
                

            html_message = render_to_string('clients/client_register_email.html', {
                'client': instance.client,
                'password': portal_password
                
            })

            subject = instance.client.organization.organization_name + ' has Invited to you join the portal'

            send_mail(subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [instance.client.email],
                html_message = html_message,
                fail_silently=False
            )
            print('enable portal is True & no portal password')

        else :
            instance.client.user.is_active=False
            instance.client.user.save()

        return instance


class AddressSerializer(serializers.ModelSerializer):
    phone = PhoneNumberField(allow_blank=True, allow_null=True)
    class Meta:
        model = Address
        fields = [
            'attention','country','state','city','address1','address2','pin_code','fax','phone'
        ]
    def create(self,validated_data):
          client = validated_data.pop('client')
          address=Address(**validated_data)
          address.client=client
          address.save()
          return address
    
    def validate(self, data):
        """vaidating Country, state, city 
        """
        
        country = data.get("country")
        state = data.get("state")
        city = data.get("city")
        pin_code = data.get("pin_code")

        if state:
            state_exists = State.objects.filter(
                pk=state.pk, 
                country=country
            ).exists()
        
            if not state_exists:
                raise serializers.ValidationError({
                        'state' : 'invalid state for Country %s' %country.pk
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
        if pin_code and country:

            if not is_postcode_valid(pin_code, country.code2):

                raise serializers.ValidationError("Invalid pincode")
        return data

    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        instance = super().update(instance, validated_data)
        instance.updated_by = user
        instance.save()
        return instance
    
    def to_representation(self, obj):
        data = super().to_representation(obj)
        if hasattr(obj,'country'):
                data['country']={
                'id': obj.country.id,
                'name_ascii' : obj.country.name_ascii
                }
        if hasattr(obj,'state'):
                data['state']={
                'id': obj.state.id,
                'name_ascii' : obj.state.name_ascii
                }
        if hasattr(obj,'city'):
                data['city']={
                'id': obj.city.id,
                'name_ascii': obj.city.name_ascii
                }

                
        return data

class ShippingAddressSerializer(serializers.ModelSerializer):
    
    # shipping_attention = serializers.CharField(source='attention',required=False,allow_blank=True)
    # shipping_country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(),source='country',required=False,allow_null=True)
    # shipping_state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(),source='state',required=False,allow_null=True)
    # shipping_city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(),source='city',required=False,allow_null=True)
    # shipping_address1 = serializers.CharField(source='address1',required=False,allow_blank=True)
    # shipping_address2 = serializers.CharField(source='address2',required=False,allow_blank=True)
    # shipping_pin_code = serializers.CharField(source='pin_code',required=False,allow_blank=True)
    # shipping_fax = serializers.CharField(source='fax',required=False,allow_blank=True)
    shipping_phone = PhoneNumberField(allow_blank=True, allow_null=True,required=False)
    
    class Meta:
        model = ShippingAddress
        fields = [
            'shipping_attention','shipping_country','shipping_state','shipping_city','shipping_address1','shipping_address2',
            'shipping_pin_code','shipping_fax','shipping_phone'
        ]
    
        # fields = [
        #     'attention','country','state','city','address1','address2',
        #     'pin_code','fax','phone'
        # ]
    
    def create(self,validated_data):
          client = validated_data.pop('client')
          shipping_address=ShippingAddress(**validated_data)
          shipping_address.client=client
          shipping_address.save()
          return shipping_address

    def validate(self, data):
        """vaidating Country, state, city 
        """
        country = data.get("shipping_country")
        state = data.get("shipping_state")
        city = data.get("shipping_city")
        pin_code = data.get("shipping_pin_code")

        if state:
            state_exists = State.objects.filter(
                pk=state.pk, 
                country=country
            ).exists()
        
            if not state_exists:
                raise serializers.ValidationError({
                        'state' : 'invalid state for Country %s' %country.pk
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
        if pin_code and country:

            if not is_postcode_valid(pin_code, country.code2):

                raise serializers.ValidationError("Invalid pincode")
        return data

class RemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remark
        fields =  [
            'remarks'
        ]
    def create(self,validated_data):
          client = validated_data.pop('client')
          remark=Remark(**validated_data)
          remark.client=client
          remark.save()
          return remark
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        instance = super().update(instance, validated_data)
        instance.updated_by = user
        instance.save()
        return instance


class ContactPersonSerializer(serializers.ModelSerializer):
    # contactperson_mobile_number = PhoneNumberField(allow_blank=True, allow_null=True)
    # contactperson_work_phone_number = PhoneNumberField(allow_blank=True, allow_null=True)

    class Meta:
        model= ContactPerson
        fields =[
            'contactperson_salutation','contactperson_first_name','contactperson_last_name','contactperson_email',
            'contactperson_mobile_number','contactperson_skype_name'
        ]

    def create(self,validated_data):
        client = validated_data.pop('client')
        contact_person=ContactPerson(**validated_data)
        contact_person.client=client
        contact_person.save()
        return contact_person
    
    
class ClientCommentSerializer(serializers.ModelSerializer):
    client = serializers.SlugRelatedField(queryset=Client.objects.all(), slug_field='slug')

    class Meta:
        model= ClientComment
        fields =[
            'comment','client'
        ]
        

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['comment']=obj.comment
        if hasattr(obj.created_by,'client_user'):
            data['commented_by']=obj.created_by.client_user.first_name + ' ' + obj.created_by.client_user.last_name
        elif hasattr(obj.created_by,'employee_user') and not obj.created_by.is_superuser:
            data['commented_by']=obj.created_by.employee_user.first().first_name + ' ' + obj.created_by.employee_user.first().last_name
        else:
            data['commented_by']=obj.created_by.user_profile.first_name + ' ' + obj.created_by.user_profile.last_name

        data['date_time']=timezone.localtime(obj.created).strftime("%A %d. %B %Y %H:%M %p")

        return data

    def create(self,validated_data):
        client = validated_data.pop('client')
        client_comment=ClientComment(**validated_data)
        client_comment.client=client
        client_comment.created_by=self.context['request'].user
        client_comment.updated_by=self.context['request'].user
        client_comment.slug = slugify(uuid.uuid4())
        client_comment.save()
        return client_comment


class ClientCommentListSerializer(serializers.ModelSerializer):
    """
    serializer for listing comments for a corresponding client
    """
    client = serializers.SlugRelatedField(queryset=Client.objects.all(), slug_field='slug')
    class Meta:
        model= ClientComment
        fields =[
            'client'
        ]

class ClientListSerializer(serializers.ModelSerializer):
    """
    Serializer for client listing according to organization
    """
    organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='slug')
    branch = serializers.SlugRelatedField(queryset=Branch.objects.all(), slug_field='slug', allow_null=True)

    class Meta:
        model = Client
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