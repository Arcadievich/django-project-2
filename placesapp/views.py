from django.shortcuts import render

import requests
from geopy import distance

from placesapp.models import PlaceCoordinates


def fetch_coordinates(api_key, address):
    if not address or not isinstance(address, str) or len(address.strip()) == 0:
        return None

    try:
        cached_place = PlaceCoordinates.objects.filter(address=address).first()
        if cached_place:
            return (float(cached_place.lat), float(cached_place.lon))
    except Exception as e:
        print(f"Ошибка при поиске в кэше координат: {e}")
    
    base_url = "https://geocode-maps.yandex.ru/1.x"
    
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": api_key,
            "format": "json",
        }, timeout=5)
        
        response.raise_for_status()
        
        data = response.json()
        found_places = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
        
        if not found_places:
            print(f"Адрес не найден геокодером: {address}")
            return None
        
        most_relevant = found_places[0]
        point = most_relevant.get('GeoObject', {}).get('Point', {})
        pos = point.get('pos', '')
        
        if not pos:
            print(f"Не удалось извлечь координаты для адреса: {address}")
            return None
        
        lon, lat = pos.split(" ")
        lat_float = float(lat)
        lon_float = float(lon)
        
        try:
            PlaceCoordinates.objects.create(
                address=address,
                lat=lat_float,
                lon=lon_float
            )
            print(f"Сохранены координаты для адреса: {address}")
        except Exception as e:
            print(f"Не удалось сохранить координаты в БД: {e}")
        
        return (lat_float, lon_float)
        
    except requests.exceptions.Timeout:
        print(f"Таймаут при запросе к геокодеру для адреса: {address}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Ошибка подключения к геокодеру для адреса: {address}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP ошибка геокодера для адреса {address}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к геокодеру для адреса {address}: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        print(f"Ошибка парсинга ответа геокодера для адреса {address}: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка при геокодировании адреса {address}: {e}")
        return None
    

def calc_delivery_distance(restaurant_coords, delivery_coords):
    if not restaurant_coords or not delivery_coords:
        return None
    
    delivery_distance = distance.distance(
        restaurant_coords,
        delivery_coords,
    ).km
    
    return round(delivery_distance, 3)
