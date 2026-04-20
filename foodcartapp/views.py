from django.http import JsonResponse
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.decorators import api_view
from rest_framework.response import Response

import json

from .models import Product
from .models import Order
from .models import OrderItem


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


@csrf_exempt
@api_view(['POST'])
def register_order(request):
    new_order_info = request.data

    for key, value in new_order_info.items(): # Отладочный принт
        print(f'{key}: {value}')

    ordered_products = new_order_info['products']

    total_price = 0

    for item in ordered_products:
        db_product = Product.objects.get(id=item['product'])
        total_price += db_product.price * item['quantity']

    order = Order.objects.create(
        first_name=new_order_info['firstname'],
        last_name=new_order_info['lastname'],
        phone_number=new_order_info['phonenumber'],
        address=new_order_info['address'],
        price=total_price,
        created_at=timezone.now(),
        )
    
    for item in ordered_products:
        db_product = Product.objects.get(id=item['product'])
        OrderItem.objects.create(
            product=db_product,
            order=order,
            quantity=item['quantity']
        )

    return Response()
