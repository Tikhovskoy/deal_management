import logging
import os
import requests

logger = logging.getLogger(__name__)

class CompaniesMapService:
    def __init__(self, bitrix_user_token):
        self.but = bitrix_user_token

    def get_companies_data(self):
        yandex_api_key = os.getenv("YANDEX_API_KEY")
        if not yandex_api_key:
            raise ValueError("API-ключ для Яндекс.Карт не найден. Добавьте YANDEX_API_KEY в .env файл.")

        methods = [
            ("companies", "crm.company.list", {"select": ["ID", "TITLE"]}),
            ("addresses", "crm.address.list", {"filter": {"ENTITY_TYPE_ID": 4}}),
        ]
        batch_result = self.but.batch_api_call(methods=methods)

        batch_successes = batch_result.successes
        companies_result = batch_successes.get("companies", {}).get("result", [])
        addresses_result = batch_successes.get("addresses", {}).get("result", [])

        logger.info(
            f"Получено {len(companies_result)} компаний и {len(addresses_result)} адресов из Bitrix24."
        )

        companies_by_id = {str(c["ID"]): c for c in companies_result}

        companies_data = []
        for address_data in addresses_result:
            company_id = str(address_data.get("ENTITY_ID"))
            company = companies_by_id.get(company_id)

            if not company:
                continue

            full_address = self._format_address(address_data)
            if not full_address:
                continue

            try:
                response = requests.get(
                    "https://geocode-maps.yandex.ru/1.x/",
                    params={
                        "apikey": yandex_api_key,
                        "geocode": full_address,
                        "format": "json",
                        "results": 1,
                    },
                    timeout=5,
                )
                response.raise_for_status()
                geo_data = response.json()

                feature_member = geo_data["response"]["GeoObjectCollection"][
                    "featureMember"
                ]
                if not feature_member:
                    logger.warning(f"Не удалось геокодировать адрес: {full_address}")
                    continue

                point = feature_member[0]["GeoObject"]["Point"]["pos"]
                lon, lat = point.split(" ")

                companies_data.append(
                    {
                        "id": company["ID"],
                        "title": company["TITLE"],
                        "address": full_address,
                        "lat": float(lat),
                        "lon": float(lon),
                    }
                )

            except Exception as e:
                logger.error(f"Ошибка геокодирования для адреса '{full_address}': {e}")
        
        return companies_data, yandex_api_key

    def _format_address(self, address_data):
        parts = [
            address_data.get("COUNTRY"),
            address_data.get("PROVINCE"),
            address_data.get("CITY"),
            address_data.get("ADDRESS_1"),
            address_data.get("ADDRESS_2"),
        ]
        return ", ".join(filter(None, parts))
