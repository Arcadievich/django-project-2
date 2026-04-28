from django.http import JsonResponse
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import json
from typing import Any, Tuple, Dict

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


def order_info_validation(order_info: Any) -> Tuple[bool, Dict[str, Any]]:
    """Валидация информации о заказе."""
    if not isinstance(order_info, dict):
        return False, {
            'status_code': status.HTTP_400_BAD_REQUEST,
            'error': 'Invalid input format',
            'message': 'Order info must be a JSON object',
        }
    
    if 'products' not in order_info:
        return False, {
            'status_code': status.HTTP_400_BAD_REQUEST,
            'error': 'Invalid input format',
            'message': 'Required field is missing',
        }
    
    if order_info.get('products') is None:
        return False, {
            'status_code': status.HTTP_400_BAD_REQUEST,
            'error': 'Products field is empty',
            'message': 'Products field should not be empty',
        }
    
    products = order_info.get('products')
    if not isinstance(products, list):
        return False, {
            'status_code': status.HTTP_400_BAD_REQUEST,
            'error': 'Invalid products format',
            'message': 'Products must be a list',
        }
    
    if products == []:
        return False, {
            'status_code': status.HTTP_400_BAD_REQUEST,
            'error': 'Products field is empty',
            'message': 'Products field should not be empty',
        }
    
    string_fields = ['firstname', 'lastname', 'phonenumber', 'address']

    for field in string_fields:
        value = order_info.get(field)

        if not isinstance(value, str):
            return False, {
                'status_code': status.HTTP_422_UNPROCESSABLE_ENTITY,
                'error': f'Invalid {field}',
                'message': f'{field} must be a string',
            }

    return True, {
        'status_code': status.HTTP_200_OK,
        'message': 'Order validation successful',
    }

@csrf_exempt
@api_view(['POST'])
def register_order(request):
    new_order_info = request.data

    is_valid, validation_response = order_info_validation(new_order_info)

    if not is_valid:
        return Response(
            data={
                'error': validation_response.get('error'),
                'detail': validation_response.get('message'),
                'status_code': validation_response.get('status_code'),
            },
            status=validation_response.get('status_code', status.HTTP_400_BAD_REQUEST)
        )

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

    return Response(
        data={
            'message': 'Order created successful',
            'order_id': order.id,
            'total_price': total_price,
        },
        status=status.HTTP_201_CREATED
    )
