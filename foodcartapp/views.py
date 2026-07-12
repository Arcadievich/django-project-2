from django.http import JsonResponse
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ListField

import phonenumbers

import json
from typing import Any, Tuple, Dict

from .models import Product
from .models import Order
from .models import OrderItem


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = ListField(
        child=OrderItemSerializer(),
        allow_empty=False,
        write_only=True,
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products',
        ]


def test_error(request):
    """Trigger a test error for Rollbar."""
    a = None
    a.hello()  # This will raise AttributeError
    return HttpResponse("This will not be reached")


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    new_order_info = request.data

    serializer = OrderSerializer(data=new_order_info)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address'],
        created_at=timezone.now()
    )
    
    products_fields = serializer.validated_data['products']
    order_items = [
        OrderItem(
            product=product['product'],
            order=order,
            quantity=product['quantity'],
            price=product['product'].price * product['quantity']
        )
        for product in products_fields
    ]
    OrderItem.objects.bulk_create(order_items)

    return Response(OrderSerializer(order).data ,status=status.HTTP_201_CREATED)
