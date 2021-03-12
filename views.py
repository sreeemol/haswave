from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.views.generic import FormView, View

from django.core.exceptions import ObjectDoesNotExist

from Recipe.models import recipe, CartAddedRecipe, RecipeIngredient
from django.http import HttpResponse
from django.views.generic import TemplateView, DetailView
from django.utils.translation import gettext_lazy as _

from catalogue.views import record_aws_event
from oscar.core.loading import get_class, get_model
from django.http import HttpResponse
from oscar.apps.catalogue.models import Product
from rest_framework.response import Response as APIResponse
from django.conf import settings
# from basket.models import Basket
from oscar.apps.basket.models import Basket, Line
get_product_search_handler_class = get_class('catalogue.search_handlers', 'get_product_search_handler_class')


class RecipeView(TemplateView):
    context_object_name = "name_recipe"
    template_name = 'oscar/recipe/browseRecipe.html'

    def get_context_data(self, **kwargs):
        search_context = {}
        search_context['summary'] = _("All recipes")
        search_context['name_recipe'] = recipe.objects.all()
        search_context['image'] = recipe.objects.all()
        return search_context


class RecipeAddedCart(APIView):
    """
    Api to get all the training codes from the training master
    """
    def post(self, request, format=None):
        product_id = request.data.get("recipe_id")
        quantity = request.data.get("quantity")
        mode = request.data.get("mode")
        product = Product.objects.get(id=product_id)
        response = {}
        try:
            obj = CartAddedRecipe.objects.get(recipe_product=product, owner=self.request.user)
        except CartAddedRecipe.DoesNotExist:
            obj = None

        if obj is None:
            obj = CartAddedRecipe.objects.create(recipe_product=product, owner=self.request.user, quantity=0)
            obj.save()

        if mode == "add":
            # event_type = "added_to_cart"
            # record_aws_event(request.user, product, event_type)
            quantity_obj = int(obj.quantity) + int(quantity)
            obj.quantity = quantity_obj
            obj.save()
            try:
                basket = Basket.objects.filter(owner = self.request.user).last()
                for item in Line.objects.filter(basket = basket):
                    for ingredient in RecipeIngredient.objects.filter(products=product):
                        if item.product.id == ingredient.ingredient.id:
                            item.fake_quantity += ingredient.quantity * int(quantity)
                            item.save()
            except basket.DoesNotExist:
                pass
        if mode == "reduce":
            quantity_obj = obj.quantity - int(quantity)
            obj.quantity = quantity_obj
            obj.save()

            try:
                basket = Basket.objects.filter(owner = self.request.user).last()
                for item in Line.objects.filter(basket = basket):
                    for ingredient in RecipeIngredient.objects.filter(products=product):
                        if item.product.id == ingredient.ingredient.id:
                            item.fake_quantity -= ingredient.quantity * int(quantity)
                            item.save()
            except basket.DoesNotExist:
                pass

            if quantity_obj <= 0:
                try:
                    obj_for_remove = CartAddedRecipe.objects.get(recipe_product=product, owner=self.request.user, quantity=0).delete()
                    basket = None
                except CartAddedRecipe.DoesNotExist:
                    pass
                #     obj_for_remove = None
                #
                # if obj_for_remove is not None:
                #     del obj_for_remove


        if basket is None:
            response = {"result": "Quantity updated","status":200}
        else:
            response = {"result": "Added to cart recipe","status":200}

        return APIResponse(response)


class RecipeRemoveCart(APIView):

    def post(self, request, format=None):
        response = {}
        product_id = request.data.get("recipe_id")
        product = Product.objects.get(id=product_id)
        try:
            obj = CartAddedRecipe.objects.filter(recipe_product=product, owner=self.request.user)
            obj.delete()
            response = {"result": "Recipe removed from recipe cart", "status": 200}
        except obj.DoesNotExist:
            response = {"result": "Object does not exist" , "status": 500}

        return APIResponse(response)


class GetRecipeDetails(APIView):

    def post(self, request, format=None):
        response = {}

        product_id = request.data.get("recipe_id")
        product = Product.objects.get(id=product_id)
        ctx= {}
        outer_list = []
        try:
            ingredients = RecipeIngredient.objects.filter(products=product)
            for product in ingredients:

                inner_list = {}
                inner_list['id'] = product.ingredient.id
                inner_list['quantity'] = product.quantity
                outer_list.append(inner_list)
            ctx['ingredients'] = outer_list
            ctx['recipe_id'] = product_id

            response = {"result": ctx, "status": 200}

        except ingredients.DoesNotExist:
            response = {"result": "Object does not exist" , "status": 500}

        return APIResponse(response)


class BasketTotal(APIView):

    def get(self, request):
        response = {}
        total_incl_tax = 0
        total_excl_tax = 0
        curency = ''
        try:
            basket = Basket.objects.filter(owner = self.request.user).last()
            for item in Line.objects.filter(basket = basket):
                total_excl_tax += item.price_excl_tax * item.quantity
                # total_incl_tax += item.total_incl_tax * item.quantity
                # curency = item.currency
            response['total_excl_tax'] = total_excl_tax
            response['item_count'] = basket.num_lines
            # response['total_incl_tax'] = total_incl_tax
            # response['currency'] = curency
        except Basket.DoesNotExist:
            response = {"total": 0 , "currency": "None"}

        return APIResponse(response)
