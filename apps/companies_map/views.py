import json
import os
import requests
from django.shortcuts import render
from ..employees.views import smart_auth
import logging

logger = logging.getLogger(__name__)


@smart_auth
def index(request):
    yandex_api_key = os.getenv('YANDEX_API_KEY')
    if not yandex_api_key:
        return render(request, 'companies_map/index.html', {
            'error': 'API-ключ для Яндекс.Карт не найден. Добавьте YANDEX_API_KEY в .env файл.'
        })

    try:
        companies = request.bitrix_user_token.call_list_method('crm.company.list', {
            'select': ['ID', 'TITLE', 'ADDRESS']
        })
        logger.info(f"Получено {len(companies)} компаний из Bitrix24.")

        companies_data = []
        for company in companies:
            address = company.get('ADDRESS')
            if not address:
                continue

            try:
                response = requests.get(
                    'https://geocode-maps.yandex.ru/1.x/',
                    params={
                        'apikey': yandex_api_key,
                        'geocode': address,
                        'format': 'json',
                        'results': 1
                    }
                )
                response.raise_for_status()
                geo_data = response.json()

                feature_member = geo_data["response"]["GeoObjectCollection"]["featureMember"]
                if not feature_member:
                    logger.warning(f"Не удалось геокодировать адрес: {address}")
                    continue

                point = feature_member[0]["GeoObject"]["Point"]["pos"]
                lon, lat = point.split(' ')

                companies_data.append({
                    'id': company['ID'],
                    'title': company['TITLE'],
                    'address': address,
                    'lat': float(lat),
                    'lon': float(lon),
                })

            except Exception as e:
                logger.error(f"Ошибка геокодирования для адреса '{address}': {e}")

        logger.info(f"Успешно геокодировано {len(companies_data)} адресов.")

        context = {
            'yandex_api_key': yandex_api_key,
            'companies_json': json.dumps(companies_data)
        }
        return render(request, 'companies_map/index.html', context)

    except Exception as e:
        logger.error(f"Ошибка при получении данных для карты: {e}")
        return render(request, 'companies_map/index.html', {'error': str(e)})
