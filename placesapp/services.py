from django.conf import settings

import requests
from geopy import distance

from .models import PlaceCoordinates
    

def fetch_coordinates(api_key, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": api_key,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon
    

def get_addresses_with_coords(orders, restaurants):
    restaurants_addresses = [restaurant.address for restaurant in restaurants]
    orders_addresses = [order.address for order in orders]

    all_addresses = restaurants_addresses + orders_addresses

    db_places = PlaceCoordinates.objects.filter(address__in=all_addresses)

    db_addresses = [place.address for place in db_places]

    missing_addresses = [
        address for address in all_addresses if address not in db_addresses
    ]

    addresses_with_coords = {}

    for place in db_places:
        addresses_with_coords[place.address] = (
            float(place.lat),
            float(place.lon),
        )

    if missing_addresses:
        api_key = settings.YANDEX_GEOCODER_API_KEY

        for address in missing_addresses:
            coords = fetch_coordinates(api_key, address)

            if coords is None:
                addresses_with_coords[address] = None
            else:
                PlaceCoordinates.objects.create(
                    address=address,
                    lat=coords[0],
                    lon=coords[1],
                )
                addresses_with_coords[address] = coords

    return addresses_with_coords
    

def calc_delivery_distance(restaurant_coords, delivery_coords):
    if not restaurant_coords or not delivery_coords:
        return None
    
    delivery_distance = distance.distance(
        restaurant_coords,
        delivery_coords,
    ).km
    
    return round(delivery_distance, 3)
