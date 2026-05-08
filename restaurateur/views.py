from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.conf import settings

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem

from placesapp.views import fetch_coordinates, calc_delivery_distance


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders_list = []

    orders = (Order.objects
              .exclude(status='completed_order')
              .order_by('status')
              .prefetch_related('items__product'))

    for order in orders:
        order_data = {
            'id': order.id,
            'status': order.get_status_display(),
            'payment_method': order.get_payment_method_display(),
            'price': order.price,
            'fullname': f"{order.firstname} {order.lastname}",
            'phonenumber': order.phonenumber,
            'address': order.address,
            'comment': order.comment,
            'restaurant': order.restaurant,
        }

        if not order.restaurant:
            suitable_restaurants = get_suitable_restaurants_for_order(order)
            restaurants_with_distance = get_restaurants_with_distance(
                suitable_restaurants, 
                order.address
            )
            order_data['suitable_restaurants'] = restaurants_with_distance
        else:
            order_data['suitable_restaurants'] = []

        orders_list.append(order_data)

    return render(
        request,
        template_name='order_items.html',
        context={'order_items': orders_list},
    )


def get_suitable_restaurants_for_order(order):
    """
    Возвращает список ресторанов, которые могут приготовить все блюда из заказа.
    """

    order_items = order.items.select_related('product').all()
    
    if not order_items:
        return []
    
    restaurants_per_product = []
    
    for order_item in order_items:
        product = order_item.product
        
        suitable_restaurants = set(
            RestaurantMenuItem.objects.filter(
                product=product,
                availability=True
            ).select_related('restaurant').values_list('restaurant', flat=True)
        )
        
        restaurants_per_product.append(suitable_restaurants)
    
    if restaurants_per_product:
        common_restaurants_ids = set(restaurants_per_product[0])
        for rest_set in restaurants_per_product[1:]:
            common_restaurants_ids &= rest_set
        
        suitable_restaurants = Restaurant.objects.filter(
            id__in=common_restaurants_ids
        )
        
        return suitable_restaurants
    
    return []


def get_restaurants_with_distance(restaurants, delivery_address):
    if not restaurants or not delivery_address:
        return []
    
    api_key = settings.YANDEX_GEOCODER_API_KEY
    
    delivery_coords = fetch_coordinates(api_key, delivery_address)
    
    if not delivery_coords:
        return [{'restaurant': r, 'distance': None} for r in restaurants]
    
    restaurants_with_distance = []
    for restaurant in restaurants:
        restaurant_coords = fetch_coordinates(api_key, restaurant.address)
        
        if restaurant_coords:
            distance_km = calc_delivery_distance(
                restaurant_coords,
                delivery_coords,
            )
            restaurants_with_distance.append({
                'restaurant': restaurant,
                'distance': distance_km
            })
        else:
            restaurants_with_distance.append({
                'restaurant': restaurant,
                'distance': None
            })
    
    restaurants_with_distance = sorted(
        restaurants_with_distance,
        key=lambda x: x['distance'] if x['distance'] is not None else float('inf')
    )
    
    return restaurants_with_distance