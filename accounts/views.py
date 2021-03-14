from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action


from .serializers import *
from .models import *

from accounts.serializers import UserSerializer


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    queryset = Client.objects.all()
    lookup_field = 'slug'

    def create(self,request):
        context = { 'request': request }

        user_serializer = UserSerializer(data=request.data)
        
        serializer = self.get_serializer(data=request.data, context=context)
        other_details_serializer=OtherDetailsSerializer(data=request.data,context=context)
        address_serializer=AddressSerializer(data=request.data)
        shipping_address_serializer=ShippingAddressSerializer(data=request.data)
        remark_serializer=RemarkSerializer(data=request.data)
        contact_person_serializer=ContactPersonSerializer(data=request.data['contact_person'],many=True)

        user_serializer_valid=user_serializer.is_valid()
        client_serializer_is_valid=serializer.is_valid()
        other_details_serializer_is_valid=other_details_serializer.is_valid()
        address_serializer_is_valid=address_serializer.is_valid()
        shipping_address_serializer_valid=shipping_address_serializer.is_valid()
        remark_serializer_valid=remark_serializer.is_valid()
        contact_person_serializer_valid=contact_person_serializer.is_valid()
        
        if user_serializer_valid and client_serializer_is_valid and other_details_serializer_is_valid and address_serializer_is_valid \
            and shipping_address_serializer_valid and remark_serializer_valid and contact_person_serializer_valid:
            
            user=user_serializer.save()
            client=serializer.save(user=user)
            other_details_serializer.save(client=client)
            address_serializer.save(client=client)
            shipping_address_serializer.save(client=client)
            remark_serializer.save(client=client)
            contact_person_serializer.save(client=client)
                        
            return Response(serializer.data)
                
        final_errors={}
        if user_serializer.errors:
            final_errors['client']=user_serializer.errors
        if serializer.errors:
            final_errors['client']=serializer.errors
        if other_details_serializer.errors:
            final_errors['other_details']=other_details_serializer.errors
        if address_serializer.errors:
            final_errors['billing_address']=address_serializer.errors
        if shipping_address_serializer.errors:
            final_errors['shipping_address']=shipping_address_serializer.errors
        
        if contact_person_serializer.errors:
            final_errors['contact_person']=contact_person_serializer.errors
         
        return Response(final_errors, status=status.HTTP_400_BAD_REQUEST)

    
    
    @action(methods=['post'], detail=False, url_path='organization-clients')
    def organization_clients(self, request):
        
        serializer=ClientListSerializer(data=request.data)
        
        if serializer.is_valid():
            organization = serializer.validated_data.get('organization')
            # branch_slug = serializer.data.get('branch')
            clients = Client.objects.filter(organization=organization)
            serializer = self.get_serializer(clients, many=True)
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    # @action(methods=['patch'], detail=False,url_path='update-other-details')
    # def update_other_details(self, request):
    #     serializer=OtherDetailsUpdateSerializer(data=request.data,partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     else:
    #         return Response(serializer.errors)

class OtherDetailsViewset(viewsets.ModelViewSet):
    serializer_class = OtherDetailsSerializer
    queryset = OtherDetails.objects.all()
    
    def update(self, request, *args, **kwargs):

        obj=Client.objects.get(slug=self.request.data['client']).otherdetails
        serializer = self.get_serializer(obj,data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class AddressViewset(viewsets.ModelViewSet):
    serializer_class=AddressSerializer
    queryset=Address.objects.all()

    def update(self, request, *args, **kwargs):

        obj=Client.objects.get(slug=self.request.data['client']).address
        serializer = self.get_serializer(obj,data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
class RemarksViewset(viewsets.ModelViewSet):
    serializer_class=RemarkSerializer
    queryset=Remark.objects.all()

    def update(self, request, *args, **kwargs):

        obj=Client.objects.get(slug=self.request.data['client']).remark
        serializer = self.get_serializer(obj,data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class ContactPersonsViewset(viewsets.ModelViewSet):
    serializer_class=ContactPersonSerializer
    queryset=ContactPerson.objects.all()

    def create(self, request, *args, **kwargs):
        client=Client.objects.get(slug=self.request.GET.get('client'))
        
        client.contactperson_set.all().delete()
        serializer = ContactPersonSerializer(data=request.data['contact_person'],many=True)

        if serializer.is_valid():
            serializer.save(client=client)
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class ClientCommentViewSet(viewsets.ModelViewSet):
    serializer_class = ClientCommentSerializer
    queryset = ClientComment.objects.order_by('-created')
    lookup_field = 'slug'

    def create(self,request):
        context = { 'request': request }
        client_comment_serializer=ClientCommentSerializer(data=request.data,context=context)

        if client_comment_serializer.is_valid():
            client_comment_serializer.save()
            return Response(client_comment_serializer.data)
        return Response(client_comment_serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False, url_path='listing-clients-comments')
    def clients_comments(self,request):

        serializer=ClientCommentListSerializer(data=request.data)
        if serializer.is_valid():
            client=serializer.validated_data.get('client')
            client_comments=ClientComment.objects.filter(client=client).order_by('-created')
            serializer = self.get_serializer(client_comments, many=True)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
