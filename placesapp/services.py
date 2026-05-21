from django.conf import settings

import requests
from geopy import distance

from .models import PlaceCoordinates


def get_coordinates_batch(addresses, api_key=None):
    if not addresses:
        return {}
    
    if api_key is None:
        api_key = settings.YANDEX_GEOCODER_API_KEY
    
    unique_addresses = {
        addr.strip() for addr in addresses 
        if addr and isinstance(addr, str) and addr.strip()
    }
    
    if not unique_addresses:
        return {}
    
    existing_places = PlaceCoordinates.objects.filter(
        address__in=unique_addresses
    )
    
    result = {}
    missing_addresses = set(unique_addresses)
    
    for place in existing_places:
        result[place.address] = (float(place.lat), float(place.lon))
        missing_addresses.discard(place.address)
    
    if missing_addresses:
        for address in missing_addresses:
            coords = _fetch_coordinates_from_api(address, api_key)
            if coords:
                result[address] = coords
                
                try:
                    PlaceCoordinates.objects.create(
                        address=address,
                        lat=coords[0],
                        lon=coords[1]
                    )
                    print(f"Сохранены координаты для: {address}")
                except Exception as e:
                    print(f"Ошибка сохранения {address}: {e}")
    
    return result


def _fetch_coordinates_from_api(address, api_key):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": api_key,
            "format": "json",
        }, timeout=5)
        
        response.raise_for_status()
        
        data = response.json()
        found_places = (
            data.get('response', {})
                .get('GeoObjectCollection', {})
                .get('featureMember', [])
        )
        
        if not found_places:
            print(f"Адрес не найден: {address}")
            return None
        
        most_relevant = found_places[0]
        point = most_relevant.get('GeoObject', {}).get('Point', {})
        pos = point.get('pos', '')
        
        if not pos:
            print(f"Нет координат для: {address}")
            return None
        
        lon, lat = pos.split(" ")
        return (float(lat), float(lon))
        
    except Exception as e:
        print(f"Ошибка API для {address}: {e}")
        return None
    

def calc_delivery_distance(restaurant_coords, delivery_coords):
    if not restaurant_coords or not delivery_coords:
        return None
    
    delivery_distance = distance.distance(
        restaurant_coords,
        delivery_coords,
    ).km
    
    return round(delivery_distance, 3)