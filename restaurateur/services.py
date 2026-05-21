from collections import defaultdict

from foodcartapp.models import RestaurantMenuItem
from placesapp.services import calc_delivery_distance


def get_restaurant_menu():
    menu_items = RestaurantMenuItem.objects.filter(
        availability=True
    ).select_related(
        'restaurant', 'product' 
    ).values_list('restaurant', 'product')

    restaurant_menu = defaultdict(set)
    for restaurant_id, product in menu_items:
        restaurant_menu[restaurant_id].add(product)

    return restaurant_menu


def get_restaurants_for_orders(orders, restaurants):
    if not orders:
        return {}
    
    restaurant_menu = get_restaurant_menu()

    all_restaurants = {
        restaurant.id: restaurant
        for restaurant in restaurants
    }

    orders_with_restaurants = {}

    for order in orders:
        order_product_ids = {
            item.product_id
            for item in order.items.all()
        }

        suitable_restaurants = []
        for restaurant_id, available_products in restaurant_menu.items():
            if order_product_ids.issubset(available_products):
                restaurant = all_restaurants.get(restaurant_id)
                if restaurant:
                    suitable_restaurants.append(restaurant)

        orders_with_restaurants[order.id] = suitable_restaurants

    return orders_with_restaurants


def get_restaurants_with_distance(restaurants, delivery_address, addresses_with_coords):
    restaurants_with_distance = []

    delivery_coords = addresses_with_coords[delivery_address]

    if delivery_coords is None:
        return [{
            'restaurant': r, 
            'distance': None, 
            'address_not_found': True,
        } for r in restaurants]

    for restaurant in restaurants:
        restaurant_coords = addresses_with_coords[restaurant.address]
        distance = calc_delivery_distance(restaurant_coords, delivery_coords)
        record = {
            'restaurant': restaurant,
            'distance': distance,
            'address_not_found': False,
        }
        restaurants_with_distance.append(record)

    
    restaurants_with_distance.sort(
        key=lambda x: x['distance'] if x['distance'] is not None else float('inf')
    )
    
    return restaurants_with_distance